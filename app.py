import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="학생 채점 시스템", layout="centered")
st.title("학생 채점 시스템")

# -------------------------------
# 기본 스타일
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
    if str(s["학생ID"]).strip().upper() == student_id:
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
    if str(t["학교"]).strip() == str(student["학교"]).strip():
        available_tests.append(t)

if not available_tests:
    st.warning("응시 가능한 시험이 없습니다.")
    st.stop()

# -------------------------------
# 결과 행 찾기 함수
# -------------------------------
def find_result_row(student_id, test_name):
    for idx, r in enumerate(results, start=2):  # 시트 기준 실제 row 번호 (헤더가 1행)
        if (
            str(r.get("학생ID", "")).strip().upper() == student_id
            and str(r.get("시험명", "")).strip() == test_name
        ):
            return idx, r
    return None, None

# -------------------------------
# 차수 / 오답문항 계산 함수
# -------------------------------
def parse_wrong_list(value):
    text = str(value).strip()
    if text == "" or text == "-":
        return []
    return [x.strip() for x in text.split(",") if x.strip()]

def get_stage_info(result_row):
    if not result_row:
        return {
            "current_stage": 1,
            "stage1_wrong": [],
            "stage2_wrong": [],
            "stage3_wrong": [],
            "status": "1차대기"
        }

    stage1_wrong = parse_wrong_list(result_row.get("1차오답", "-"))
    stage2_wrong = parse_wrong_list(result_row.get("2차오답", "-"))
    stage3_wrong = parse_wrong_list(result_row.get("3차오답", "-"))

    if str(result_row.get("3차오답", "")).strip() not in ["", None]:
        return {
            "current_stage": 4,
            "stage1_wrong": stage1_wrong,
            "stage2_wrong": stage2_wrong,
            "stage3_wrong": stage3_wrong,
            "status": "완료"
        }

    if str(result_row.get("2차오답", "")).strip() not in ["", None]:
        return {
            "current_stage": 3,
            "stage1_wrong": stage1_wrong,
            "stage2_wrong": stage2_wrong,
            "stage3_wrong": stage3_wrong,
            "status": "3차가능"
        }

    if str(result_row.get("1차오답", "")).strip() not in ["", None]:
        return {
            "current_stage": 2,
            "stage1_wrong": stage1_wrong,
            "stage2_wrong": stage2_wrong,
            "stage3_wrong": stage3_wrong,
            "status": "2차가능"
        }

    return {
        "current_stage": 1,
        "stage1_wrong": [],
        "stage2_wrong": [],
        "stage3_wrong": [],
        "status": "1차대기"
    }

# -------------------------------
# session_state 초기화
# -------------------------------
if "selected_test_name" not in st.session_state:
    st.session_state.selected_test_name = None

# -------------------------------
# 시험 목록 표시
# -------------------------------
st.subheader("응시 가능한 시험")

