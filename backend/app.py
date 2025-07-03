from logging import getLogger
from fastapi import FastAPI, HTTPException, Depends, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.auth import get_current_user
from core.exceptions import ChatbotException
from core.responses import handle_exception_response, internal_server_error_response
from core.config import CORS_ORIGINS, APP_NAME, APP_VERSION
from database import get_db, init_db, close_db, DatabaseManager
from services.auth import AuthService
from routers.messages import router as message_router
from routers.users import router as user_router
import models, schemas
from sqlalchemy.orm import Session
from core.exceptions import setup_exception_handlers
from core.middleware import setup_performance_middleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the database tables
init_db()

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="A high-performance chatbot API with caching and optimization"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup performance monitoring middleware
setup_performance_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)

# Error handling
@app.exception_handler(ChatbotException)
async def chatbot_exception_handler(request: Request, exc: ChatbotException):
    """Handle custom ChatbotException instances."""
    return handle_exception_response(exc)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException instances."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"message": exc.detail, "status_code": exc.status_code}},
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return internal_server_error_response("An unexpected error occurred")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/api/v1/health")
async def api_health_check(db: Session = Depends(get_db)):
    """Detailed health check with database connectivity."""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "version": APP_VERSION,
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Authentication route
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    token = AuthService.authenticate_and_create_token(db, username, password)
    return token

# Include routers
app.include_router(message_router, dependencies=[Depends(get_current_user)])
app.include_router(user_router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks."""
    logger.info("Starting up the application...")
    init_db()
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down the application...")
    close_db()
    logger.info("Application shutdown complete")