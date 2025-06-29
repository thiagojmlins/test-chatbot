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

# Initialize the database tables
init_db()

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="A modern chatbot API with improved database management"
)

logger = getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Health check endpoint to verify API and database status."""
    db_healthy = DatabaseManager.health_check()
    connection_info = DatabaseManager.get_connection_info()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": {
            "status": "connected" if db_healthy else "disconnected",
            "connection_pool": connection_info
        },
        "api": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "status": "running"
        }
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
    """Initialize application on startup."""
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info("Database connection pool initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application on shutdown."""
    logger.info("Shutting down application...")
    close_db()
    logger.info("Database connections closed")