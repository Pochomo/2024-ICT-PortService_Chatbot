from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import openai
from dotenv import load_dotenv
import os

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
print(openai.api_key)
# OpenAI API 키 설정
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")

openai.api_key = openai_api_key

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get('message')
    if not user_input:
        raise HTTPException(status_code=400, detail="No input provided")

    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',  # 사용모델
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1024,  # 반환되는 텍스트 길이
            n=1,
            stop=None,
            temperature=0.5
        )
        bot_response = response['choices'][0]['message']['content'].strip()
        return JSONResponse(content={'response': bot_response})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':

    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
