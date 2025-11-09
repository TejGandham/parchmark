"""Unit tests for the health service utilities."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from app.services.health_service import HealthService


def test_check_database_connection_success():
    """The service should execute a lightweight query and report healthy."""
    session = MagicMock()

    assert HealthService.check_database_connection(session) is True

    session.execute.assert_called_once()
    executed_query = session.execute.call_args[0][0]
    assert str(executed_query) == str(text("SELECT 1"))


def test_check_database_connection_failure_returns_false():
    """Database exceptions should be caught and return False."""
    session = MagicMock()
    session.execute.side_effect = RuntimeError("db down")

    assert HealthService.check_database_connection(session) is False


def test_get_health_status_returns_expected_payload(monkeypatch):
    """Healthy database connections should yield the full status payload."""
    monkeypatch.setattr(
        HealthService,
        "check_database_connection",
        staticmethod(lambda _: True),
    )

    status = HealthService.get_health_status(MagicMock())

    assert status == {
        "status": "healthy",
        "database": "connected",
        "service": "ParchMark API",
        "version": "1.0.0",
    }


def test_get_health_status_raises_when_database_unavailable(monkeypatch):
    """The service should raise when the database health check fails."""
    monkeypatch.setattr(
        HealthService,
        "check_database_connection",
        staticmethod(lambda _: False),
    )

    with pytest.raises(Exception, match="Database connection failed"):
        HealthService.get_health_status(MagicMock())
