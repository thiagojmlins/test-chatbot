import os
import pytest
from core.config import (
    TESTING, SECRET_KEY, API_KEY, SQLALCHEMY_DATABASE_URL,
    CORS_ORIGINS, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)

def test_testing_environment():
    """Test that TESTING environment variable is properly set."""
    assert TESTING == True

def test_required_environment_variables():
    """Test that required environment variables are set in CI."""
    assert SECRET_KEY is not None
    assert API_KEY is not None
    assert SECRET_KEY == "test-secret-key-for-ci"
    assert API_KEY == "test-api-key-for-ci"

def test_database_url_in_testing():
    """Test that database URL is set to SQLite in testing mode."""
    assert SQLALCHEMY_DATABASE_URL == "sqlite:///./test_chatbot.db"

def test_cors_origins():
    """Test that CORS origins are properly configured."""
    assert isinstance(CORS_ORIGINS, list)
    assert len(CORS_ORIGINS) > 0

def test_auth_configuration():
    """Test that authentication configuration is properly set."""
    assert ALGORITHM == "HS256"
    assert ACCESS_TOKEN_EXPIRE_MINUTES == 30

def test_environment_variables_are_strings():
    """Test that environment variables are properly typed."""
    assert isinstance(SECRET_KEY, str)
    assert isinstance(API_KEY, str)
    assert isinstance(ALGORITHM, str)
    assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int) 