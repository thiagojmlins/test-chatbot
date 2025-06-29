from fastapi import HTTPException, status
from typing import Optional, Any, Dict


class ChatbotException(HTTPException):
    """Base exception for chatbot application errors."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class MessageNotFoundError(ChatbotException):
    """Raised when a message is not found."""
    
    def __init__(self, message_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id {message_id} not found"
        )


class UserNotFoundError(ChatbotException):
    """Raised when a user is not found."""
    
    def __init__(self, username: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )


class UserAlreadyExistsError(ChatbotException):
    """Raised when trying to create a user that already exists."""
    
    def __init__(self, username: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' is already registered"
        )


class AuthenticationError(ChatbotException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Incorrect username or password"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(ChatbotException):
    """Raised when user is not authorized to perform an action."""
    
    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ChatbotServiceError(ChatbotException):
    """Raised when there's an error with the chatbot service."""
    
    def __init__(self, detail: str = "Error communicating with chatbot service"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class ValidationError(ChatbotException):
    """Raised when input validation fails."""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        ) 