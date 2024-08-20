from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MILVUS_HOST: str
    MILVUS_PORT: str
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    ELASTICSEARCH_HOST: str
    ELASTICSEARCH_PORT: str

    class Config:
        env_file = ".env"

settings = Settings()