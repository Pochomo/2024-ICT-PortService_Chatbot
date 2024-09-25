# app/schemas.py

# from pydantic import BaseModel
# from datetime import datetime
# from typing import List

# class UserCreate(BaseModel):
#     username: str
#     email: str
#     password: str

# class User(BaseModel):
#     id: int
#     username: str
#     email: str
#     class Config:
#         orm_mode = True

# class VisitBadgeCreate(BaseModel):
#     contact_person: str
#     visit_location: str
#     visit_purpose: str
#     start_time: datetime
#     end_time: datetime
#     visitor_name: str
#     visitor_phone: str
#     visitor_birthdate: str
#     visitor_company: str
#     business_registration_number: str
#     visitor_gender: str

# class VisitBadge(BaseModel):
#     id: int
#     user_id: int
#     contact_person: str
#     visit_location: str
#     visit_purpose: str
#     start_time: datetime
#     end_time: datetime
#     visitor_name: str
#     visitor_phone: str
#     visitor_birthdate: str
#     visitor_company: str
#     business_registration_number: str
#     visitor_gender: str
#     class Config:
#         orm_mode = True
