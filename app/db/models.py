from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Information(Base):
    __tablename__ = "All_information"

    id = Column(Integer, primary_key=True, index=True)
    chat_log_id = Column(Integer)
    button_name = Column(String(255), nullable=False) 
    response_text = Column(String(1500), nullable=True)
    link = Column(String(1000), nullable=True)
