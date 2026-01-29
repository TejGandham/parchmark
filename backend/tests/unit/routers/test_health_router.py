"""Unit tests for the health router."""

import pytest
from fastapi import HTTPException

from app.routers.health import health_check
from app.services.health_service import health_service


class DummySession:
    """Lightweight stand-in for a SQLAlchemy async session."""


@pytest.mark.asyncio
async def test_health_check_returns_service_payload(monkeypatch):
    """The endpoint should proxy the health service payload on success."""

    expected_payload = {"status": "healthy", "database": "connected"}

    async def fake_get_health_status(db):  # pragma: no cover - simple stub
        assert isinstance(db, DummySession)
        return expected_payload

    monkeypatch.setattr(health_service, "get_health_status", fake_get_health_status)

    result = await health_check(db=DummySession())

    assert result is expected_payload


@pytest.mark.asyncio
async def test_health_check_raises_http_exception_on_service_failure(monkeypatch):
    """The endpoint should convert service errors into HTTP 503 responses."""

    async def fake_get_health_status(_):  # pragma: no cover - simple stub
        raise RuntimeError("boom")

    monkeypatch.setattr(health_service, "get_health_status", fake_get_health_status)

    with pytest.raises(HTTPException) as excinfo:
        await health_check(db=DummySession())

    error = excinfo.value
    assert error.status_code == 503
    assert "Service unhealthy" in error.detail
