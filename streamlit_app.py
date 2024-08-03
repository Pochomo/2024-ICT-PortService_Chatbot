import streamlit as st
import requests

# FastAPI 백엔드 URL 설정
BACKEND_URL = "http://localhost:8000"

# 채팅 입력 및 전송
st.title("Chat with Vector Database")
user_input = st.text_input("Your message:", "")

if st.button("Send"):
    if user_input:
        # FastAPI 백엔드로 요청 전송
        response = requests.post(f"{BACKEND_URL}/chat", json={"message": user_input})
        if response.status_code == 200:
            st.write(f"Response: {response.json()['response']}")
        else:
            st.write(f"Error: {response.status_code}")
    else:
        st.write("Please enter a message.")

# 벡터 저장소 확인
if st.button("Get Vectors"):
    response = requests.get(f"{BACKEND_URL}/vectors")
    if response.status_code == 200:
        vectors = response.json()
        st.write("저장된 벡터 데이터:")
        st.write(vectors)
    else:
        st.write(f"Error: {response.status_code}")
