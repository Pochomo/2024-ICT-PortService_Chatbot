# # app/database.py
# import os
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from app.core.config import settings

# from dotenv import load_dotenv

# load_dotenv()
# DATABASE_URL = os.getenv('RDB_URL')


# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # Dependency for getting the database session
# def get_rdb():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
