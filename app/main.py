from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles  # StaticFiles 임포트
from app.api.v1.endpoints import chat  # chat 모듈을 임포트

from fastapi.staticfiles import StaticFiles
from app.api.v1.endpoints import chat
from sqlalchemy import text
from mysql.connector import connect, Error
from sqlalchemy.orm import Session
from app.rdb import engine as rdb_engine, Base as rdb_Base, get_rdb
from app.rdb.models import User, Form, VisitBadge
from app.rdb import crud, schemas
from dotenv import load_dotenv
import uvicorn
import os

from app.rdb import engine, Base, get_rdb
from app.rdb.models import User, Form, VisitBadge



from pydantic import ValidationError
load_dotenv()
# 환경 변수 설정
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)
rdb_Base.metadata.create_all(bind=rdb_engine)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 현재 파일의 디렉토리를 기준으로 상대 경로 사용
current_dir = os.path.dirname(os.path.abspath(__file__))
static_directory = os.path.join(current_dir, "..", "public")
app.mount("/static", StaticFiles(directory=static_directory), name="static")

# chat.py의 라우터를 포함

app.include_router(chat.router, prefix="/api/v1")

@app.get("/api/v1/forms/{form_id}")
async def get_form(form_id: int, db: Session = Depends(get_rdb)):
    form = db.query(Form).filter(Form.id == form_id).first()
    
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found")
    return {
        "id": form.id,
        "title": form.title,
        "description": form.description,
        "fields": form.fields
    }


@app.post("/api/v1/submit-form")
async def submit_form(request: Request, db: Session = Depends(get_rdb)):
    body = await request.json()
    try:
        visit_badge = schemas.VisitBadgeCreate(**body)
        # user_id를 body에서 가져오되, 없으면 None으로 설정
        user_id = body.get('user_id')
        db_visit_badge = crud.create_visit_badge(db=db, visit_badge=visit_badge, user_id=user_id)
        return db_visit_badge
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_database_connection():
    try:
        connection = connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        print("Database connection successful")
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
    
def get_rdb_connection():
    try:
        connection = connect(
            DATABASE_URL = os.getenv('RDB_URL')
        )
        print("rdb connection successful")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Platform: {e}")
        raise HTTPException(status_code=500, detail="rdb connection failed")
    

@app.get("/check-rdb-connection")
async def check_rdb_connection(db: Session = Depends(get_rdb)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Database connection successful (AWS RDS)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Contest Entry 페이지를 제공하는 엔드포인트
@app.get("/contest-entry", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(static_directory, "index.html")
    print(f"Serving file from: {index_path}")  # 파일 경로를 출력하여 확인
    try:
        with open(index_path, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        print(f"Error: File {index_path} not found")  # 오류 로그 추가
        raise HTTPException(status_code=404, detail="index.html file not found")

# main 함수: uvicorn 서버 실행
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)