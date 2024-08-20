from fastapi import FastAPI, HTTPException, Query
from mysql.connector import connect, Error
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

# 환경 변수에서 데이터베이스 설정 읽기
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

app = FastAPI()

def get_database_connection():
    """데이터베이스 연결을 설정하고 반환합니다."""
    try:
        connection = connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Platform: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/fetch-info")
async def fetch_info(category: str = Query(None, title="Category", description="The category to fetch data for")):
    """지정된 카테고리에 따라 데이터베이스에서 정보를 조회합니다."""
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM some_table WHERE category = %s"
        cursor.execute(query, (category,))
        results = cursor.fetchall()
        return {"data": results}
    except Error as e:
        print(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {e}")
    finally:
        cursor.close()
        conn.close()
