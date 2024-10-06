# # app/crud.py

# from sqlalchemy.orm import Session
# from . import models, schemas

# # 유저 생성 함수
# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"  # 실제로는 해싱을 사용해야 함
#     db_user = models.User(username=user.username, email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# # 방문 정보 생성 함수
# def create_visit_badge(db: Session, visit_badge: schemas.VisitBadgeCreate, user_id: int):
#     db_visit_badge = models.VisitBadge(**visit_badge.dict(), user_id=user_id)
#     db.add(db_visit_badge)
#     db.commit()
#     db.refresh(db_visit_badge)
#     return db_visit_badge

# # 유저별 방문 정보 조회 함수
# def get_visit_badges_by_user(db: Session, user_id: int):
#     return db.query(models.VisitBadge).filter(models.VisitBadge.user_id == user_id).all()
