"""Unit tests for the health service utilities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import text

from app.services.health_service import HealthService
from app.version import VERSION


@pytest.mark.asyncio
async def test_check_database_connection_success():
    """The service should execute a lightweight query and report healthy."""
    session = MagicMock()
    session.execute = AsyncMock()

    assert await HealthService.check_database_connection(session) is True

    session.execute.assert_called_once()
    executed_query = session.execute.call_args[0][0]
    assert str(executed_query) == str(text("SELECT 1"))


@pytest.mark.asyncio
async def test_check_database_connection_failure_returns_false():
    """Database exceptions should be caught and return False."""
    session = MagicMock()
    session.execute = AsyncMock(side_effect=RuntimeError("db down"))

    assert await HealthService.check_database_connection(session) is False


@pytest.mark.asyncio
async def test_get_health_status_returns_expected_payload(monkeypatch):
    """Healthy database connections should yield the full status payload."""

    async def mock_check_connection(_):
        return True

    monkeypatch.setattr(
        HealthService,
        "check_database_connection",
        staticmethod(mock_check_connection),
    )

    status = await HealthService.get_health_status(MagicMock())

    assert status["status"] == "healthy"
    assert status["database"] == "connected"
    assert status["service"] == "ParchMark API"
    assert status["version"] == VERSION
    assert "gitSha" in status
    assert "buildDate" in status


@pytest.mark.asyncio
async def test_get_health_status_raises_when_database_unavailable(monkeypatch):
    """The service should raise when the database health check fails."""

    async def mock_check_connection(_):
        return False

    monkeypatch.setattr(
        HealthService,
        "check_database_connection",
        staticmethod(mock_check_connection),
    )

    with pytest.raises(Exception, match="Database connection failed"):
        await HealthService.get_health_status(MagicMock())
