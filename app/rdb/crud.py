# app/crud.py
import logging
from sqlalchemy.orm import Session
from . import models, schemas
from typing import Optional

logger = logging.getLogger(__name__)
# 유저 생성 함수
def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(username=user.username, email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 방문 정보 생성 함수 (user_id를 선택적으로 받도록 수정)
def create_visit_badge(db: Session, visit_badge: schemas.VisitBadgeCreate, user_id: Optional[int] = None):
    visit_badge_data = visit_badge.dict()
    if user_id is not None:
        visit_badge_data['user_id'] = user_id
    db_visit_badge = models.VisitBadge(**visit_badge_data)
    db.add(db_visit_badge)
    db.commit()
    db.refresh(db_visit_badge)
    return db_visit_badge

# 유저별 방문 정보 조회 함수
def get_visit_badges_by_user(db: Session, user_id: int):
    return db.query(models.VisitBadge).filter(models.VisitBadge.user_id == user_id).all()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

# Form 생성 함수
def create_form(db: Session, form: schemas.FormCreate):
    logger.info(f"Attempting to create form: {form.dict()}")
    db_form = models.Form(**form.dict(exclude={'fields'}))
    db.add(db_form)
    db.flush()  # This assigns an ID to db_form without committing the transaction
    
    for field in form.fields:
        db_field = models.FormField(**field, form_id=db_form.id)
        db.add(db_field)
    
    try:
        db.commit()
        db.refresh(db_form)
        logger.info(f"Form created successfully: {db_form.id}")
        return db_form
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating form: {str(e)}")
        raise

# Form 조회 함수
def get_form(db: Session, form_id: int):
    return db.query(models.Form).filter(models.Form.id == form_id).first()

def get_form_fields(db: Session, form_id: int):
    return db.query(models.FormField).filter(models.FormField.form_id == form_id).all()

