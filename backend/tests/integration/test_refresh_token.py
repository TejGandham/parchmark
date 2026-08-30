"""
Integration tests for refresh token functionality.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

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


def test_refresh_endpoint_with_empty_subject_token(client):
    """Reject a validly-signed refresh token that carries an empty subject.

    ``verify_token`` only rejects a *missing* (None) subject, so an empty-string
    ``sub`` passes signature and type validation and flows through to
    ``refresh_access_token``. There the ``if not token_data.username`` guard
    (``app/services/auth_service.py`` line 74) fires and raises 401. This is the
    only input shape that reaches that branch.
    """
    empty_subject_token = jwt.encode(
        {
            "sub": "",
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(days=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": empty_subject_token},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate refresh token"


def test_refresh_endpoint_with_unknown_user_token(client):
    """Reject a validly-signed refresh token whose subject names no user.

    The subject is truthy, so the ``if not token_data.username`` guard passes,
    but ``get_user_by_username`` returns ``None`` for a subject with no matching
    row. ``refresh_access_token`` then reaches the ``if not user`` guard
    (``app/services/auth_service.py`` line 79) and raises 401. The user is never
    created; the subject deliberately resolves to no row.
    """
    unknown_user_token = jwt.encode(
        {
            "sub": f"ghost-user-{uuid4().hex}",
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(days=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": unknown_user_token},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate refresh token"


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
