"""
Integration tests for refresh token functionality.
"""

import jwt
from fastapi import status

from app.auth.auth import ALGORITHM, SECRET_KEY


def test_login_returns_refresh_token(client, sample_user, sample_user_data):
    """Test that login endpoint returns both access and refresh tokens."""
    response = client.post(
        "/api/auth/login",
        json={"username": sample_user_data["username"], "password": sample_user_data["password"]},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Check that both tokens are returned
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Tokens should be different
    assert data["access_token"] != data["refresh_token"]


def test_refresh_endpoint_with_valid_token(client, sample_user, sample_user_data):
    """Test that refresh endpoint returns new tokens with valid refresh token."""
    # First login to get tokens
    login_response = client.post(
        "/api/auth/login",
        json={"username": sample_user_data["username"], "password": sample_user_data["password"]},
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

    # Verify tokens are valid and contain correct data
    access_payload = jwt.decode(new_tokens["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    refresh_payload = jwt.decode(new_tokens["refresh_token"], SECRET_KEY, algorithms=[ALGORITHM])

    # Verify token contents
    assert access_payload["sub"] == sample_user_data["username"]
    assert access_payload["type"] == "access"
    assert refresh_payload["sub"] == sample_user_data["username"]
    assert refresh_payload["type"] == "refresh"

    # Verify tokens have expiration times
    assert "exp" in access_payload
    assert "exp" in refresh_payload
    assert refresh_payload["exp"] > access_payload["exp"]  # Refresh token expires later


def test_refresh_endpoint_with_invalid_token(client):
    """Test that refresh endpoint rejects invalid refresh token."""
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate refresh token"


def test_refresh_endpoint_with_access_token(client, sample_user, sample_user_data):
    """Test that refresh endpoint rejects access token as refresh token."""
    # First login to get tokens
    login_response = client.post(
        "/api/auth/login",
        json={"username": sample_user_data["username"], "password": sample_user_data["password"]},
    )

    assert login_response.status_code == status.HTTP_200_OK
    tokens = login_response.json()

    # Try to use access token as refresh token
    refresh_response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": tokens["access_token"]},  # Using access token
    )

    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert refresh_response.json()["detail"] == "Could not validate refresh token"


def test_me_endpoint_still_works_with_access_token(client, sample_user, sample_user_data):
    """Test that /me endpoint still works with access token (not refresh token)."""
    # Login to get tokens
    login_response = client.post(
        "/api/auth/login",
        json={"username": sample_user_data["username"], "password": sample_user_data["password"]},
    )

    assert login_response.status_code == status.HTTP_200_OK
    tokens = login_response.json()

    # Use access token for /me endpoint
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert me_response.status_code == status.HTTP_200_OK
    assert me_response.json()["username"] == sample_user_data["username"]

    # Refresh token should NOT work for /me endpoint
    me_with_refresh = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )

    assert me_with_refresh.status_code == status.HTTP_401_UNAUTHORIZED
