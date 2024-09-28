import pytest
from unittest.mock import patch
from tests.test_utils import create_test_user

@pytest.fixture
def auth_headers_user1(client, db_session):
    create_test_user(db_session, "user1", "password1")
    response = client.post(
        "/token",
        data={"username": "user1", "password": "password1"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers

@pytest.fixture
def auth_headers_user2(client, db_session):
    create_test_user(db_session, "user2", "password2")
    response = client.post(
        "/token",
        data={"username": "user2", "password": "password2"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers

@patch('chatbot.generate_reply')
@pytest.mark.parametrize("content,status_code", [
    ("Hello, chatbot!", 200),
    ("", 422),  # Empty content
    ("a" * 1001, 422),  # Content too long if you have a max length validation
])
def test_send_message_edge_cases(mock_generate_reply, client, auth_headers_user1, content, status_code):
    mock_generate_reply.return_value = "Mock reply"
    response = client.post(
        "/send_message",
        json={"content": content},
        headers=auth_headers_user1,
    )
    assert response.status_code == status_code

def test_edit_nonexistent_message(client, auth_headers_user1):
    response = client.put(
        "/edit_message/9999",
        json={"content": "Updated content"},
        headers=auth_headers_user1,
    )
    assert response.status_code == 404

def test_delete_nonexistent_message(client, auth_headers_user1):
    response = client.delete(
        "/delete_message/9999",
        headers=auth_headers_user1,
    )
    assert response.status_code == 404

def test_user_cannot_edit_another_users_message(client, auth_headers_user1, auth_headers_user2):
    # User1 sends a message
    with patch('chatbot.generate_reply') as mock_generate_reply:
        mock_generate_reply.return_value = "Mock reply"
        send_response = client.post(
            "/send_message",
            json={"content": "User1's message"},
            headers=auth_headers_user1,
        )
    message_id = send_response.json()["message"]["id"]

    # User2 attempts to edit User1's message
    edit_response = client.put(
        f"/edit_message/{message_id}",
        json={"content": "User2's malicious edit"},
        headers=auth_headers_user2,
    )
    assert edit_response.status_code == 404 or edit_response.status_code == 403

def test_user_cannot_delete_another_users_message(client, auth_headers_user1, auth_headers_user2):
    # User1 sends a message
    with patch('chatbot.generate_reply') as mock_generate_reply:
        mock_generate_reply.return_value = "Mock reply"
        send_response = client.post(
            "/send_message",
            json={"content": "User1's message"},
            headers=auth_headers_user1,
        )
    message_id = send_response.json()["message"]["id"]

    # User2 attempts to delete User1's message
    delete_response = client.delete(
        f"/delete_message/{message_id}",
        headers=auth_headers_user2,
    )
    assert delete_response.status_code == 404 or delete_response.status_code == 403

def test_get_history_when_no_messages(client, auth_headers_user1):
    response = client.get("/history", headers=auth_headers_user1)
    assert response.status_code == 200
    data = response.json()
    assert data == []
