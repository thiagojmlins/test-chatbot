from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from core.exceptions import UserAlreadyExistsError, UserNotFoundError
import models, schemas
from core.auth import get_password_hash, verify_password
from database import DatabaseManager
from core.cache import cache_manager, cache_invalidate
from services.query import QueryService

class UserService:
    """Service for handling user operations with improved database management and caching."""
    
    @staticmethod
    @cache_invalidate("user:*")
    def create_new_user(db: Session, user: schemas.UserCreate) -> models.User:
        """
        Create a new user with validation and error handling.
        
        Args:
            db: Database session
            user: User creation data
            
        Returns:
            The created user
            
        Raises:
            UserAlreadyExistsError: If username already exists
        """
        def _create_user_operation():
            # Check if user already exists
            existing_user = QueryService.get_user_by_username(db, user.username)
            
            if existing_user:
                raise UserAlreadyExistsError(user.username)
            
            # Create new user
            hashed_password = get_password_hash(user.password)
            new_user = models.User(
                username=user.username,
                hashed_password=hashed_password
            )
            
            db.add(new_user)
            db.flush()
            db.refresh(new_user)
            
            return new_user
        
        return DatabaseManager.execute_with_retry(_create_user_operation)

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
        """
        Get a user by their ID with caching.
        
        Args:
            db: Database session
            user_id: ID of the user to retrieve
            
        Returns:
            User object or None if not found
        """
        return QueryService.get_user_by_id(db, user_id)

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
        """
        Get a user by their username with caching.
        
        Args:
            db: Database session
            username: Username to search for
            
        Returns:
            User object or None if not found
        """
        return QueryService.get_user_by_username(db, username)

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
        """
        Authenticate a user with username and password.
        
        Args:
            db: Database session
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = UserService.get_user_by_username(db, username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user

    @staticmethod
    @cache_invalidate("user:*")
    def update_user_password(db: Session, user_id: int, new_password: str) -> models.User:
        """
        Update a user's password.
        
        Args:
            db: Database session
            user_id: ID of the user
            new_password: New password to set
            
        Returns:
            Updated user object
            
        Raises:
            UserNotFoundError: If user is not found
        """
        def _update_password_operation():
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                raise UserNotFoundError(user_id)
            
            user.hashed_password = get_password_hash(new_password)
            db.flush()
            db.refresh(user)
            
            return user
        
        return DatabaseManager.execute_with_retry(_update_password_operation)

    @staticmethod
    @cache_invalidate("user:*")
    def delete_user(db: Session, user_id: int) -> models.User:
        """
        Delete a user and all their associated data.
        
        Args:
            db: Database session
            user_id: ID of the user to delete
            
        Returns:
            The deleted user object
            
        Raises:
            UserNotFoundError: If user is not found
        """
        def _delete_user_operation():
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                raise UserNotFoundError(user_id)
            
            # Delete all user messages first (cascade delete)
            db.query(models.Message).filter(
                models.Message.user_id == user_id
            ).delete()
            
            # Delete the user
            db.delete(user)
            db.flush()
            
            return user
        
        return DatabaseManager.execute_with_retry(_delete_user_operation)

    @staticmethod
    def get_users_paginated(db: Session, skip: int = 0, limit: int = 10) -> List[models.User]:
        """
        Get paginated list of users.
        
        Args:
            db: Database session
            skip: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of users
        """
        return db.query(models.User).order_by(models.User.id).offset(skip).limit(limit).all()

    @staticmethod
    def get_user_count(db: Session) -> int:
        """
        Get the total number of users.
        
        Args:
            db: Database session
            
        Returns:
            Total number of users
        """
        return db.query(models.User).count()

    @staticmethod
    def search_users(db: Session, search_term: str, limit: int = 10) -> List[models.User]:
        """
        Search users by username.
        
        Args:
            db: Database session
            search_term: Term to search for in usernames
            limit: Maximum number of results to return
            
        Returns:
            List of users matching the search term
        """
        return db.query(models.User).filter(
            models.User.username.ilike(f"%{search_term}%")
        ).order_by(models.User.username).limit(limit).all()

    @staticmethod
    def get_user_with_messages(db: Session, user_id: int) -> Optional[models.User]:
        """
        Get a user with their messages loaded.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            User object with messages loaded or None if not found
        """
        from sqlalchemy.orm import joinedload
        
        return db.query(models.User).options(
            joinedload(models.User.messages)
        ).filter(models.User.id == user_id).first()

    @staticmethod
    def get_user_stats(db: Session, user_id: int) -> dict:
        """
        Get statistics for a user with caching.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            Dictionary with user statistics
        """
        return QueryService.get_user_stats(db, user_id)

    @staticmethod
    def get_user_activity_summary(db: Session, user_id: int, days: int = 30) -> dict:
        """
        Get user activity summary for the last N days.
        
        Args:
            db: Database session
            user_id: ID of the user
            days: Number of days to analyze
            
        Returns:
            Activity summary dictionary
        """
        return QueryService.get_user_activity_summary(db, user_id, days) 