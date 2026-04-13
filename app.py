import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials

st.title("학생 채점 시스템")

# -------------------------
# 0. 구글시트 연결
# -------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1WZGrjTSF8ZfD3gbU6DR4mivsdVSGusLL/edit?usp=sharing&ouid=111504349976400776284&rtpof=true&sd=true")

students_ws = spreadsheet.worksheet("학생정보")
tests_ws = spreadsheet.worksheet("시험정보")

students = students_ws.get_all_records()
tests = tests_ws.get_all_records()

# -------------------------
# 1. URL에서 학생ID 읽기
# -------------------------
params = st.query_params
student_id = str(params.get("student", "")).strip()

if not student_id:
    st.error("학생 전용 링크가 아닙니다.")
    st.stop()

# -------------------------
# 2. 학생 찾기
# -------------------------
student = None
for s in students:
    if str(s["학생ID"]).strip() == student_id:
        student = s
        break

if not student:
    st.error("등록되지 않은 학생입니다.")
    st.stop()

# -------------------------
# 3. 이름 출력
# -------------------------
st.subheader(f"{student['학생이름']} 학생")
st.caption(f"학교: {student['학교']}")

# -------------------------
# 4. 학교 기준 시험 필터
# -------------------------
available_tests = []

for t in tests:
    if str(t["학교"]).strip() == str(student["학교"]).strip():
        available_tests.append(t)

# -------------------------
# 5. 시험 선택창
# -------------------------
if available_tests:
    test_names = [t["시험명"] for t in available_tests]
    selected_test = st.selectbox("응시할 시험 선택", test_names)
else:
    st.warning("응시 가능한 시험이 없습니다.")
