import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
TESTING = os.getenv("TESTING", "0") == "1"

# Authentication
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Database Configuration
DATABASE_HOST = os.getenv("DATABASE_HOST", "db")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "chatbot")
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")

# Database URLs
if TESTING:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test_chatbot.db"
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# CORS Configuration
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Add additional origins from environment variable
CORS_ORIGINS_EXTRA = os.getenv("CORS_ORIGINS_EXTRA", "")
if CORS_ORIGINS_EXTRA:
    CORS_ORIGINS.extend(CORS_ORIGINS_EXTRA.split(","))

# API Configuration
API_KEY = os.getenv("API_KEY")
API_MODEL = os.getenv("API_MODEL", "gpt-3.5-turbo")

# Application Settings
APP_NAME = os.getenv("APP_NAME", "Chatbot API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Validation
def validate_config():
    """Validate that required configuration values are set."""
    required_vars = {
        "SECRET_KEY": SECRET_KEY,
        "API_KEY": API_KEY,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Validate configuration on import (except during testing)
if not TESTING:
    validate_config() 