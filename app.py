import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="학생 채점 시스템", layout="centered")
st.title("학생 채점 시스템")

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

# -------------------------------
# 학생 정보 표시
# -------------------------------
st.subheader(f"{student['학생이름']} 학생")
st.caption(f"학교: {student['학교']}")

# -------------------------------
# 학교에 맞는 시험 찾기
# -------------------------------
available_tests = []
for t in tests:
    if str(t["학교"]).strip() == str(student["학교"]).strip():
        available_tests.append(t)

if not available_tests:
    st.warning("응시 가능한 시험이 없습니다.")
    st.stop()

# -------------------------------
# 시험 선택
# -------------------------------
test_names = [t["시험명"] for t in available_tests]
selected_test = st.selectbox(
    "응시할 시험 선택",
    test_names,
    index=0
)

selected_test_data = None
for t in available_tests:
    if t["시험명"] == selected_test:
        selected_test_data = t
        break

if not selected_test_data:
    st.error("시험 정보를 찾을 수 없습니다.")
    st.stop()

# -------------------------------
# 이미 제출했는지 확인
# -------------------------------
already_submitted = False
for r in results:
    if (
        str(r.get("학생ID", "")).strip().upper() == student_id
        and str(r.get("시험명", "")).strip() == selected_test
    ):
        already_submitted = True
        break

if already_submitted:
    st.warning("이미 제출한 시험입니다.")
    st.stop()

# -------------------------------
# 문항 열 추출
# -------------------------------
question_cols = [k for k in selected_test_data.keys() if str(k).startswith("문항")]
question_cols = sorted(question_cols, key=lambda x: int(str(x).replace("문항", "")))

# 실제 정답이 있는 문항만 사용
valid_question_cols = []
for q_col in question_cols:
    value = str(selected_test_data[q_col]).strip()
    if value != "":
        valid_question_cols.append(q_col)

if not valid_question_cols:
    st.warning("시험 문항 정보가 없습니다.")
    st.stop()

# -------------------------------
# form 내부에서 답안 입력
# -------------------------------
st.subheader("답안 입력")

with st.form("answer_form", clear_on_submit=False):
    answers_list = []

    for q_col in valid_question_cols:
        q_num = str(q_col).replace("문항", "")
        correct_value = str(selected_test_data[q_col]).strip()

        st.markdown(f"**{q_num}번**")

        # 복수 정답 문항
        if "," in correct_value:
            selected = st.segmented_control(
                label=f"{q_num}번",
                options=["1", "2", "3", "4", "5"],
                selection_mode="multi",
                default=[],
                key=f"q_{q_num}",
                label_visibility="collapsed",
                width="stretch"
            )
            answer_text = ",".join(sorted(selected)) if selected else ""
            answers_list.append(answer_text)

        # 단일 정답 문항
        else:
            selected = st.segmented_control(
                label=f"{q_num}번",
                options=["1", "2", "3", "4", "5"],
                selection_mode="single",
                default=None,
                key=f"q_{q_num}",
                label_visibility="collapsed",
                width="stretch"
            )
            answers_list.append(selected if selected else "")

    submitted = st.form_submit_button("제출하기", use_container_width=True)

# -------------------------------
# 제출 후 처리
# -------------------------------
if submitted:
    # 미응답 체크
    empty_questions = []
    for idx, ans in enumerate(answers_list, start=1):
        if ans == "":
            empty_questions.append(str(idx))

    if empty_questions:
        st.warning(f"선택하지 않은 문항이 있습니다: {', '.join(empty_questions)}번")
        st.stop()

    # 정답 / 학생답 비교
    correct_answers = []
    for q_col in valid_question_cols:
        correct_answers.append(str(selected_test_data[q_col]).strip())

    total_questions = len(correct_answers)
    score = 0
    wrong_nums = []
    mark_list = []

    for i, (student_ans, correct_ans) in enumerate(zip(answers_list, correct_answers), start=1):
        # 복수 정답은 순서 통일 후 비교
        if "," in correct_ans:
            correct_norm = ",".join(sorted([x.strip() for x in correct_ans.split(",") if x.strip()]))
            student_norm = ",".join(sorted([x.strip() for x in student_ans.split(",") if x.strip()]))
        else:
            correct_norm = correct_ans.strip()
            student_norm = student_ans.strip()

        if student_norm == correct_norm:
            score += 1
            mark_list.append("O")
        else:
            wrong_nums.append(str(i))
            mark_list.append("X")

    answers_text = "|".join(answers_list)
    wrong_text = ",".join(wrong_nums) if wrong_nums else "-"
    mark_text = "|".join(mark_list)

    # 결과 시트 저장
    # 결과 시트 첫 행 헤더 예시:
    # 학생ID | 학생이름 | 학교 | 시험명 | 제출답안 | 점수 | 총문항 | 오답번호 | 정오표
    result_ws.append_row([
        student["학생ID"],
        student["학생이름"],
        student["학교"],
        selected_test,
        answers_text,
        score,
        total_questions,
        wrong_text,
        mark_text
    ])

    # 즉석 결과 표시
    st.success("제출 완료!")
    st.info(f"점수: {score} / {total_questions}")

    if wrong_nums:
        st.error(f"오답 번호: {', '.join(wrong_nums)}")
    else:
        st.success("전부 정답입니다.")

    with st.expander("문항별 결과 보기"):
        for i, (student_ans, correct_ans, ox) in enumerate(zip(answers_list, correct_answers, mark_list), start=1):
            st.write(f"{i}번 | 제출: {student_ans} | 정답: {correct_ans} | 결과: {ox}")
