from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import chat  # chat 모듈을 임포트
from mysql.connector import connect, Error
import uvicorn
import os

# 환경 변수 설정
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에 대해 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드를 허용
    allow_headers=["*"],  # 모든 헤더를 허용
)

# chat.py의 라우터를 포함
app.include_router(chat.router, prefix="/api/v1")

# 데이터베이스 연결 함수
def get_database_connection():
    try:
        connection = connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        print("Database connection successful")  # 연결 성공 시 메시지 출력
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Platform: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# DB 연결 확인용 엔드포인트
@app.get("/check-db-connection")
async def check_db_connection():
    try:
        conn = get_database_connection()
        conn.close()
        return {"status": "Database connection successful"}
    except HTTPException as e:
        return {"status": str(e.detail)}

# main 함수: uvicorn 서버 실행
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
