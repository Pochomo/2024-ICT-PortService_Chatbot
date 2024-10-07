# app/schemas.py
from pydantic import BaseModel, validator
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str

    class Config:
            from_attributes = True


class VisitBadgeCreate(BaseModel):
    user_id: Optional[int] = None
    contact_person: str
    visit_location: str
    visit_purpose: str
    start_time: datetime
    end_time: datetime
    visitor_name: str
    visitor_phone: str
    visitor_birthdate: str
    visitor_company: str
    business_registration_number: str
    visitor_gender: str

class VisitBadge(VisitBadgeCreate):
    id: int
    user_id: Optional[int] = None

    @validator('*', pre=True)
    def check_empty_string(cls, v):
        if isinstance(v, str) and v.strip() == '':
            raise ValueError('Field cannot be empty string')
        return v

    @validator('start_time', 'end_time')
    def check_datetime(cls, v):
        if not isinstance(v, datetime):
            raise ValueError(f'Invalid datetime format: {v}')
        return v
    class Config:
        from_attributes = True

class FormFieldBase(BaseModel):
    field_name: str
    field_type: str
    label: str
    placeholder: Optional[str] = None
    is_required: bool

class FormField(FormFieldBase):
    id: int
    form_id: int

    class Config:
        from_attributes = True

class FormCreate(BaseModel):
    title: str
    description: Optional[str] = None
    fields: List[FormFieldBase]

class Form(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    fields: List[FormField]

    class Config:
        from_attributes = True