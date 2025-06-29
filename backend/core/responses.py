from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from .exceptions import ChatbotException


def create_error_response(
    status_code: int,
    detail: str,
    error_code: Optional[str] = None,
    headers: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        detail: Error message
        error_code: Optional error code for client handling
        headers: Optional HTTP headers
    
    Returns:
        JSONResponse with standardized error format
    """
    error_data = {
        "error": {
            "message": detail,
            "status_code": status_code
        }
    }
    
    if error_code:
        error_data["error"]["code"] = error_code
    
    return JSONResponse(
        status_code=status_code,
        content=error_data,
        headers=headers
    )


def create_success_response(
    data: Any,
    status_code: int = 200,
    message: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        status_code: HTTP status code (default: 200)
        message: Optional success message
    
    Returns:
        JSONResponse with standardized success format
    """
    response_data = {"data": data}
    
    if message:
        response_data["message"] = message
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def handle_exception_response(exc: ChatbotException) -> JSONResponse:
    """
    Handle ChatbotException and return standardized response.
    
    Args:
        exc: ChatbotException instance
    
    Returns:
        JSONResponse with standardized error format
    """
    return create_error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        headers=exc.headers
    )


# Common error responses
def not_found_response(resource: str, identifier: str) -> JSONResponse:
    """Create a standardized 404 response."""
    return create_error_response(
        status_code=404,
        detail=f"{resource} with identifier '{identifier}' not found",
        error_code="NOT_FOUND"
    )


def validation_error_response(detail: str) -> JSONResponse:
    """Create a standardized 422 validation error response."""
    return create_error_response(
        status_code=422,
        detail=detail,
        error_code="VALIDATION_ERROR"
    )


def authentication_error_response(detail: str = "Authentication failed") -> JSONResponse:
    """Create a standardized 401 authentication error response."""
    return create_error_response(
        status_code=401,
        detail=detail,
        error_code="AUTHENTICATION_ERROR",
        headers={"WWW-Authenticate": "Bearer"}
    )


def authorization_error_response(detail: str = "Not authorized") -> JSONResponse:
    """Create a standardized 403 authorization error response."""
    return create_error_response(
        status_code=403,
        detail=detail,
        error_code="AUTHORIZATION_ERROR"
    )


def internal_server_error_response(detail: str = "Internal server error") -> JSONResponse:
    """Create a standardized 500 internal server error response."""
    return create_error_response(
        status_code=500,
        detail=detail,
        error_code="INTERNAL_SERVER_ERROR"
    ) 