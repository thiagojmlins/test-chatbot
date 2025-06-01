import os
import psycopg
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default to PostgreSQL for production
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres:postgres@db:5432/chatbot"

# Allow override for testing
if os.getenv("TESTING"):
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test_chatbot.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()