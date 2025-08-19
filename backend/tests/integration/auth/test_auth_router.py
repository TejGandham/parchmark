"""
Integration tests for authentication router (app.routers.auth).
Tests auth endpoints with real FastAPI client and database.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.auth import create_access_token


class TestLoginEndpoint:
    """Test /auth/login endpoint."""

    def test_login_success(self, client: TestClient, sample_user, sample_user_data):
        """Test successful user login."""
        response = client.post("/api/auth/login", json=sample_user_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_invalid_username(self, client: TestClient):
        """Test login with invalid username."""
        login_data = {"username": "nonexistent", "password": "testpass123"}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert data["detail"] == "Invalid username or password"
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_login_invalid_password(self, client: TestClient, sample_user, sample_user_data):
        """Test login with invalid password."""
        login_data = {"username": sample_user_data["username"], "password": "wrongpassword"}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert data["detail"] == "Invalid username or password"

    def test_login_missing_username(self, client: TestClient):
        """Test login with missing username."""
        login_data = {"password": "password123"}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        data = response.json()
        assert "detail" in data
        # Check that validation error mentions username
        assert any("username" in str(error) for error in data["detail"])

    def test_login_missing_password(self, client: TestClient):
        """Test login with missing password."""
        login_data = {"username": "testuser"}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        data = response.json()
        assert "detail" in data
        # Check that validation error mentions password
        assert any("password" in str(error) for error in data["detail"])

    def test_login_empty_username(self, client: TestClient):
        """Test login with empty username."""
        login_data = {"username": "", "password": "password123"}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_empty_password(self, client: TestClient):
        """Test login with empty password."""
        login_data = {"username": "testuser", "password": ""}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_invalid_json(self, client: TestClient):
        """Test login with invalid JSON."""
        response = client.post("/api/auth/login", data="invalid json", headers={"Content-Type": "application/json"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_username_case_sensitive(self, client: TestClient, sample_user, sample_user_data):
        """Test that login is case-sensitive for usernames."""
        login_data = {"username": sample_user_data["username"].upper(), "password": sample_user_data["password"]}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_special_characters(self, client: TestClient, test_db_session):
        """Test login with special characters in credentials."""
        from app.auth.auth import get_password_hash
        from app.models.models import User

        # Create user with special characters
        special_user = User(username="user@domain.com", password_hash=get_password_hash("pass@word123!"))
        test_db_session.add(special_user)
        test_db_session.commit()

        login_data = {"username": "user@domain.com", "password": "pass@word123!"}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data

    @patch("app.routers.auth.authenticate_user")
    def test_login_database_error(self, mock_auth, client: TestClient):
        """Test login when database error occurs."""
        mock_auth.side_effect = Exception("Database connection failed")

        login_data = {"username": "testuser", "password": "password123"}

        with pytest.raises(Exception):
            client.post("/api/auth/login", json=login_data)


class TestLogoutEndpoint:
    """Test /auth/logout endpoint."""

    def test_logout_success(self, client: TestClient, auth_headers):
        """Test successful user logout."""
        response = client.post("/api/auth/logout", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "logged out successfully" in data["message"]

    def test_logout_no_token(self, client: TestClient):
        """Test logout without authentication token."""
        response = client.post("/api/auth/logout")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_logout_invalid_token(self, client: TestClient):
        """Test logout with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert data["detail"] == "Could not validate credentials"

    def test_logout_expired_token(self, client: TestClient, expired_token):
        """Test logout with expired token."""
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_malformed_token(self, client: TestClient):
        """Test logout with malformed token."""
        malformed_tokens = [
            "Bearer not.a.token",
            "Bearer",
            "InvalidFormat token",
            "Bearer a.b.c.d.e",
        ]

        for auth_header in malformed_tokens:
            headers = {"Authorization": auth_header}
            response = client.post("/api/auth/logout", headers=headers)

            assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_logout_wrong_user_token(self, client: TestClient, test_db_session):
        """Test logout with token for non-existent user."""
        # Create token for user that doesn't exist in database
        fake_token = create_access_token(data={"sub": "nonexistent_user"}, expires_delta=timedelta(minutes=30))

        headers = {"Authorization": f"Bearer {fake_token}"}
        response = client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUserInfoEndpoint:
    """Test /auth/me endpoint."""

    def test_get_current_user_success(self, client: TestClient, auth_headers, sample_user):
        """Test successful retrieval of current user info."""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "username" in data
        assert data["username"] == sample_user.username
        # Ensure no sensitive data is exposed
        assert "password" not in data
        assert "password_hash" not in data
        assert "id" not in data

    def test_get_current_user_no_token(self, client: TestClient):
        """Test get current user without authentication token."""
        response = client.get("/api/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test get current user with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_expired_token(self, client: TestClient, expired_token):
        """Test get current user with expired token."""
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_response_format(self, client: TestClient, auth_headers, sample_user):
        """Test that response follows UserResponse schema."""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Verify response structure matches UserResponse schema
        required_fields = {"username"}
        forbidden_fields = {"password", "password_hash", "id", "created_at"}

        assert set(data.keys()) == required_fields
        assert not any(field in data for field in forbidden_fields)


class TestAuthHealthEndpoint:
    """Test /auth/health endpoint."""

    def test_auth_health_check(self, client: TestClient):
        """Test authentication service health check."""
        response = client.get("/api/auth/health")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "status" in data
        assert data["status"] == "Authentication service is healthy"

    def test_auth_health_check_no_auth_required(self, client: TestClient):
        """Test that health check doesn't require authentication."""
        response = client.get("/api/auth/health")

        assert response.status_code == status.HTTP_200_OK
        # Should work without any authentication headers


class TestAuthRouterIntegration:
    """Test integration between auth router endpoints."""

    def test_full_auth_flow(self, client: TestClient, sample_user, sample_user_data):
        """Test complete authentication flow: login -> get user info -> logout."""
        # Step 1: Login
        login_response = client.post("/api/auth/login", json=sample_user_data)
        assert login_response.status_code == status.HTTP_200_OK

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Get user info
        user_response = client.get("/api/auth/me", headers=headers)
        assert user_response.status_code == status.HTTP_200_OK
        assert user_response.json()["username"] == sample_user_data["username"]

        # Step 3: Logout
        logout_response = client.post("/api/auth/logout", headers=headers)
        assert logout_response.status_code == status.HTTP_200_OK

        # Step 4: Verify token is still valid (logout is client-side)
        user_response_after_logout = client.get("/api/auth/me", headers=headers)
        assert user_response_after_logout.status_code == status.HTTP_200_OK

    def test_token_reuse_across_endpoints(self, client: TestClient, auth_headers):
        """Test that same token works across different auth endpoints."""
        # Test /auth/me
        me_response = client.get("/api/auth/me", headers=auth_headers)
        assert me_response.status_code == status.HTTP_200_OK

        # Test /auth/logout
        logout_response = client.post("/api/auth/logout", headers=auth_headers)
        assert logout_response.status_code == status.HTTP_200_OK

        # Token should still be valid after logout (JWT is stateless)
        me_response_again = client.get("/api/auth/me", headers=auth_headers)
        assert me_response_again.status_code == status.HTTP_200_OK

    def test_multiple_login_sessions(self, client: TestClient, sample_user, sample_user_data):
        """Test multiple concurrent login sessions."""
        # Create multiple tokens
        tokens = []
        for _ in range(3):
            response = client.post("/api/auth/login", json=sample_user_data)
            assert response.status_code == status.HTTP_200_OK
            tokens.append(response.json()["access_token"])

        # All tokens should be valid
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/auth/me", headers=headers)
            assert response.status_code == status.HTTP_200_OK

    def test_auth_error_response_format(self, client: TestClient):
        """Test that auth errors follow consistent response format."""
        # Test various auth error scenarios
        error_scenarios = [
            ("POST", "/api/auth/login", {"username": "wrong", "password": "wrong"}),
            ("GET", "/api/auth/me", None),
            ("POST", "/api/auth/logout", None),
        ]

        for method, endpoint, json_data in error_scenarios:
            if method == "POST":
                response = client.post(endpoint, json=json_data) if json_data else client.post(endpoint)
            else:
                response = client.get(endpoint)

            if response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]:
                data = response.json()
                assert "detail" in data
                assert isinstance(data["detail"], str)


