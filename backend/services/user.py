from sqlalchemy.orm import Session
from fastapi import HTTPException
import models, schemas
from core.auth import get_password_hash

class UserService:
    @staticmethod
    def create_new_user(db: Session, user: schemas.UserCreate):
        db_user = db.query(models.User).filter(models.User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        hashed_password = get_password_hash(user.password)
        new_user = models.User(username=user.username, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user 