# from fastapi import FastAPI, HTTPException
# from mysql.connector import connect, Error
# import os

# app = FastAPI()


# def get_database_connection():
#     try:
#         connection = connect(
#             host="ict-chat.c7a6km20gu3m.ap-northeast-2.rds.amazonaws.com",  # 여기에 실제 데이터베이스 호스트를 넣으세요
#             user="root",  # 여기에 실제 데이터베이스 사용자명을 넣으세요
#             password="2021125027",  # 여기에 실제 데이터베이스 비밀번호를 넣으세요
#             database="ict-chat"  # 여기에 실제 데이터베이스 이름을 넣으세요
#         )
#         print("Database connection successful")  # 연결 성공 시 메시지 출력
#         return connection
#     except Error as e:
#         print(f"Error connecting to MySQL Platform: {e}")
#         raise HTTPException(status_code=500, detail="Database connection failed")


# # DB 연결 확인용 엔드포인트
# @app.get("/check-db-connection")
# async def check_db_connection():
#     try:
#         conn = get_database_connection()
#         conn.close()
#         return {"status": "Database connection successful"}
#     except HTTPException as e:
#         return {"status": str(e.detail)}

# @app.get("/get-button-response/{button_id}")
# async def get_button_response(button_id: int):
#     try:
#         conn = get_database_connection()
#         cursor = conn.cursor()

#         # 버튼 ID로 in_out_report 테이블에서 데이터를 가져옵니다.
#         query = "SELECT button_text FROM in_out_report WHERE id = %s"
#         cursor.execute(query, (button_id,))
#         result = cursor.fetchone()

#         if result:
#             return {"response": result[0]}  # button_text 값 반환
#         else:
#             raise HTTPException(status_code=404, detail="Data not found")

#     except Error as e:
#         print(f"Error executing query: {e}")
#         raise HTTPException(status_code=500, detail="Database query failed")
#     finally:
#         cursor.close()
#         conn.close()
