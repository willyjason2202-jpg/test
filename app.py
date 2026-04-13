import streamlit as st
import pandas as pd

st.title("채점 프로그램")

answer_key = [3,3,4,1,3,5,4,1,3,5,2,5,1,4,2,4,5,3,4,5,5,3,4,5,3,5,3,2,4]

st.write("답 입력")

student_answers = []
for i in range(len(answer_key)):
    ans = st.text_input(f"{i+1}번", key=i)
    student_answers.append(ans)

if st.button("채점하기"):
    correct = 0
    wrong_list = []

    for i in range(len(answer_key)):
        try:
            if int(student_answers[i]) == answer_key[i]:
                correct += 1
            else:
                wrong_list.append(i+1)
        except:
            wrong_list.append(i+1)

    st.write(f"점수: {correct}/{len(answer_key)}")
    st.write(f"오답: {wrong_list}")
