# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.api.v1.endpoints import chat
# import uvicorn
# import os
# os.environ["TOKENIZERS_PARALLELISM"] = "false"

# app = FastAPI()

# # CORS 설정
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # chat.py의 라우터 포함
# app.include_router(chat.router, prefix="/api/v1")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)