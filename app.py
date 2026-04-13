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
