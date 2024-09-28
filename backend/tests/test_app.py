import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from fastapi.testclient import TestClient
from database import Base, get_db
from models import User, Message
from app import app
from auth import get_password_hash
from services import ChatService
from unittest.mock import patch, MagicMock, ANY

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_chatbot.db"

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

@pytest.fixture
def authenticated_client(setup_database):
    # Create a user
    with TestingSessionLocal() as db:
        user = create_test_user(db, "john", "secretpassword")

    # Login to get the token
    response = client.post(
        "/token",
        data={"username": "john", "password": "secretpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    access_token = response.json()["access_token"]

    # Create a new TestClient with the authentication header
    authenticated_client = TestClient(app)
    authenticated_client.headers = {"Authorization": f"Bearer {access_token}"}

    return {"client": authenticated_client, "user_id": user.id}

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

def test_login_for_access_token(setup_database, authenticated_client):
    response = authenticated_client["client"].post(
        "/token",
        data={"username": "john", "password": "secretpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_protected_route_with_token(authenticated_client):
    response = authenticated_client["client"].get("/users/me")
    assert response.status_code == 200
    assert "username" in response.json()

def test_protected_route_without_token(setup_database):
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.json() == {"message": "Not authenticated"}

@patch.object(ChatService, 'create_message')
def test_send_message_with_token(mock_create_message, authenticated_client):
    mock_create_message.return_value = (
        Message(id=1, user_id=authenticated_client["user_id"], content="Hello, chatbot!", is_from_user=True, reply_to=None),
        Message(id=2, user_id=authenticated_client["user_id"], content="This is a mock response", is_from_user=False, reply_to=1)
    )

    response = authenticated_client["client"].post("/messages/", json={"content": "Hello, chatbot!"})

    assert response.status_code == 200
    data = response.json()
    assert data["message"]["content"] == "Hello, chatbot!"
    assert data["reply"]["content"] == "This is a mock response"

    mock_create_message.assert_called_once_with(ANY, authenticated_client["user_id"], "Hello, chatbot!")

@patch.object(ChatService, 'edit_message_and_update_reply')
def test_edit_message_with_token(mock_edit_message, authenticated_client):
    mock_edit_message.return_value = (
        Message(id=1, user_id=authenticated_client["user_id"], content="Updated content", is_from_user=True, reply_to=None),
        Message(id=2, user_id=authenticated_client["user_id"], content="Updated response", is_from_user=False, reply_to=1)
    )

    # Create a message first
    with TestingSessionLocal() as db:
        message = Message(user_id=authenticated_client["user_id"], content="Original content", is_from_user=True)
        db.add(message)
        db.commit()
        db.refresh(message)

    response = authenticated_client["client"].put(
        f"/messages/{message.id}",
        json={"content": "Updated content"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"]["content"] == "Updated content"
    assert data["reply"]["content"] == "Updated response"

    mock_edit_message.assert_called_once_with(ANY, authenticated_client["user_id"], message.id, "Updated content")

@patch.object(ChatService, 'delete_message')
def test_delete_message_with_token(mock_delete_message, authenticated_client):
    mock_delete_message.return_value = Message(id=1, user_id=authenticated_client["user_id"], content="Message to delete", is_from_user=True)

    # Create a message first
    with TestingSessionLocal() as db:
        message = Message(user_id=authenticated_client["user_id"], content="Message to delete", is_from_user=True)
        db.add(message)
        db.commit()
        db.refresh(message)

    response = authenticated_client["client"].delete(f"/messages/{message.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "user_id": authenticated_client["user_id"],
        "content": "Message to delete",
        "is_from_user": True,
        "reply_to": None
    }

    mock_delete_message.assert_called_once_with(ANY, authenticated_client["user_id"], message.id)





