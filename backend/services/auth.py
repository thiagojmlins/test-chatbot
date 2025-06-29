from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from core.exceptions import AuthenticationError
from core.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from services.user import UserService

class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def authenticate_and_create_token(db: Session, username: str, password: str) -> dict:
        """
        Authenticate a user and create an access token.
        
        Args:
            db: Database session
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            Dictionary containing access token and token type
            
        Raises:
            AuthenticationError: If authentication fails
        """
        user = UserService.authenticate_user(db, username, password)
        if not user:
            raise AuthenticationError("Incorrect username or password")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}

    @staticmethod
    def get_current_user(db: Session, username: str) -> Optional[dict]:
        """
        Get current user information by username.
        
        Args:
            db: Database session
            username: Username to retrieve
            
        Returns:
            User information dictionary or None if not found
        """
        user = UserService.get_user_by_username(db, username)
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "message_count": UserService.get_user_stats(db, user.id)["total_messages"]
        }

    @staticmethod
    def validate_token_payload(payload: dict) -> bool:
        """
        Validate JWT token payload.
        
        Args:
            payload: JWT token payload
            
        Returns:
            True if payload is valid, False otherwise
        """
        required_fields = ["sub", "exp"]
        return all(field in payload for field in required_fields) 