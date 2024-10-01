from pydantic_settings import BaseSettings
from pydantic import SecretStr
from dotenv import load_dotenv
import os
from typing import Optional

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[SecretStr] = SecretStr(os.getenv("OPENAI_API_KEY", "")) if os.getenv("OPENAI_API_KEY") else None
    MILVUS_HOST: Optional[str] = os.getenv("MILVUS_HOST")
    MILVUS_PORT: Optional[str] = os.getenv("MILVUS_PORT")
    DB_HOST: Optional[str] = os.getenv("DB_HOST")
    DB_USER: Optional[str] = os.getenv("DB_USER")
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
    DB_NAME: Optional[str] = os.getenv("DB_NAME")
    ELASTICSEARCH_HOST: Optional[str] = os.getenv("ELASTICSEARCH_HOST")
    ELASTICSEARCH_PORT: Optional[str] = os.getenv("ELASTICSEARCH_PORT")
    #RDB_URL: Optional[str] = os.getenv("RDB_URL")
    class Config:
        env_file = ".env"

# Settings 인스턴스 생성
settings = Settings()

# OPENAI_API_KEY를 사용해야 할 때는 .get_secret_value() 사용
if settings.OPENAI_API_KEY:
    openai_api_key = settings.OPENAI_API_KEY.get_secret_value()  # SecretStr에서 실제 값을 추출
else:
    openai_api_key = None

