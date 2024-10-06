from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .rdb import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)  # 길이를 50으로 지정
    email = Column(String(100), unique=True, index=True)    # 길이를 100으로 지정
    hashed_password = Column(String(100))                   # 길이를 100으로 지정
    
    forms = relationship("Form", back_populates="owner")
    visit_badges = relationship("VisitBadge", back_populates="user")

class Form(Base):
    __tablename__ = "forms"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True)                 # 길이를 100으로 지정
    description = Column(String(255))                       # 길이를 255로 지정
    fields = relationship("FormField", back_populates="form")
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="forms")

class FormField(Base):
    __tablename__ = "form_fields"
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey('forms.id'))
    field_name = Column(String(50))                         # 길이를 50으로 지정
    field_type = Column(String(20))                         # 길이를 20으로 지정
    label = Column(String(100))                             # 길이를 100으로 지정
    placeholder = Column(String(100))                       # 길이를 100으로 지정
    is_required = Column(Boolean)
    form = relationship("Form", back_populates="fields")

class VisitBadge(Base):
    __tablename__ = 'visit_badges'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    contact_person = Column(String(100))                    # 길이를 100으로 지정
    visit_location = Column(String(255))                    # 길이를 255로 지정
    visit_purpose = Column(String(255))                     # 길이를 255로 지정
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    visitor_name = Column(String(100))                      # 길이를 100으로 지정
    visitor_phone = Column(String(20))                      # 길이를 20으로 지정
    visitor_birthdate = Column(String(10))                  # 길이를 10으로 지정
    visitor_company = Column(String(100))                   # 길이를 100으로 지정
    business_registration_number = Column(String(20))       # 길이를 20으로 지정
    visitor_gender = Column(String(10))                     # 길이를 10으로 지정
    
    user = relationship("User", back_populates="visit_badges")