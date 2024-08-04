from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
from app.services.vector_db import get_all_vectors, create_vector_store, search_vector_store, save_vector
import numpy as np

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요한 도메인으로 변경 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI 비동기 클라이언트 설정
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

async def get_embedding(text: str):
    response = await client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get('message')
    if not user_input:
        raise HTTPException(status_code=400, detail="No input provided")

    try:
        response = await client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5
        )
        bot_response = response.choices[0].message.content

        # 벡터로 변환하여 저장
        vector = await get_embedding(user_input)
        vector_bytes = np.array(vector).tobytes()
        save_vector(vector_bytes)  # 비동기 함수가 아니므로 await 사용하지 않음

        return JSONResponse(content={'response': bot_response})
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vectors")
async def create_vectors(request: Request):
    data = await request.json()
    documents = data.get('documents')
    if not documents:
        raise HTTPException(status_code=400, detail="No documents provided")

    try:
        await create_vector_store(documents)
        return JSONResponse(content={'detail': 'Vectors created successfully'})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vectors")
async def read_vectors():
    return await get_all_vectors()

@app.post("/vectors/search")
async def search_vectors(request: Request):
    data = await request.json()
    query = data.get('query')
    if not query:
        raise HTTPException(status_code=400, detail="No query provided")

    try:
        documents = [doc[1] for doc in await get_all_vectors()]
        index = await create_vector_store(documents)
        
        indices = await search_vector_store(query, index)
        return JSONResponse(content={'indices': indices.tolist()})
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return JSONResponse(content={}, status_code=204)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
