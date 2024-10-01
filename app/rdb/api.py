# # app/api.py

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from . import crud, rdb, schemas

# router = APIRouter()

# # 유저 생성 엔드포인트
# @router.post("/users/", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(rdb.get_db)):
#     db_user = crud.get_user_by_username(db, username=user.username)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Username already registered")
#     return crud.create_user(db, user)

# # 유저별 방문 정보 등록 엔드포인트
# @router.post("/users/{user_id}/visit-badges/", response_model=schemas.VisitBadge)
# def create_visit_badge_for_user(user_id: int, visit_badge: schemas.VisitBadgeCreate, db: Session = Depends(rdb.get_db)):
#     return crud.create_visit_badge(db=db, visit_badge=visit_badge, user_id=user_id)

# # 유저별 방문 정보 조회 엔드포인트
# @router.get("/users/{user_id}/visit-badges/", response_model=List[schemas.VisitBadge])
# def get_visit_badges_for_user(user_id: int, db: Session = Depends(rdb.get_db)):
#     return crud.get_visit_badges_by_user(db=db, user_id=user_id)