for test in available_tests:
    test_name = str(test["시험명"]).strip()
    row_num, result_row = find_result_row(student_id, test_name)
    info = get_stage_info(result_row)

    c1, c2 = st.columns([4, 1])

    with c1:
        st.markdown(f"""
        <div class="test-card">
            <div style="font-size:18px;font-weight:700;">{test_name}</div>
            <div class="small-muted">
                1차: {len(info['stage1_wrong'])}문항 틀림 /
                2차: {len(info['stage2_wrong'])}문항 틀림 /
                3차: {len(info['stage3_wrong'])}문항 틀림
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
        if str(t["시험명"]).strip() == selected_test_name:
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

    st.divider()
    st.subheader(f"{selected_test_name} - {current_stage}차 응시")

    # 전체 문항 추출
    question_cols = [k for k in selected_test_data.keys() if str(k).startswith("문항")]
    question_cols = sorted(question_cols, key=lambda x: int(str(x).replace("문항", "")))

    all_question_nums = []
    for q_col in question_cols:
        correct_value = str(selected_test_data[q_col]).strip()
        if correct_value != "":
            q_num = str(q_col).replace("문항", "")
            all_question_nums.append(q_num)

    # 현재 차수에 보여줄 문항 번호 결정
    if current_stage == 1:
        target_question_nums = all_question_nums
    elif current_stage == 2:
        target_question_nums = info["stage1_wrong"]
    else:
        target_question_nums = info["stage2_wrong"]

    if not target_question_nums:
        st.success("이번 차수에 다시 풀 문항이 없습니다.")
        st.stop()

    with st.form("answer_form", clear_on_submit=False):
        answers_dict = {}

        for q_num in target_question_nums:
            q_col = f"문항{q_num}"
            correct_value = str(selected_test_data[q_col]).strip()

            st.markdown(f"""
            <div class="q-card">
                <div style="font-size:18px;font-weight:700;margin-bottom:10px;">{q_num}번</div>
            """, unsafe_allow_html=True)

            if "," in correct_value:
                selected = st.pills(
                    label=f"{q_num}번",
                    options=["1", "2", "3", "4", "5"],
                    selection_mode="multi",
                    default=[],
                    key=f"q_{current_stage}_{q_num}",
                    label_visibility="collapsed",
                    width="stretch"
                )
                answers_dict[q_num] = ",".join(sorted(selected)) if selected else ""
            else:
                selected = st.pills(
                    label=f"{q_num}번",
                    options=["1", "2", "3", "4", "5"],
                    selection_mode="single",
                    default=None,
                    key=f"q_{current_stage}_{q_num}",
                    label_visibility="collapsed",
                    width="stretch"
                )
                answers_dict[q_num] = selected if selected else ""

            st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button(f"{current_stage}차 제출하기", use_container_width=True)

    if submitted:
        empty_questions = [q for q, a in answers_dict.items() if a == ""]
        if empty_questions:
            st.warning(f"선택하지 않은 문항이 있습니다: {', '.join(empty_questions)}번")
            st.stop()

        wrong_nums = []

        for q_num in target_question_nums:
            q_col = f"문항{q_num}"
            correct_ans = str(selected_test_data[q_col]).strip()
            student_ans = answers_dict[q_num].strip()

            if "," in correct_ans:
                correct_norm = ",".join(sorted([x.strip() for x in correct_ans.split(",") if x.strip()]))
                student_norm = ",".join(sorted([x.strip() for x in student_ans.split(",") if x.strip()]))
            else:
                correct_norm = correct_ans
                student_norm = student_ans

            if student_norm != correct_norm:
                wrong_nums.append(q_num)

        wrong_text = ",".join(wrong_nums) if wrong_nums else "-"
        wrong_count = len(wrong_nums)

        # 결과 저장 / 업데이트
        if row_num is None:
            # 첫 응시(1차)
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
                "2차가능" if wrong_count > 0 else "완료"
            ])
        else:
            if current_stage == 2:
                result_ws.update(f"G{row_num}", wrong_text)   # 2차오답
                result_ws.update(f"H{row_num}", wrong_count)  # 2차오답수
                result_ws.update(f"K{row_num}", "3차가능" if wrong_count > 0 else "완료")
            elif current_stage == 3:
                result_ws.update(f"I{row_num}", wrong_text)   # 3차오답
                result_ws.update(f"J{row_num}", wrong_count)  # 3차오답수
                result_ws.update(f"K{row_num}", "완료")
            else:
                # 혹시 1차 재기록 상황 대비
                result_ws.update(f"E{row_num}", wrong_text)   # 1차오답
                result_ws.update(f"F{row_num}", wrong_count)  # 1차오답수
                result_ws.update(f"K{row_num}", "2차가능" if wrong_count > 0 else "완료")

        st.success(f"{current_stage}차 제출 완료")

        if wrong_nums:
            st.error(f"틀린 문항: {', '.join(wrong_nums)}")
            st.info(f"틀린 문항 수: {wrong_count}")
        else:
            st.success("모든 문항 정답입니다.")

        st.session_state.selected_test_name = None
        st.rerun()
