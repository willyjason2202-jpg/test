import re
from typing import Dict, List, Optional, Tuple

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(page_title="Matice Assignment", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800&family=Noto+Sans+KR:wght@400;500;700&display=swap');

.stApp {
    background-color: #f7f8fc;
}

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

/* 메인 영역 폭/여백 */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 760px;
}

/* 기본 form 테두리 제거 */
div[data-testid="stForm"] {
    border: none;
    padding: 0;
    background: transparent;
}

/* 버튼 공통 */
div[data-testid="stFormSubmitButton"] button,
div.stButton > button {
    border-radius: 14px !important;
    height: 48px !important;
    font-weight: 700 !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}

/* 시험 카드 */
.test-card {
    padding: 16px 18px;
    border: 1px solid #eceef5;
    border-radius: 20px;
    margin-bottom: 12px;
    background: #ffffff;
    box-shadow: 0 6px 18px rgba(17, 24, 39, 0.05);
}

/* 문항 카드 */
.q-card {
    padding: 10px 14px;
    border: 1px solid #eceef5;
    border-radius: 18px;
    margin-bottom: 4px;
    background: #ffffff;
    box-shadow: 0 4px 12px rgba(17, 24, 39, 0.04);
}

.q-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 62px;
    height: 30px;
    padding: 0 14px;
    background-color: #8ea3ff;
    color: white;
    border-radius: 999px;
    font-weight: 400;
    font-size: 15px;
    line-height: 1;
    margin-bottom: 4px;
}

/* 보조 텍스트 */
.small-muted {
    color: #8b95a1;
    font-size: 13px;
    line-height: 1.5;
}

/* 알림 박스 둥글게 */
div[data-baseweb="notification"] {
    border-radius: 16px !important;
}

/* 라디오/선택 pill 영역 조금 여유 */
div[role="radiogroup"] {
    gap: 6px !important;
}

/* 상단 앱 헤더 */
.app-header {
    background: linear-gradient(135deg, #6c8cff 0%, #8ea3ff 100%);
    border-radius: 24px;
    padding: 20px 20px 18px 20px;
    margin-bottom: 18px;
    box-shadow: 0 10px 24px rgba(108, 140, 255, 0.22);
    color: white;
}

.app-badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 10px;
}

.app-title {
    font-family: 'Nunito', 'Noto Sans KR', sans-serif;
    font-size: 30px;
    font-weight: 800;
    line-height: 1.15;
    margin: 0;
}

.app-subtitle {
    margin-top: 6px;
    font-size: 14px;
    opacity: 0.95;
}