class TestAuthRouterSecurity:
    """Test security aspects of auth router."""

    def test_login_rate_limiting_simulation(self, client: TestClient):
        """Test multiple failed login attempts (simulating rate limiting)."""
        login_data = {"username": "nonexistent", "password": "wrongpassword"}

        # Simulate multiple failed attempts
        for _ in range(5):
            response = client.post("/api/auth/login", json=login_data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            # Each request should return same error (no information leakage)
            assert response.json()["detail"] == "Invalid username or password"

    def test_password_not_in_responses(self, client: TestClient, sample_user, sample_user_data):
        """Test that passwords are never included in responses."""
        # Login
        login_response = client.post("/api/auth/login", json=sample_user_data)
        login_data = login_response.json()

        # Get user info
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_response = client.get("/api/auth/me", headers=headers)
        user_data = user_response.json()

        # Logout
        logout_response = client.post("/api/auth/logout", headers=headers)
        logout_data = logout_response.json()

        # Check no password data in any response
        all_responses = [login_data, user_data, logout_data]
        for response_data in all_responses:
            assert "password" not in str(response_data).lower()
            assert "pwd" not in str(response_data).lower()
            assert "hash" not in str(response_data).lower()

    def test_token_format_security(self, client: TestClient, sample_user, sample_user_data):
        """Test that tokens follow proper JWT format."""
        response = client.post("/api/auth/login", json=sample_user_data)
        token = response.json()["access_token"]

        # JWT should have 3 parts separated by dots
        parts = token.split(".")
        assert len(parts) == 3

        # Each part should be base64-like (no obvious secrets)
        for part in parts:
            assert len(part) > 0
            # Should not contain obvious passwords or usernames
            assert sample_user_data["password"] not in part
            assert sample_user_data["username"] not in part
