from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
from app.services.vector_db import create_vector_store, search_vector_store, save_vector, get_all_vectors
import numpy as np
import logging

# 환경 변수 로드 (.env 파일에서 API 키 등을 로드)
load_dotenv()

# FastAPI 애플리케이션 생성
app = FastAPI()

# CORS 설정: 다른 도메인에서 이 API에 접근할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요한 도메인으로 변경 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI 비동기 클라이언트 설정
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 입력 텍스트를 임베딩 벡터로 변환하는 함수
async def get_embedding(text: str):
    response = await client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# /chat 엔드포인트: 사용자의 입력을 받아 OpenAI의 GPT-3.5 모델로 응답 생성
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get('message')
    if not user_input:
        raise HTTPException(status_code=400, detail="No input provided")

    try:
        # OpenAI ChatCompletion API 호출하여 응답 생성
        response = await client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": "You are a chatbot specialized in port authority services. Answer questions concisely and informatively."},  # 시스템 메시지
                {"role": "user", "content": user_input}  # 사용자 입력 메시지
            ],
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5
        )
        bot_response = response.choices[0].message.content

        # 사용자 입력을 벡터로 변환하여 저장
        vector = await get_embedding(user_input)
        vector_bytes = np.array(vector).tobytes()
        save_vector(vector_bytes)  # 벡터 저장

        return JSONResponse(content={'response': bot_response})
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# /vectors 엔드포인트: 벡터 데이터베이스에서 모든 벡터 읽기
@app.get("/vectors")
async def read_vectors():
    try:
        vectors = get_all_vectors()
        logging.info(f"Vectors fetched successfully: {vectors}")
        return JSONResponse(content=vectors)
    except Exception as e:
        logging.error(f"Error fetching vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# /vectors/log 엔드포인트: 벡터 데이터베이스에서 모든 벡터 로그 출력
@app.get("/vectors/log")
async def log_vectors():
    try:
        vectors = get_all_vectors()
        for vector in vectors:
            logging.info(f"Vector ID: {vector[0]}, Vector Data: {vector[1]}")
        return JSONResponse(content={'detail': 'Vectors logged successfully'})
    except Exception as e:
        logging.error(f"Error logging vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# /vectors/download 엔드포인트: 벡터 데이터베이스에서 모든 벡터 파일로 저장
@app.get("/vectors/download")
async def download_vectors():
    try:
        vectors = get_all_vectors()
        with open('vectors.txt', 'w') as f:
            for vector in vectors:
                f.write(f"Vector ID: {vector[0]}, Vector Data: {vector[1]}\n")
        return JSONResponse(content={'detail': 'Vectors saved to file successfully'})
    except Exception as e:
        logging.error(f"Error saving vectors to file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# /favicon.ico 엔드포인트: favicon 요청 무시
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return JSONResponse(content={}, status_code=204)

# 애플리케이션 실행: 개발 환경에서는 uvicorn을 사용하여 실행
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
