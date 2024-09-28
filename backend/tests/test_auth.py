import pytest
from tests.test_utils import create_test_user
from tests.conftest import TestingSessionLocal

def test_create_user(client):
    response = client.post(
        "/users/",
        json={"username": "john", "password": "secretpassword"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "john"

@pytest.mark.parametrize("username,password,status_code", [
    ("john", "secretpassword", 422),
    ("", "password", 422),  # Invalid username
    ("john", "", 422),      # Invalid password
])
def test_create_user_edge_cases(client, username, password, status_code):
    response = client.post(
        "/users/",
        json={"username": username, "password": password},
    )
    assert response.status_code == status_code

def test_login_for_access_token(client):
    # First, create a user
    with TestingSessionLocal() as db:
        create_test_user(db, "john", "secretpassword")

    # Login to get the token
    response = client.post(
        "/token",
        data={"username": "john", "password": "secretpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.parametrize("username,password,status_code", [
    ("john", "wrongpassword", 401),
    ("unknown", "secretpassword", 401),
    ("", "secretpassword", 422),
    ("john", "", 422),
])
def test_login_edge_cases(client, username, password, status_code):
    # First, create a user
    with TestingSessionLocal() as db:
        create_test_user(db, "john", "secretpassword")

    # Attempt to login with various credentials
    response = client.post(
        "/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status_code
