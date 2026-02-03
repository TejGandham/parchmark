"""Unit tests for the health service utilities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text

from app.services.health_service import HealthService


@pytest.mark.asyncio
async def test_check_database_connection_success():
    """The service should execute a lightweight query and report healthy."""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()

    with patch("app.services.health_service.get_db", return_value=mock_db):
        service = HealthService()
        assert await service.check_database_connection() is True

    mock_db.execute.assert_called_once()
    executed_query = mock_db.execute.call_args[0][0]
    assert str(executed_query) == str(text("SELECT 1"))


@pytest.mark.asyncio
async def test_check_database_connection_failure_returns_false():
    """Database exceptions should be caught and return False."""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock(side_effect=RuntimeError("db down"))

    with patch("app.services.health_service.get_db", return_value=mock_db):
        service = HealthService()
        assert await service.check_database_connection() is False


@pytest.mark.asyncio
async def test_get_health_status_returns_expected_payload():
    """Healthy database connections should yield the full status payload."""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()

    with patch("app.services.health_service.get_db", return_value=mock_db):
        service = HealthService()
        status = await service.get_health_status()

    assert status == {
        "status": "healthy",
        "database": "connected",
        "service": "ParchMark API",
        "version": "1.0.0",
    }


@pytest.mark.asyncio
async def test_get_health_status_raises_when_database_unavailable():
    """The service should raise when the database health check fails."""
    mock_db = MagicMock()
    mock_db.execute = AsyncMock(side_effect=RuntimeError("db down"))

    with patch("app.services.health_service.get_db", return_value=mock_db):
        service = HealthService()

        with pytest.raises(Exception, match="Database connection failed"):
            await service.get_health_status()
