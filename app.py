import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("학생 채점 시스템")

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)
client = gspread.authorize(creds)

spreadsheet = client.open_by_url("채점프로그램_구글시트_초안")

students_ws = spreadsheet.worksheet("학생정보")
tests_ws = spreadsheet.worksheet("시험정보")

students = students_ws.get_all_records()
tests = tests_ws.get_all_records()

params = st.query_params
student_id = str(params.get("student", "")).strip()

if not student_id:
    st.error("학생 전용 링크가 아닙니다.")
    st.stop()

student = None
for s in students:
    if str(s["학생ID"]).strip() == student_id:
        student = s
        break

if not student:
    st.error("등록되지 않은 학생입니다.")
    st.stop()

st.subheader(f"{student['학생이름']} 학생")
st.caption(f"학교: {student['학교']}")

available_tests = []
for t in tests:
    if str(t["학교"]).strip() == str(student["학교"]).strip():
        available_tests.append(t)

if available_tests:
    test_names = [t["시험명"] for t in available_tests]
    st.selectbox("응시할 시험 선택", test_names)
else:
    st.warning("응시 가능한 시험이 없습니다.")
