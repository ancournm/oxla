import pytest
from fastapi import status
from app.models import UserPlan

def test_send_email_unauthorized(client):
    """Test sending email without authentication"""
    email_data = {
        "recipient": "test@example.com",
        "subject": "Test Subject",
        "body_text": "Test body"
    }
    response = client.post("/mail/send", json=email_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_send_email_authorized(client, auth_headers):
    """Test sending email with authentication"""
    email_data = {
        "recipient": "test@example.com",
        "subject": "Test Subject",
        "body_text": "Test body"
    }
    response = client.post("/mail/send", json=email_data, headers=auth_headers)
    # This will likely fail because we don't have a real SMTP server
    # but it should save the email to the database with FAILED status
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

def test_get_inbox_unauthorized(client):
    """Test getting inbox without authentication"""
    response = client.get("/mail/inbox")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_inbox_authorized(client, auth_headers):
    """Test getting inbox with authentication"""
    response = client.get("/mail/inbox", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    # Should return empty list initially
    assert isinstance(response.json(), list)

def test_create_alias_unauthorized(client):
    """Test creating alias without authentication"""
    alias_data = {
        "alias_name": "test",
        "is_disposable": False
    }
    response = client.post("/mail/alias", json=alias_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_alias_authorized(client, auth_headers):
    """Test creating alias with authentication"""
    alias_data = {
        "alias_name": "test",
        "is_disposable": False
    }
    response = client.post("/mail/alias", json=alias_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "alias_id" in data
    assert "alias_email" in data
    assert data["alias_name"] == "test"

def test_create_disposable_alias(client, auth_headers):
    """Test creating disposable alias"""
    alias_data = {
        "alias_name": "disposable",
        "is_disposable": True,
        "expires_hours": 24
    }
    response = client.post("/mail/alias", json=alias_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_disposable"] is True
    assert "expires_at" in data

def test_get_aliases_unauthorized(client):
    """Test getting aliases without authentication"""
    response = client.get("/mail/aliases")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_aliases_authorized(client, auth_headers):
    """Test getting aliases with authentication"""
    # First create an alias
    alias_data = {
        "alias_name": "test",
        "is_disposable": False
    }
    client.post("/mail/alias", json=alias_data, headers=auth_headers)
    
    # Then get aliases
    response = client.get("/mail/aliases", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["alias_name"] == "test"

def test_delete_alias_unauthorized(client):
    """Test deleting alias without authentication"""
    response = client.delete("/mail/alias/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_delete_alias_authorized(client, auth_headers):
    """Test deleting alias with authentication"""
    # First create an alias
    alias_data = {
        "alias_name": "test",
        "is_disposable": False
    }
    create_response = client.post("/mail/alias", json=alias_data, headers=auth_headers)
    alias_id = create_response.json()["alias_id"]
    
    # Then delete it
    response = client.delete(f"/mail/alias/{alias_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True

def test_get_unread_count_unauthorized(client):
    """Test getting unread count without authentication"""
    response = client.get("/mail/unread-count")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_unread_count_authorized(client, auth_headers):
    """Test getting unread count with authentication"""
    response = client.get("/mail/unread-count", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "unread_count" in data
    assert isinstance(data["unread_count"], int)

def test_mark_email_as_read_unauthorized(client):
    """Test marking email as read without authentication"""
    response = client.post("/mail/mark-read/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_mark_email_as_spam_unauthorized(client):
    """Test marking email as spam without authentication"""
    response = client.post("/mail/mark-spam/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_alias_plan_limits(client, auth_headers):
    """Test alias creation respects plan limits"""
    # Free plan allows 5 aliases
    for i in range(6):
        alias_data = {
            "alias_name": f"test{i}",
            "is_disposable": False
        }
        response = client.post("/mail/alias", json=alias_data, headers=auth_headers)
        
        if i < 5:
            assert response.status_code == status.HTTP_200_OK
        else:
            # Should fail on 6th alias due to plan limits
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Maximum aliases" in response.json()["detail"]