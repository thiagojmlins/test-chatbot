from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.auth import get_current_user
from database import get_db
from services.user import UserService
from core.config import PAGINATION_DEFAULT_LIMIT, PAGINATION_MAX_LIMIT
import models, schemas
import logging

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    return schemas.User.from_orm(UserService.create_new_user(db, user))

@router.post("/login", response_model=schemas.Token)
def login_user(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token."""
    user = UserService.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    from core.auth import create_access_token
    access_token = create_access_token(data={"sub": user.username, "id": user.id})
    return schemas.Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=schemas.User)
def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information."""
    user = UserService.get_user_by_id(db, current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.User.from_orm(user)

@router.get("/me/stats", response_model=schemas.UserStats)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user statistics."""
    stats = UserService.get_user_stats(db, current_user["id"])
    return schemas.UserStats(**stats)

@router.get("/me/activity", response_model=schemas.UserActivity)
def get_user_activity(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user activity summary."""
    activity = UserService.get_user_activity_summary(db, current_user["id"], days)
    return schemas.UserActivity(**activity)

@router.put("/me/password", response_model=schemas.User)
def update_password(
    password_update: schemas.PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update current user password."""
    user = UserService.update_user_password(db, current_user["id"], password_update.new_password)
    return schemas.User.from_orm(user)

@router.delete("/me", response_model=schemas.User)
def delete_account(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete current user account."""
    user = UserService.delete_user(db, current_user["id"])
    return schemas.User.from_orm(user)

@router.get("/", response_model=schemas.UserListResponse)
def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(PAGINATION_DEFAULT_LIMIT, ge=1, le=PAGINATION_MAX_LIMIT, description="Number of users to return"),
    search: str = Query(None, description="Search term for username"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated list of users (admin only)."""
    # TODO: Add admin role check
    if search:
        users = UserService.search_users(db, search, limit)
        total = len(users)
    else:
        users = UserService.get_users_paginated(db, skip, limit)
        total = UserService.get_user_count(db)
    
    return schemas.UserListResponse(
        users=[schemas.User.from_orm(user) for user in users],
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/{user_id}", response_model=schemas.User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user by ID (admin only)."""
    # TODO: Add admin role check
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.User.from_orm(user)

@router.get("/{user_id}/stats", response_model=schemas.UserStats)
def get_user_stats_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user statistics by ID (admin only)."""
    # TODO: Add admin role check
    stats = UserService.get_user_stats(db, user_id)
    return schemas.UserStats(**stats)

@router.get("/{user_id}/activity", response_model=schemas.UserActivity)
def get_user_activity_by_id(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user activity summary by ID (admin only)."""
    # TODO: Add admin role check
    activity = UserService.get_user_activity_summary(db, user_id, days)
    return schemas.UserActivity(**activity) 