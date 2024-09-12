import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from app import app, get_db

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a test-specific SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_chatbot.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the `get_db` dependency to use the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Use the TestClient for making requests to the API
client = TestClient(app)

# Ensure the test database schema is created before running the tests
@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)  # Create the test tables
    yield
    Base.metadata.drop_all(bind=engine)  # Drop the tables after tests

def test_send_message(setup_database):
    # Test sending a message
    response = client.post("/send_message", json={"content": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"]["content"] == "Hello"
    assert data["reply"]["content"] == "Reply to 'Hello'"

def test_get_history(setup_database):
    # Test retrieving the chat history
    response = client.get("/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 2  # There should be at least the message and its reply
    assert history[0]["content"] == "Hello"

def test_edit_message(setup_database):
    # Test editing a message and receiving an updated reply
    response = client.put("/edit_message/1", json={"content": "Updated message"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"]["content"] == "Updated message"
    assert data["reply"]["content"] == "Reply to 'Updated message'"

def test_delete_message(setup_database):
    # Test deleting a message
    response = client.delete("/delete_message/1")
    assert response.status_code == 200
    deleted_message = response.json()
    assert deleted_message["id"] == 1
    assert deleted_message["content"] == "Updated message"
