from app.db import models, database

def init_db():
    db = database.SessionLocal()
    info1 = models.Information(title="항만 입/출항 신고 절차", content="항만 입/출항 신고 절차에 대한 정보입니다.")
    info2 = models.Information(title="화물 입/출항 신고 절차", content="화물 입/출항 신고 절차에 대한 정보입니다.")
    db.add(info1)
    db.add(info2)
    db.commit()
    db.close()

if __name__ == "__main__":
    init_db()
