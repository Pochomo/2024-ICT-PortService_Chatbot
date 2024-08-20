import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/api/v1"

st.title("Chat with AI and Documents")

# HWP 파일 업로드
uploaded_file = st.file_uploader("Upload an HWP file", type="hwp")
if uploaded_file is not None:
    files = {"file": ("document.hwp", uploaded_file, "application/x-hwp")}
    response = requests.post(f"{BACKEND_URL}/upload-hwp", files=files)
    if response.status_code == 200:
        st.success("File uploaded and processed successfully!")
    else:
        st.error(f"Error: {response.status_code}")

# 채팅 모드 선택
chat_mode = st.radio("Select chat mode:", ("Normal Chat", "RAG Chat"))

# 채팅 입력 및 전송
user_input = st.text_input("Your message:", "")

if st.button("Send"):
    if user_input:
        if chat_mode == "Normal Chat":
            response = requests.post(f"{BACKEND_URL}/chat", json={"message": user_input})
        else:  # RAG Chat
            response = requests.post(f"{BACKEND_URL}/rag-chat", json={"query": user_input})
        
        if response.status_code == 200:
            st.write(f"Response: {response.json()['response']}")
        else:
            st.write(f"Error: {response.status_code}")
    else:
        st.write("Please enter a message.")