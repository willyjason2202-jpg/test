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

# selected_test 기본값
selected_test = None

# -------------------------------
# 시험 선택
# -------------------------------
if available_tests:
    test_names = [t["시험명"] for t in available_tests]
    selected_test = st.selectbox("응시할 시험 선택", test_names)
else:
    st.warning("응시 가능한 시험이 없습니다.")

# -------------------------------
# 답안 입력
# -------------------------------
st.subheader("답안 입력")
answers = st.text_input("답안을 입력하세요 (예: 1,2,3,4)")

# -------------------------------
# 제출 버튼
# -------------------------------
if st.button("제출하기"):
    if not selected_test:
        st.warning("응시할 시험을 먼저 선택하세요.")
    elif not answers:
        st.warning("답안을 입력하세요.")
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
