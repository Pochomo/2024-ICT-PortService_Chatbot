# app/models.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .rdb import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    forms = relationship("Form", back_populates="owner")
    visit_badges = relationship("VisitBadge", back_populates="user")  # 유저와 방문 정보 관계 설정

class Form(Base):
    __tablename__ = 'forms'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey('users.id'))
    
    owner = relationship("User", back_populates="forms")

class VisitBadge(Base):
    __tablename__ = 'visit_badges'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    contact_person = Column(String(255))
    visit_location = Column(String(255))
    visit_purpose = Column(String(255))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    visitor_name = Column(String(255))
    visitor_phone = Column(String(255))
    visitor_birthdate = Column(String(255))
    visitor_company = Column(String(255))
    business_registration_number = Column(String(255))
    visitor_gender = Column(String(255))
    
    user = relationship("User", back_populates="visit_badges")
