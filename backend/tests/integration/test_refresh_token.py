"""
Integration tests for refresh token functionality.
"""

import pytest
from fastapi import status
from sqlalchemy.orm import Session


def test_login_returns_refresh_token(client, sample_user):
    """Test that login endpoint returns both access and refresh tokens."""
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check that both tokens are returned
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Tokens should be different
    assert data["access_token"] != data["refresh_token"]


def test_refresh_endpoint_with_valid_token(client, sample_user):
    """Test that refresh endpoint returns new tokens with valid refresh token."""
    # First login to get tokens
    login_response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    
    assert login_response.status_code == status.HTTP_200_OK
    tokens = login_response.json()
    
    # Use refresh token to get new tokens
    refresh_response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    
    assert refresh_response.status_code == status.HTTP_200_OK
    new_tokens = refresh_response.json()
    
    # Check that new tokens are returned
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["token_type"] == "bearer"
    
    # New tokens should be different from old ones
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


def test_refresh_endpoint_with_invalid_token(client):
    """Test that refresh endpoint rejects invalid refresh token."""
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate refresh token"


def test_refresh_endpoint_with_access_token(client, sample_user):
    """Test that refresh endpoint rejects access token as refresh token."""
    # First login to get tokens
    login_response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    
    assert login_response.status_code == status.HTTP_200_OK
    tokens = login_response.json()
    
    # Try to use access token as refresh token
    refresh_response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": tokens["access_token"]},  # Using access token
    )
    
    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate refresh token"


def test_me_endpoint_still_works_with_access_token(client, sample_user):
    """Test that /me endpoint still works with access token (not refresh token)."""
    # Login to get tokens
    login_response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    
    assert login_response.status_code == status.HTTP_200_OK
    tokens = login_response.json()
    
    # Use access token for /me endpoint
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    
    assert me_response.status_code == status.HTTP_200_OK
    assert me_response.json()["username"] == "testuser"
    
    # Refresh token should NOT work for /me endpoint
    me_with_refresh = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    
    assert me_with_refresh.status_code == status.HTTP_401_UNAUTHORIZED