import streamlit as st

st.title("채점 프로그램")

# 시험 선택 (임시)
test_name = st.selectbox("시험 선택", ["4월 모의고사"])

st.write(f"선택한 시험: {test_name}")

# 정답 (임시)
answer_key = [3,3,4,1,3,5,4,1,3,5,2,5,1,4,2,4,5,3,4,5,5,3,4,5,3,5,3,2,4]

st.write("답안을 선택하세요")

student_answers = []

for i in range(len(answer_key)):
    ans = st.radio(
        f"{i+1}번",
        ["", "1", "2", "3", "4", "5"],
        horizontal=True,
        key=i
    )
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
