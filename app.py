import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

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

students = students_ws.get_all_records()
tests = tests_ws.get_all_records()

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

# -------------------------------
# 시험이 있을 때만 입력창 표시
# -------------------------------
if available_tests:
    test_names = [t["시험명"] for t in available_tests]
    selected_test = st.selectbox("응시할 시험 선택", test_names)

    # 선택한 시험의 전체 데이터 찾기
    selected_test_data = None
    for t in available_tests:
        if t["시험명"] == selected_test:
            selected_test_data = t
            break

    # 문항 열만 추출
    question_cols = [k for k in selected_test_data.keys() if str(k).startswith("문항")]
    question_cols = sorted(question_cols, key=lambda x: int(str(x).replace("문항", "")))

    # -------------------------------
    # 답안 입력
    # -------------------------------
    st.subheader("답안 입력")

    answers_list = []

    for q_col in question_cols:
        q_num = str(q_col).replace("문항", "")
        correct_value = str(selected_test_data[q_col]).strip()

        # 복수 정답 문항: 예) 3,4
        if "," in correct_value:
            answer = st.multiselect(
                f"{q_num}번",
                ["1", "2", "3", "4", "5"],
                key=f"q_{q_num}"
            )
            answer_text = ",".join(sorted(answer))
            answers_list.append(answer_text)

        # 단일 정답 문항: 예) 3
        else:
            answer = st.radio(
                f"{q_num}번",
                ["1", "2", "3", "4", "5"],
                horizontal=True,
                key=f"q_{q_num}"
            )
            answers_list.append(answer)

    answers = "|".join(answers_list)

    # -------------------------------
    # 제출 버튼
    # -------------------------------
    if st.button("제출하기"):
        has_empty = False
        for a in answers_list:
            if a == "":
                has_empty = True
                break

        if has_empty:
            st.warning("선택하지 않은 문항이 있습니다.")
        else:
            result_ws = spreadsheet.worksheet("결과")
            result_ws.append_row([
                student["학생ID"],
                student["학생이름"],
                student["학교"],
                selected_test,
                answers
            ])
            st.success("제출 완료!")

else:
    st.warning("응시 가능한 시험이 없습니다.")