/* section 제목 */
.section-title {
    font-size: 20px;
    font-weight: 800;
    color: #2b2f38;
    margin: 6px 0 12px 0;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div class="app-badge">STUDENT APP</div>
    <div class="app-title">Matice Assignment</div>
    <div class="app-subtitle">시험 응시와 성취도를 한눈에 확인하세요</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 상수
# =========================================================
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1Ve254f-O9NDmo62Un9pZ1eS4_6IjKeiJQgPhKWLMX2M/edit?usp=sharing"

RESULT_HEADERS = [
    "학생ID",
    "학생이름",
    "학교",
    "시험명",
    "1차오답",
    "1차오답수",
    "2차오답",
    "2차오답수",
    "3차오답",
    "3차오답수",
    "최종상태",
]


# =========================================================
# 유틸 함수
# =========================================================
def normalize_text(value) -> str:
    return str(value).strip()


def normalize_student_id(value) -> str:
    return normalize_text(value).upper()


def normalize_question_number(value) -> str:
    text = normalize_text(value)
    nums = re.findall(r"\d+", text)
    return nums[0] if nums else ""


def parse_wrong_list(value) -> List[str]:
    text = normalize_text(value)
    if text in ("", "-"):
        return []
    return re.findall(r"\d+", text)


def safe_int(value) -> int:
    try:
        return int(normalize_text(value))
    except Exception:
        return 0

def get_question_type(correct_value: str) -> str:
    """
    - 3 / 2,4 / 1,3,5  -> 객관식
    - make a difference -> 서술형
    """
    value = normalize_text(correct_value)
    value_no_space = value.replace(" ", "")

    if re.fullmatch(r"\d+(,\d+)*", value_no_space):
        return "multiple_choice"
    return "subjective"


def normalize_objective_answer(answer: str) -> str:
    return normalize_text(answer).replace(" ", "")


def normalize_subjective_answer(answer: str) -> str:
    text = normalize_text(answer).lower()
    text = re.sub(r"\s+", " ", text)
    return text
    
def get_question_type(correct_value: str) -> str:
    value = normalize_text(correct_value)
    value_no_space = value.replace(" ", "")

    if re.fullmatch(r"\d+(,\d+)*", value_no_space):
        return "multiple_choice"
    return "subjective"


def normalize_objective_answer(answer: str) -> str:
    return normalize_text(answer).replace(" ", "")


def normalize_subjective_answer(answer: str) -> str:
    text = normalize_text(answer).lower()
    text = re.sub(r"\s+", " ", text)
    return text
    
def compare_answer(student_ans: str, correct_ans: str) -> bool:
    q_type = get_question_type(correct_ans)

    if q_type == "multiple_choice":
        if "," in normalize_objective_answer(correct_ans):
            correct_norm = ",".join(
                sorted([x.strip() for x in normalize_objective_answer(correct_ans).split(",") if x.strip()])
            )
            student_norm = ",".join(
                sorted([x.strip() for x in normalize_objective_answer(student_ans).split(",") if x.strip()])
            )
            return student_norm == correct_norm

        return normalize_objective_answer(student_ans) == normalize_objective_answer(correct_ans)

    return normalize_subjective_answer(student_ans) == normalize_subjective_answer(correct_ans)


def read_records_safe(ws) -> List[Dict]:
    values = ws.get_all_values()

    if not values:
        return []

    headers = values[0]
    rows = values[1:]

    records = []
    for row in rows:
        padded = row + [""] * (len(headers) - len(row))
        records.append(dict(zip(headers, padded)))

    return records


def ensure_result_headers(ws) -> None:
    values = ws.get_all_values()

    if not values:
        ws.update("A1:K1", [RESULT_HEADERS])
        return

    first_row = values[0]
    padded = first_row + [""] * (len(RESULT_HEADERS) - len(first_row))
    current_headers = padded[:len(RESULT_HEADERS)]

    if current_headers != RESULT_HEADERS:
        ws.update("A1:K1", [RESULT_HEADERS])


def build_question_map(test_row: Dict) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    question_map: Dict[str, Dict[str, str]] = {}
    ordered_nums: List[str] = []

    question_cols = [
        key for key in test_row.keys()
        if normalize_text(key).startswith("문항")
    ]

    def sort_key(col_name: str) -> int:
        q = normalize_question_number(col_name)
        return int(q) if q.isdigit() else 999999

    for q_col in sorted(question_cols, key=sort_key):
        q_num = normalize_question_number(q_col)
        answer = normalize_text(test_row.get(q_col, ""))

        if q_num and answer:
            question_map[q_num] = {
                "col": q_col,
                "answer": answer,
            }
            ordered_nums.append(q_num)

    return question_map, ordered_nums


def get_stage_info(result_row: Optional[Dict]) -> Dict:
    if not result_row:
        return {
            "current_stage": 1,
            "stage1_wrong": [],
            "stage2_wrong": [],
            "stage3_wrong": [],
            "stage1_count": 0,
            "stage2_count": 0,
            "stage3_count": 0,
            "status": "1차대기",
        }

    stage1_wrong = parse_wrong_list(result_row.get("1차오답", "-"))
    stage2_wrong = parse_wrong_list(result_row.get("2차오답", "-"))
    stage3_wrong = parse_wrong_list(result_row.get("3차오답", "-"))

    stage1_count = safe_int(result_row.get("1차오답수", 0))
    stage2_count = safe_int(result_row.get("2차오답수", 0))
    stage3_count = safe_int(result_row.get("3차오답수", 0))

    status = normalize_text(result_row.get("최종상태", ""))

    if status == "완료":
        current_stage = 4
    elif status == "3차가능":
        current_stage = 3
    elif status == "2차가능":
        current_stage = 2
    else:
        current_stage = 1
        status = "1차대기"

    return {
        "current_stage": current_stage,
        "stage1_wrong": stage1_wrong,
        "stage2_wrong": stage2_wrong,
        "stage3_wrong": stage3_wrong,
        "stage1_count": stage1_count,
        "stage2_count": stage2_count,
        "stage3_count": stage3_count,
        "status": status,
    }


def find_student(students: List[Dict], student_id: str) -> Optional[Dict]:
    for row in students:
        if normalize_student_id(row.get("학생ID", "")) == student_id:
            return row
    return None


def find_result_row(results: List[Dict], student_id: str, test_name: str) -> Tuple[Optional[int], Optional[Dict]]:
    for idx, row in enumerate(results, start=2):
        if (
            normalize_student_id(row.get("학생ID", "")) == student_id
            and normalize_text(row.get("시험명", "")) == test_name
        ):
            return idx, row
    return None, None


def get_available_tests_for_school(tests: List[Dict], school_name: str) -> List[Dict]:
    school_name = normalize_text(school_name)
    return [row for row in tests if normalize_text(row.get("학교", "")) == school_name]


def get_target_question_nums(current_stage: int, stage_info: Dict, all_question_nums: List[str]) -> List[str]:
    if current_stage == 1:
        base = all_question_nums
    elif current_stage == 2:
        base = stage_info["stage1_wrong"]
    else:
        base = stage_info["stage2_wrong"]

    cleaned = []
    seen = set()

    for item in base:
        q = normalize_question_number(item)
        if q and q not in seen:
            cleaned.append(q)
            seen.add(q)

    return cleaned


def write_stage_result(
    result_ws,
    existing_row_num: Optional[int],
    student: Dict,
    test_name: str,
    current_stage: int,
    wrong_nums: List[str],
) -> None:
    wrong_text = ",".join(wrong_nums) if wrong_nums else "-"
    wrong_count = len(wrong_nums)

    if current_stage == 1:
        next_status = "2차가능" if wrong_count > 0 else "완료"
    elif current_stage == 2:
        next_status = "3차가능" if wrong_count > 0 else "완료"
    else:
        next_status = "완료"

    if existing_row_num is None:
        row_data = [
            student["학생ID"],
            student["학생이름"],
            student["학교"],
            test_name,
            wrong_text if current_stage == 1 else "",
            wrong_count if current_stage == 1 else "",
            wrong_text if current_stage == 2 else "",
            wrong_count if current_stage == 2 else "",
            wrong_text if current_stage == 3 else "",
            wrong_count if current_stage == 3 else "",
            next_status,
        ]
        result_ws.append_row(row_data)
        return

    if current_stage == 1:
        result_ws.update(
            f"E{existing_row_num}:K{existing_row_num}",
            [[wrong_text, wrong_count, "", "", "", "", next_status]],
        )
    elif current_stage == 2:
        result_ws.update(
            f"G{existing_row_num}:K{existing_row_num}",
            [[wrong_text, wrong_count, "", "", next_status]],
        )
    else:
        result_ws.update(
            f"I{existing_row_num}:K{existing_row_num}",
            [[wrong_text, wrong_count, next_status]],
        )


# =========================================================
# 캐시된 구글시트 연결
# =========================================================
@st.cache_resource
def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope,
    )
    return gspread.authorize(creds)


