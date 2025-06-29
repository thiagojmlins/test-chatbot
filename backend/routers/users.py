from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.auth import get_current_user
from database import get_db
from services.user import UserService
import models, schemas
import logging

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    new_user = UserService.create_new_user(db, user)
    return new_user

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    logger.info(f"User {current_user.username} is currently logged in")
    return current_user 