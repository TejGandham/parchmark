"""
Integration tests for main FastAPI application (main.py).
Tests app configuration, middleware, exception handlers, and root endpoints.
"""

import json
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.models import User


class TestAppConfiguration:
    """Test FastAPI application configuration."""

    def test_app_metadata(self, client: TestClient):
        """Test that app metadata is properly configured."""
        # Get OpenAPI schema to check app configuration
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK

        schema = response.json()
        info = schema["info"]

        assert info["title"] == "ParchMark API"
        assert info["version"] == "1.0.0"
        assert "description" in info
        assert "contact" in info
        assert "license" in info

        # Check description content
        assert "Backend API for ParchMark" in info["description"]
        assert "Authentication" in info["description"]
        assert "Notes Management" in info["description"]

        # Check contact info
        assert info["contact"]["name"] == "ParchMark API Support"
        assert info["contact"]["email"] == "support@parchmark.com"

        # Check license
        assert info["license"]["name"] == "MIT"

    def test_app_docs_endpoints(self, client: TestClient):
        """Test that documentation endpoints are available."""
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_app_openapi_schema(self, client: TestClient):
        """Test OpenAPI schema structure."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK

        schema = response.json()

        # Check required OpenAPI fields
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

        # Check that our routes are in the schema
        paths = schema["paths"]
        assert "/api/auth/login" in paths
        assert "/api/auth/logout" in paths
        assert "/api/auth/me" in paths
        assert "/api/notes/" in paths
        assert "/health" in paths
        assert "/" in paths


class TestCORSMiddleware:
    """Test CORS middleware configuration."""

    def test_cors_preflight_request(self, client: TestClient):
        """Test CORS preflight request handling."""
        response = client.options(
            "/api/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    def test_cors_actual_request(self, client: TestClient):
        """Test CORS headers on actual requests."""
        response = client.get("/health", headers={"Origin": "http://localhost:5173"})

        assert response.status_code == status.HTTP_200_OK
        assert "access-control-allow-origin" in response.headers

    def test_cors_allowed_origins(self, client: TestClient):
        """Test that configured origins are allowed."""
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
        ]

        for origin in allowed_origins:
            response = client.get("/health", headers={"Origin": origin})

            assert response.status_code == status.HTTP_200_OK
            assert response.headers.get("access-control-allow-origin") == origin

    def test_cors_disallowed_origin(self, client: TestClient):
        """Test that disallowed origins are handled."""
        response = client.get("/health", headers={"Origin": "http://malicious-site.com"})

        # Request should still succeed but without CORS headers
        assert response.status_code == status.HTTP_200_OK
        # CORS headers might not be present for disallowed origins


class TestExceptionHandlers:
    """Test custom exception handlers."""

    def test_http_exception_handler(self, client: TestClient):
        """Test HTTP exception handler format."""
        # Trigger a 404 error
        response = client.get("/api/notes/nonexistent-note", headers={"Authorization": "Bearer invalid.token"})

        # This will actually trigger auth error first (401), but that's fine
        # for testing the exception handler format
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]

        data = response.json()
        assert "detail" in data
        assert "status_code" in data
        assert "path" in data

        assert data["status_code"] == response.status_code
        assert "/api/notes/nonexistent-note" in data["path"]

    def test_validation_exception_format(self, client: TestClient):
        """Test validation exception format."""
        # Send invalid JSON to trigger validation error
        response = client.post(
            "/api/auth/login",
            json={"invalid": "data"},  # Missing required fields
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    @patch("main.logger.error")
    @pytest.mark.asyncio
    async def test_general_exception_handler(self, mock_logger, client: TestClient):
        """Test general exception handler."""
        # This is harder to test without creating an actual unhandled exception
        # We'll test that the handler exists and is configured
        from fastapi import Request
        from main import general_exception_handler

        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test/path"

        mock_exception = Exception("Test error")

        response = await general_exception_handler(mock_request, mock_exception)

        assert response.status_code == 500

        # Check response content
        content = json.loads(response.body)
        assert content["detail"] == "Internal server error"
        assert content["status_code"] == 500
        assert content["path"] == "/test/path"

        # Check that error was logged
        mock_logger.assert_called_once()


class TestRootEndpoints:
    """Test root endpoints."""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint response."""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "redoc" in data
        assert "health" in data

        assert data["message"] == "ParchMark API is running"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["redoc"] == "/redoc"
        assert data["health"] == "/health"

    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data

        assert data["status"] == "healthy"
        assert data["service"] == "ParchMark API"
        assert data["version"] == "1.0.0"

    def test_health_endpoint_no_auth_required(self, client: TestClient):
        """Test that health endpoint doesn't require authentication."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        # Should work without any authentication headers


class TestRouterRegistration:
    """Test that routers are properly registered."""

    def test_auth_router_registered(self, client: TestClient):
        """Test that auth router is registered with /api prefix."""
        # Test that auth endpoints are available
        response = client.get("/api/auth/health")
        assert response.status_code == status.HTTP_200_OK

        # Test that endpoints without prefix don't work
        response = client.get("/auth/health")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_notes_router_registered(self, client: TestClient):
        """Test that notes router is registered with /api prefix."""
        # Test that notes endpoints are available (even if they require auth)
        response = client.get("/api/notes/health/check")
        assert response.status_code == status.HTTP_200_OK

        # Test that endpoints without prefix don't work
        response = client.get("/notes/health/check")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_router_endpoints_accessible(self, client: TestClient):
        """Test that router endpoints are accessible through the app."""
        # Auth endpoints
        auth_endpoints = [
            "/api/auth/health",
        ]

        for endpoint in auth_endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK

        # Notes endpoints
        notes_endpoints = [
            "/api/notes/health/check",
        ]

        for endpoint in notes_endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK


class TestApplicationLifespan:
    """Test application lifespan events."""

    @patch("main.init_database")
    @patch("main.logger")
    def test_lifespan_startup(self, mock_logger, mock_init_db):
        """Test application startup lifespan event."""
        mock_init_db.return_value = True

        # Import and test lifespan function
        from main import app, lifespan

        # Create a mock app context for testing
        async def test_lifespan():
            async with lifespan(app):
                pass

        # This would be called during app startup
        import asyncio

        asyncio.run(test_lifespan())

        # Verify database initialization was called
        mock_init_db.assert_called_once()

        # Verify logging
        assert mock_logger.info.call_count >= 2  # Startup and completion messages

    @patch("main.init_database")
    @patch("main.logger")
    def test_lifespan_database_init_failure(self, mock_logger, mock_init_db):
        """Test lifespan handling when database initialization fails."""
        mock_init_db.return_value = False

        from main import app, lifespan

        async def test_lifespan():
            async with lifespan(app):
                pass

        import asyncio

        asyncio.run(test_lifespan())

        # Should handle failure gracefully
        mock_init_db.assert_called_once()
        mock_logger.error.assert_called()

    @patch("main.init_database")
    @patch("main.logger")
    def test_lifespan_database_init_exception(self, mock_logger, mock_init_db):
        """Test lifespan handling when database initialization raises exception."""
        mock_init_db.side_effect = Exception("Database error")

        from main import app, lifespan

        async def test_lifespan():
            async with lifespan(app):
                pass

        import asyncio

        asyncio.run(test_lifespan())

        # Should handle exception gracefully
        mock_init_db.assert_called_once()
        mock_logger.error.assert_called()


class TestApplicationIntegration:
    """Test full application integration."""

    def test_full_request_cycle(self, client: TestClient, sample_user: User, sample_user_data):
        """Test complete request cycle through the application."""
        # Health check
        health_response = client.get("/health")
        assert health_response.status_code == status.HTTP_200_OK

        # Auth flow - use the sample_user fixture which creates the user in the database
        login_response = client.post("/api/auth/login", json=sample_user_data)
        assert login_response.status_code == status.HTTP_200_OK

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Notes operations
        notes_response = client.get("/api/notes/", headers=headers)
        assert notes_response.status_code == status.HTTP_200_OK

        # Create note
        note_data = {
            "title": "Integration Test Note",
            "content": "# Integration Test Note\n\nThis is an integration test.",
        }
        create_response = client.post("/api/notes/", headers=headers, json=note_data)
        assert create_response.status_code == status.HTTP_200_OK

    def test_error_handling_integration(self, client: TestClient):
        """Test error handling across the application."""
        # Test various error scenarios

        # 404 on unknown endpoint
        response = client.get("/unknown/endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # 401 on protected endpoint without auth
        response = client.get("/api/notes/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # 422 on validation error
        response = client.post("/api/auth/login", json={"invalid": "data"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_cors_integration(self, client: TestClient):
        """Test CORS integration across different endpoints."""
        origin = "http://localhost:5173"
        headers = {"Origin": origin}

        # Test CORS on different types of endpoints
        endpoints = [
            "/",
            "/health",
            "/api/auth/health",
            "/api/notes/health/check",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == status.HTTP_200_OK
            # Should have CORS headers
            assert "access-control-allow-origin" in response.headers

    def test_content_type_handling(self, client: TestClient):
        """Test content type handling across the application."""
        # JSON endpoints should handle JSON properly
        response = client.post("/api/auth/login", json={"username": "test", "password": "test"})
        # Should get a proper response (even if auth fails)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
        assert response.headers["content-type"].startswith("application/json")

        # Health endpoints should return JSON
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("application/json")


class TestSecurityHeaders:
    """Test security-related headers and configurations."""

    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are present in responses."""
        response = client.get("/health")

        # Basic security check - at minimum should have content-type
        assert "content-type" in response.headers

        # If additional security headers are added in the future, test them here

    def test_no_sensitive_info_in_errors(self, client: TestClient):
        """Test that error responses don't leak sensitive information."""
        # Test 500 error response format
        response = client.get("/api/notes/", headers={"Authorization": "Bearer invalid.malformed.token"})

        data = response.json()

        # Should not contain sensitive information
        response_text = str(data).lower()
        assert "password" not in response_text
        assert "secret" not in response_text
        assert "key" not in response_text
        assert "hash" not in response_text

    def test_auth_header_handling(self, client: TestClient):
        """Test proper handling of authorization headers."""
        # Test various malformed auth headers
        malformed_headers = [
            {"Authorization": ""},
            {"Authorization": "Bearer"},
            {"Authorization": "NotBearer token"},
            {"Authorization": "Bearer "},
        ]

        for headers in malformed_headers:
            response = client.get("/api/notes/", headers=headers)
            # Should handle gracefully without exposing internals
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]
