import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="학생 채점 시스템", layout="centered")
st.title("학생 채점 시스템")

# -------------------------------
# 스타일
# -------------------------------
st.markdown("""
<style>
div[data-testid="stForm"] {
    border: none;
    padding: 0;
}
div[data-testid="stFormSubmitButton"] button {
    border-radius: 14px !important;
    height: 48px !important;
    font-weight: 700 !important;
}
.test-card {
    padding: 14px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    margin-bottom: 12px;
    background: #ffffff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.q-card {
    padding: 14px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    margin-bottom: 12px;
    background: #ffffff;
}
.small-muted {
    color: #6b7280;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 구글시트 연결
# -------------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)
client = gspread.authorize(creds)

spreadsheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1Ve254f-O9NDmo62Un9pZ1eS4_6IjKeiJQgPhKWLMX2M/edit?usp=sharing"
)

students_ws = spreadsheet.worksheet("학생정보")
tests_ws = spreadsheet.worksheet("시험정보")
result_ws = spreadsheet.worksheet("결과")

students = students_ws.get_all_records()
tests = tests_ws.get_all_records()
results = result_ws.get_all_records()

# -------------------------------
# 학생 ID 읽기
# -------------------------------
params = st.query_params
student_id = str(params.get("student", "")).strip().upper()

if not student_id:
    st.error("학생 전용 링크가 아닙니다.")
    st.stop()

# -------------------------------
# 학생 찾기
# -------------------------------
student = None
for s in students:
    if str(s.get("학생ID", "")).strip().upper() == student_id:
        student = s
        break

if not student:
    st.error("등록되지 않은 학생입니다.")
    st.stop()

st.subheader(f"{student['학생이름']} 학생")
st.caption(f"학교: {student['학교']}")

# -------------------------------
# 학교별 시험 목록
# -------------------------------
available_tests = []
for t in tests:
    if str(t.get("학교", "")).strip() == str(student.get("학교", "")).strip():
        available_tests.append(t)

if not available_tests:
    st.warning("응시 가능한 시험이 없습니다.")
    st.stop()

# -------------------------------
# 유틸 함수
# -------------------------------
def normalize_question_number(value):
    """
    '3', ' 3 ', '3번', '문항3' -> '3'
    """
    text = str(value).strip()
    text = text.replace("문항", "").replace("번", "").strip()
    return text

def parse_wrong_list(value):
    """
    '-', '', '3', '3,5', '3번, 5번' 등을 ['3'], ['3','5'] 형태로 변환
    """
    text = str(value).strip()

    if text == "" or text == "-":
        return []

    result = []
    for x in text.split(","):
        q = normalize_question_number(x)
        if q:
            result.append(q)
    return result

def find_result_row(student_id_value, test_name):
    """
    결과 시트에서 해당 학생/시험 행 찾기
    반환: (실제 시트 row 번호, row dict) 또는 (None, None)
    """
    for idx, r in enumerate(results, start=2):  # 헤더가 1행
        if (
            str(r.get("학생ID", "")).strip().upper() == student_id_value
            and str(r.get("시험명", "")).strip() == test_name
        ):
            return idx, r
    return None, None

def safe_int(value):
    try:
        return int(str(value).strip())
    except:
        return 0
        
def get_stage_info(result_row):
    if not result_row:
        return {
            "current_stage": 1,
            "stage1_wrong": [],
            "stage2_wrong": [],
            "stage3_wrong": [],
            "stage1_count": 0,
            "stage2_count": 0,
            "stage3_count": 0,
            "status": "1차대기"
        }

    stage1_wrong = parse_wrong_list(result_row.get("1차오답", "-"))
    stage2_wrong = parse_wrong_list(result_row.get("2차오답", "-"))
    stage3_wrong = parse_wrong_list(result_row.get("3차오답", "-"))

    stage1_count = safe_int(result_row.get("1차오답수", 0))
    stage2_count = safe_int(result_row.get("2차오답수", 0))
    stage3_count = safe_int(result_row.get("3차오답수", 0))

    status = str(result_row.get("최종상태", "")).strip()

    if status == "완료":
        current_stage = 4
    elif status == "3차가능":
        current_stage = 3
    elif status == "2차가능":
        current_stage = 2
    else:
        current_stage = 1

    return {
        "current_stage": current_stage,
        "stage1_wrong": stage1_wrong,
        "stage2_wrong": stage2_wrong,
        "stage3_wrong": stage3_wrong,
        "stage1_count": stage1_count,
        "stage2_count": stage2_count,
        "stage3_count": stage3_count,
        "status": status if status else "1차대기"
    }

def build_question_map(test_row):
    """
    시험정보 행에서 실제 사용 가능한 문항 목록 생성
    반환:
      question_map = {'1': {'col':'문항1', 'answer':'3'}, ...}
      ordered_nums = ['1','2',...]
    """
    question_map = {}
    ordered_nums = []

    keys = list(test_row.keys())
    question_cols = [k for k in keys if str(k).strip().startswith("문항")]

    def sort_key(x):
        n = normalize_question_number(x)
        return int(n) if n.isdigit() else 999999

    question_cols = sorted(question_cols, key=sort_key)

    for q_col in question_cols:
        q_num = normalize_question_number(q_col)
        ans = str(test_row.get(q_col, "")).strip()

        if q_num and ans != "":
            question_map[q_num] = {
                "col": q_col,
                "answer": ans
            }
            ordered_nums.append(q_num)

    return question_map, ordered_nums

def compare_answer(student_ans, correct_ans):
    """
    단일/복수 정답 비교
    """
    student_ans = str(student_ans).strip()
    correct_ans = str(correct_ans).strip()

    if "," in correct_ans:
        correct_norm = ",".join(
            sorted([x.strip() for x in correct_ans.split(",") if x.strip()])
        )
        student_norm = ",".join(
            sorted([x.strip() for x in student_ans.split(",") if x.strip()])
        )
        return student_norm == correct_norm

    return student_ans == correct_ans

# -------------------------------
# session_state
# -------------------------------
if "selected_test_name" not in st.session_state:
    st.session_state.selected_test_name = None

# -------------------------------
# 시험 목록 표시
# -------------------------------
st.subheader("응시 가능한 시험")

for test in available_tests:
    test_name = str(test.get("시험명", "")).strip()
    row_num, result_row = find_result_row(student_id, test_name)
    info = get_stage_info(result_row)

    c1, c2 = st.columns([5, 1])

    with c1:
        st.markdown(f"""
        <div class="test-card">
            <div style="font-size:18px;font-weight:700;">{test_name}</div>
            <div class="small-muted">
                1차: {info['stage1_count']}문항 틀림 /
                2차: {info['stage2_count']}문항 틀림 /
                3차: {info['stage3_count']}문항 틀림
            </div>
            <div class="small-muted">현재 상태: {info['status']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        if info["current_stage"] <= 3:
            if st.button("응시", key=f"open_{test_name}"):
                st.session_state.selected_test_name = test_name
                st.rerun()
        else:
            st.button("완료", key=f"done_{test_name}", disabled=True)

# -------------------------------
# 선택한 시험 응시 화면
# -------------------------------
selected_test_name = st.session_state.selected_test_name

if selected_test_name:
    selected_test_data = None
    for t in available_tests:
        if str(t.get("시험명", "")).strip() == selected_test_name:
            selected_test_data = t
            break

    if not selected_test_data:
        st.error("시험 정보를 찾을 수 없습니다.")
        st.stop()

    row_num, result_row = find_result_row(student_id, selected_test_name)
    info = get_stage_info(result_row)
    current_stage = info["current_stage"]

    if current_stage > 3:
        st.info("이 시험은 3차까지 모두 완료되었습니다.")
        st.stop()

    question_map, all_question_nums = build_question_map(selected_test_data)

    if not question_map:
        st.error("시험정보 시트에 문항 데이터가 없습니다.")
        st.stop()

    # 현재 차수에 보여줄 문항 결정
    if current_stage == 1:
        target_question_nums = all_question_nums
    elif current_stage == 2:
        target_question_nums = info["stage1_wrong"]
    else:
        target_question_nums = info["stage2_wrong"]

    # 실제 시험정보에 있는 문항만 남김
    cleaned_target_question_nums = []
    for q_num in target_question_nums:
        nq = normalize_question_number(q_num)
        if nq in question_map:
            cleaned_target_question_nums.append(nq)

    target_question_nums = cleaned_target_question_nums

    st.divider()
    st.subheader(f"{selected_test_name} - {current_stage}차 응시")

    if not target_question_nums:
        st.success("이번 차수에 다시 풀 문항이 없습니다.")
        if st.button("목록으로 돌아가기"):
            st.session_state.selected_test_name = None
            st.rerun()
        st.stop()

    with st.form("answer_form", clear_on_submit=False):
        answers_dict = {}

        for q_num in target_question_nums:
            correct_value = question_map[q_num]["answer"]

            st.markdown(f"""
            <div class="q-card">
                <div style="font-size:18px;font-weight:700;margin-bottom:10px;">{q_num}번</div>
            """, unsafe_allow_html=True)

            # 복수 정답 문항
            if "," in correct_value:
                selected = st.pills(
                    label=f"{q_num}번",
                    options=["1", "2", "3", "4", "5"],
                    selection_mode="multi",
                    default=[],
                    key=f"q_{current_stage}_{selected_test_name}_{q_num}",
                    label_visibility="collapsed",
                    width="stretch"
                )
                answers_dict[q_num] = ",".join(sorted(selected)) if selected else ""

            # 단일 정답 문항
            else:
                selected = st.pills(
                    label=f"{q_num}번",
                    options=["1", "2", "3", "4", "5"],
                    selection_mode="single",
                    default=None,
                    key=f"q_{current_stage}_{selected_test_name}_{q_num}",
                    label_visibility="collapsed",
                    width="stretch"
                )
                answers_dict[q_num] = selected if selected else ""

            st.markdown("</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button(f"{current_stage}차 제출하기", use_container_width=True)
        with c2:
            back = st.form_submit_button("목록으로", use_container_width=True)

    if back:
        st.session_state.selected_test_name = None
        st.rerun()

    if submitted:
        empty_questions = [q for q, a in answers_dict.items() if a == ""]
        if empty_questions:
            st.warning(f"선택하지 않은 문항이 있습니다: {', '.join(empty_questions)}번")
            st.stop()

        wrong_nums = []

        for q_num in target_question_nums:
            student_ans = answers_dict[q_num]
            correct_ans = question_map[q_num]["answer"]

            if not compare_answer(student_ans, correct_ans):
                wrong_nums.append(q_num)

        wrong_text = ",".join(wrong_nums) if wrong_nums else "-"
        wrong_count = len(wrong_nums)

        # -------------------------------
        # 결과 저장
        # 결과 시트 열 순서:
        # A 학생ID
        # B 학생이름
        # C 학교
        # D 시험명
        # E 1차오답
        # F 1차오답수
        # G 2차오답
        # H 2차오답수
        # I 3차오답
        # J 3차오답수
        # K 최종상태
        # -------------------------------
        if row_num is None:
            # 첫 제출 = 1차
            final_status = "2차가능" if wrong_count > 0 else "완료"
            result_ws.append_row([
                student["학생ID"],
                student["학생이름"],
                student["학교"],
                selected_test_name,
                wrong_text,
                wrong_count,
                "",
                "",
                "",
                "",
                final_status
            ])
        else:
            if current_stage == 1:
                final_status = "2차가능" if wrong_count > 0 else "완료"
                result_ws.update(f"E{row_num}:K{row_num}", [[
                    wrong_text,
                    wrong_count,
                    result_row.get("2차오답", ""),
                    result_row.get("2차오답수", ""),
                    result_row.get("3차오답", ""),
                    result_row.get("3차오답수", ""),
                    final_status
                ]])

            elif current_stage == 2:
                final_status = "3차가능" if wrong_count > 0 else "완료"
                result_ws.update(f"G{row_num}:K{row_num}", [[
                    wrong_text,
                    wrong_count,
                    result_row.get("3차오답", ""),
                    result_row.get("3차오답수", ""),
                    final_status
                ]])

            elif current_stage == 3:
                final_status = "완료"
                result_ws.update(f"I{row_num}:K{row_num}", [[
                    wrong_text,
                    wrong_count,
                    final_status
                ]])

        # 즉시 결과 표시
        st.success(f"{current_stage}차 제출 완료")

        if wrong_nums:
            st.error(f"틀린 문항: {', '.join(wrong_nums)}")
            st.info(f"틀린 문항 수: {wrong_count}")
        else:
            st.success("모든 문항 정답입니다.")

        if st.button("시험 목록으로 돌아가기"):
            st.session_state.selected_test_name = None
            st.rerun()
