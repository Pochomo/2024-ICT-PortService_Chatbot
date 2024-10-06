# app/database.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

from dotenv import load_dotenv
load_dotenv()
RDB_URL = os.getenv('RDB_URL')




engine = create_engine(RDB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        return False

# Dependency for getting the database session
def get_rdb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

