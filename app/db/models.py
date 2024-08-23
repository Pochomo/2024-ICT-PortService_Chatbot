from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Information(Base):
    __tablename__ = "all_information"

    id = Column(Integer, primary_key=True, index=True)
    chat_log_id = Column(Integer)
    button_name = Column(String, index=True)
    response_text = Column(String)
    link = Column(String, nullable=True)
