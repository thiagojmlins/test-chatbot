import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from fastapi.testclient import TestClient
from database import Base, get_db
from models import User  # Make sure User is imported
from app import app
from auth import get_password_hash
from unittest.mock import patch, MagicMock

SQLALCHEMY_DATABASE_URL = "sqlite:///./chatbot.db"

# Create the engine with shared connection across threads
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session local for testing
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure the same connection is used for all database sessions
@event.listens_for(Engine, "connect")
def do_connect(dbapi_connection, connection_record):
    dbapi_connection.isolation_level = None

# Dependency override for FastAPI
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Fixture to set up and tear down the test database
@pytest.fixture(scope="function")
def setup_database():
    # Create the tables before each test
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the tables after each test
    Base.metadata.drop_all(bind=engine)

# Utility function to create a test user
def create_test_user(db, username="testuser", password="testpassword"):
    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def test_create_user(setup_database):
    response = client.post(
        "/users/",
        json={"username": "john", "password": "secretpassword"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "john"

def test_login_for_access_token(setup_database):
    # First, create a user
    with TestingSessionLocal() as db:
        create_test_user(db, "john", "secretpassword")

    # Login to get the token
    response = client.post(
        "/token",
        data={"username": "john", "password": "secretpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_protected_route_with_token(setup_database):
    # First, create a user
    with TestingSessionLocal() as db:
        create_test_user(db, "john", "secretpassword")

    # Login to get the token
    login_response = client.post(
        "/token",
        data={"username": "john", "password": "secretpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    access_token = login_response.json()["access_token"]

    # Access the protected route using the token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/history", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_protected_route_without_token(setup_database):
    response = client.get("/history")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@patch('chatbot.client.chat.completions.create')
def test_send_message_with_token(mock_create, setup_database):
    # Mock the chatbot API response
    mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="This is a mock response"))])

    # First, create a user
    with TestingSessionLocal() as db:
        create_test_user(db, "john", "secretpassword")

    # Login to get the token
    login_response = client.post(
        "/token",
        data={"username": "john", "password": "secretpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    access_token = login_response.json()["access_token"]

    # Send a message using the token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/send_message", json={"content": "Hello, chatbot!"}, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["message"]["content"] == "Hello, chatbot!"
    assert data["reply"]["content"] == "This is a mock response"

@patch('chatbot.client.chat.completions.create')
def test_edit_message_with_token(mock_create, setup_database):
    # Mock the chatbot API response
    mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="Updated response"))])

    # First, create a user
    with TestingSessionLocal() as db:
        create_test_user(db, "john", "secretpassword")

    # Login to get the token
    login_response = client.post(
        "/token",
        data={"username": "john", "password": "secretpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    access_token = login_response.json()["access_token"]

    # Send a message using the token
    headers = {"Authorization": f"Bearer {access_token}"}
    send_response = client.post("/send_message", json={"content": "Hello, chatbot!"}, headers=headers)
    message_id = send_response.json()["message"]["id"]

    # Edit the message using the token
    edit_response = client.put(f"/edit_message/{message_id}", json={"content": "Updated content"}, headers=headers)

    assert edit_response.status_code == 200
    data = edit_response.json()
    assert data["message"]["content"] == "Updated content"
    assert data["reply"]["content"] == "Updated response"

def test_delete_message_with_token(setup_database):
    # First, create a user
    with TestingSessionLocal() as db:
        create_test_user(db, "john", "secretpassword")

    # Login to get the token
    login_response = client.post(
        "/token",
        data={"username": "john", "password": "secretpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    access_token = login_response.json()["access_token"]

    # Send a message using the token
    headers = {"Authorization": f"Bearer {access_token}"}
    send_response = client.post("/send_message", json={"content": "Message to delete"}, headers=headers)
    message_id = send_response.json()["message"]["id"]

    # Delete the message using the token
    delete_response = client.delete(f"/delete_message/{message_id}", headers=headers)

    assert delete_response.status_code == 200
    assert delete_response.json()["content"] == "Message to delete"
