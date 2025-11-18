import pytest
from fastapi import status
from app.models import UserPlan

def test_register_user(client, test_user_data):
    """Test user registration"""
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_register_duplicate_email(client, test_user_data):
    """Test registration with duplicate email"""
    # First registration
    client.post("/auth/register", json=test_user_data)
    
    # Second registration with same email
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in response.json()["detail"]

def test_login_user(client, test_user_data):
    """Test user login"""
    # Register user first
    client.post("/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_invalid_credentials(client, test_user_data):
    """Test login with invalid credentials"""
    # Register user first
    client.post("/auth/register", json=test_user_data)
    
    # Login with wrong password
    login_data = {
        "email": test_user_data["email"],
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in response.json()["detail"]

def test_get_current_user(client, test_user, auth_headers):
    """Test getting current user info"""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["name"] == "Test User"
    assert data["plan"] == UserPlan.FREE.value
    assert data["is_verified"] is False

def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication"""
    response = client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_refresh_token(client, test_user):
    """Test token refresh"""
    refresh_data = {
        "refresh_token": test_user["refresh_token"]
    }
    headers = {"Authorization": f"Bearer {test_user['refresh_token']}"}
    response = client.post("/auth/refresh", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_email_verification_flow(client, test_user_data):
    """Test email verification flow"""
    # Register user
    register_response = client.post("/auth/register", json=test_user_data)
    assert register_response.status_code == 200
    
    # Check user is not verified
    login_response = client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    
    me_response = client.get("/auth/me", headers=auth_headers)
    assert me_response.json()["is_verified"] is False
    
    # TODO: In a real implementation, we would get the verification token
    # from the email service. For now, we'll simulate it.
    
    # Verify email (this will fail without a real token)
    verify_data = {"token": "fake_token"}
    verify_response = client.post("/auth/verify-email", json=verify_data)
    assert verify_response.status_code == status.HTTP_404_NOT_FOUND

def test_password_reset_flow(client, test_user_data):
    """Test password reset flow"""
    # Register user
    client.post("/auth/register", json=test_user_data)
    
    # Request password reset
    reset_request_data = {"email": test_user_data["email"]}
    response = client.post("/auth/request-reset", json=reset_request_data)
    assert response.status_code == 200
    assert "If email exists, reset link sent" in response.json()["message"]
    
    # Request reset for non-existent email (should not reveal this)
    reset_request_data = {"email": "nonexistent@example.com"}
    response = client.post("/auth/request-reset", json=reset_request_data)
    assert response.status_code == 200
    assert "If email exists, reset link sent" in response.json()["message"]
    
    # Try to reset with invalid token
    reset_data = {
        "token": "invalid_token",
        "new_password": "newpassword123"
    }
    response = client.post("/auth/reset-password", json=reset_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_protected_routes_without_auth(client):
    """Test accessing protected routes without authentication"""
    response = client.get("/api/protected")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_pro_feature_without_auth(client):
    """Test accessing pro feature without authentication"""
    response = client.get("/api/pro-feature")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED