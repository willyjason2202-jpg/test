import streamlit as st
import pandas as pd

st.title("학생 채점 시스템")

# -------------------------
# 1. URL에서 학생ID 읽기
# -------------------------
params = st.query_params
student_id = str(params.get("student", "")).strip()

if not student_id:
    st.error("학생 전용 링크가 아닙니다.")
    st.stop()

# -------------------------
# 2. 학생정보 (임시 데이터)
# -------------------------
students = [
    {"학생ID": "1", "학생이름": "김민수", "학교": "예일여고"},
    {"학생ID": "2", "학생이름": "이서연", "학교": "대성고"},
    {"학생ID": "3", "학생이름": "박준호", "학교": "예일여고"},
]

# -------------------------
# 3. 학생 찾기
# -------------------------
student = None
for s in students:
    if s["학생ID"] == student_id:
        student = s
        break

if not student:
    st.error("등록되지 않은 학생입니다.")
    st.stop()

# -------------------------
# 4. 이름 출력
# -------------------------
st.subheader(f"{student['학생이름']} 학생")
st.caption(f"학교: {student['학교']}")

# -------------------------
# 5. 시험정보 (임시 데이터)
# -------------------------
tests = [
    {"시험ID": "EX001", "시험명": "4월 모의고사", "학교": "예일여고"},
    {"시험ID": "EX002", "시험명": "5월 모의고사", "학교": "예일여고"},
    {"시험ID": "EX003", "시험명": "단어시험", "학교": "대성고"},
]

# -------------------------
# 6. 학교 기준 필터
# -------------------------
available_tests = []

for t in tests:
    if t["학교"] == student["학교"]:
        available_tests.append(t)

# -------------------------
# 7. 시험 선택창
# -------------------------
if available_tests:
    test_names = [t["시험명"] for t in available_tests]
    selected_test = st.selectbox("응시할 시험 선택", test_names)
else:
    st.warning("응시 가능한 시험이 없습니다.")
