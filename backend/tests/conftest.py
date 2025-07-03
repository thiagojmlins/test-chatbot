import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from database import Base, get_db
import os

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test_performance.db"

# Create the engine with shared connection across threads
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session local for testing
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure the same connection is used for all database sessions
@event.listens_for(Engine, "connect")
def do_connect(dbapi_connection, connection_record):
    dbapi_connection.isolation_level = None

@pytest.fixture(scope="function")
def db() -> Session:
    """Provide a database session for tests."""
    # Create the tables before each test
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop the tables after each test
        Base.metadata.drop_all(bind=engine)
        # Clean up test database file
        if os.path.exists("./test_performance.db"):
            os.remove("./test_performance.db")

@pytest.fixture(scope="function")
def setup_database():
    """Set up and tear down the test database."""
    # Create the tables before each test
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the tables after each test
    Base.metadata.drop_all(bind=engine)
    # Clean up test database file
    if os.path.exists("./test_performance.db"):
        os.remove("./test_performance.db") 