@st.cache_resource
def get_spreadsheet():
    client = get_gspread_client()
    return client.open_by_url(SPREADSHEET_URL)


@st.cache_data(ttl=30)
def load_students():
    ws = get_spreadsheet().worksheet("학생정보")
    return ws.get_all_records()


@st.cache_data(ttl=30)
def load_tests():
    ws = get_spreadsheet().worksheet("시험정보")
    return ws.get_all_records()


@st.cache_data(ttl=10)
def load_results():
    ws = get_spreadsheet().worksheet("결과")
    ensure_result_headers(ws)
    return read_records_safe(ws)


# =========================================================
# 구글 시트 연결
# =========================================================
try:
    spreadsheet = get_spreadsheet()

    students_ws = spreadsheet.worksheet("학생정보")
    tests_ws = spreadsheet.worksheet("시험정보")
    result_ws = spreadsheet.worksheet("결과")

    students = load_students()
    tests = load_tests()
    results = load_results()

except Exception as e:
    st.error("구글시트 연결 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()


# =========================================================
# 학생 식별
# =========================================================
params = st.query_params
student_param = params.get("student", "")
if isinstance(student_param, list):
    student_param = student_param[0] if student_param else ""

student_id = normalize_student_id(student_param)

if not student_id:
    st.error("학생 전용 링크가 아닙니다.")
    st.stop()

student = find_student(students, student_id)
if not student:
    st.error("등록되지 않은 학생입니다.")
    st.stop()

st.markdown(f"""
<div class="test-card" style="margin-bottom:16px;">
    <div style="font-size:20px; font-weight:800; color:#2b2f38;">
        {student['학생이름']} 학생
    </div>
    <div class="small-muted">학교: {student['학교']}</div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# 학생 학교 기준 시험 목록
# =========================================================
available_tests = get_available_tests_for_school(tests, student["학교"])

if not available_tests:
    st.warning("응시 가능한 시험이 없습니다.")
    st.stop()


# =========================================================
# 선택 상태
# =========================================================
if "selected_test_name" not in st.session_state:
    st.session_state.selected_test_name = None


# =========================================================
# 시험 목록 화면
# =========================================================
st.markdown('<div class="section-title">응시 가능한 시험</div>', unsafe_allow_html=True)

for test in available_tests:
    test_name = normalize_text(test.get("시험명", ""))
    row_num, result_row = find_result_row(results, student_id, test_name)
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


# =========================================================
# 응시 화면
# =========================================================
selected_test_name = st.session_state.selected_test_name

if selected_test_name:
    selected_test = None
    for test in available_tests:
        if normalize_text(test.get("시험명", "")) == selected_test_name:
            selected_test = test
            break

    if not selected_test:
        st.error("시험 정보를 찾을 수 없습니다.")
        st.stop()

    row_num, result_row = find_result_row(results, student_id, selected_test_name)
    stage_info = get_stage_info(result_row)
    current_stage = stage_info["current_stage"]

    if current_stage > 3:
        st.stop()

    question_map, all_question_nums = build_question_map(selected_test)
    if not question_map:
        st.error("시험정보 시트에 문항 데이터가 없습니다.")
        st.stop()

    target_question_nums = get_target_question_nums(
        current_stage=current_stage,
        stage_info=stage_info,
        all_question_nums=all_question_nums,
    )
    target_question_nums = [q for q in target_question_nums if q in question_map]

    st.divider()
    st.subheader(f"{selected_test_name} - {current_stage}차 응시")

    if not target_question_nums:
        st.warning("이번 차수에 다시 풀 문항이 없습니다.")
        if st.button("목록으로 돌아가기"):
            st.session_state.selected_test_name = None
            st.rerun()
        st.stop()

    with st.form("answer_form", clear_on_submit=False):
        answers_dict: Dict[str, str] = {}

        for q_num in target_question_nums:
            correct_value = question_map[q_num]["answer"]

            st.markdown(f"""
            <div class="q-number">{q_num}번</div>
            """, unsafe_allow_html=True)

            q_type = get_question_type(correct_value)

            if q_type == "multiple_choice":
                if "," in normalize_objective_answer(correct_value):
                    selected = st.pills(
                        label=f"{q_num}번",
                        options=["1", "2", "3", "4", "5"],
                        selection_mode="multi",
                        default=[],
                        key=f"q_{current_stage}_{selected_test_name}_{q_num}",
                        label_visibility="collapsed",
                        width="stretch",
                    )
                    answers_dict[q_num] = ",".join(sorted(selected)) if selected else ""
                else:
                    selected = st.pills(
                        label=f"{q_num}번",
                        options=["1", "2", "3", "4", "5"],
                        selection_mode="single",
                        default=None,
                        key=f"q_{current_stage}_{selected_test_name}_{q_num}",
                        label_visibility="collapsed",
                        width="stretch",
                    )
                    answers_dict[q_num] = selected if selected else ""

            else:
                parts = split_subjective_answers(correct_value)

                if len(parts) == 1:
                    text_answer = st.text_input(
                        label=f"{q_num}번",
                        key=f"q_{current_stage}_{selected_test_name}_{q_num}",
                        placeholder="영어 소문자로 입력",
                        label_visibility="collapsed",
                    )
                    answers_dict[q_num] = text_answer
                else:
                    multi_answers = []

                    for idx, _ in enumerate(parts, start=1):
                        text_answer = st.text_input(
                            label=f"{q_num}-{idx}",
                            key=f"q_{current_stage}_{selected_test_name}_{q_num}_{idx}",
                            placeholder=f"{idx}번째 문장을 입력하세요",
                        )
                        multi_answers.append(text_answer)

                    answers_dict[q_num] = " || ".join(multi_answers)

        col_submit, col_back = st.columns(2)

        with col_submit:
            submitted = st.form_submit_button(
                f"{current_stage}차 제출하기",
                use_container_width=True,
            )

        with col_back:
            go_back = st.form_submit_button(
                "목록으로",
                use_container_width=True,
            )

    if go_back:
        st.session_state.selected_test_name = None
        st.rerun()

    if submitted:
        empty_questions = [q for q, ans in answers_dict.items() if not ans]
        if empty_questions:
            st.warning(f"선택하지 않은 문항이 있습니다: {', '.join(empty_questions)}번")
            st.stop()

        wrong_nums = []
        for q_num in target_question_nums:
            student_ans = answers_dict[q_num]
            correct_ans = question_map[q_num]["answer"]

            if not compare_answer(student_ans, correct_ans):
                wrong_nums.append(q_num)

        write_stage_result(
            result_ws=result_ws,
            existing_row_num=row_num,
            student=student,
            test_name=selected_test_name,
            current_stage=current_stage,
            wrong_nums=wrong_nums,
        )

        load_results.clear()

        st.success(f"{current_stage}차 제출 완료")

        if wrong_nums:
            st.error(f"틀린 문항: {', '.join(wrong_nums)}")
            st.info(f"틀린 문항 수: {len(wrong_nums)}")
        else:
            st.success("모든 문항 정답입니다.")

        if st.button("시험 목록으로 돌아가기"):
            st.session_state.selected_test_name = None
            st.rerun()
