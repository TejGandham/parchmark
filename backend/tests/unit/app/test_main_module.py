"""Unit tests for the `app.__main__` module entry point."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import app.__main__ as app_main


def _capture_print(monkeypatch) -> list[str]:
    """Patch builtins.print and capture each message as a single string."""

    messages: list[str] = []

    def _fake_print(*args, **kwargs):
        text = " ".join(str(arg) for arg in args)
        messages.append(text)

    monkeypatch.setattr("builtins.print", _fake_print)
    return messages


def test_main_uses_environment_configuration(monkeypatch):
    """main() should honor HOST/PORT/log level env vars and enable reload in development."""
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    mock_uvicorn_run = MagicMock()
    monkeypatch.setattr(app_main.uvicorn, "run", mock_uvicorn_run)
    messages = _capture_print(monkeypatch)

    app_main.main()

    mock_uvicorn_run.assert_called_once_with(
        "app.main:app",
        host="127.0.0.1",
        port=9000,
        reload=True,
        log_level="warning",
        access_log=True,
    )
    assert any("ParchMark Backend Server" in message for message in messages)


def test_main_handles_keyboard_interrupt(monkeypatch):
    """main() should swallow KeyboardInterrupt and log a friendly shutdown message."""
    monkeypatch.setenv("ENVIRONMENT", "production")

    mock_uvicorn_run = MagicMock(side_effect=KeyboardInterrupt)
    monkeypatch.setattr(app_main.uvicorn, "run", mock_uvicorn_run)
    messages = _capture_print(monkeypatch)

    # Should not raise despite KeyboardInterrupt bubbling from uvicorn
    app_main.main()

    mock_uvicorn_run.assert_called_once()
    assert messages[-1].strip().startswith("🛑 Server stopped by user")


def test_main_rethrows_unexpected_startup_errors(monkeypatch):
    """main() should log and re-raise unexpected exceptions from uvicorn."""
    monkeypatch.setenv("ENVIRONMENT", "development")

    mock_uvicorn_run = MagicMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(app_main.uvicorn, "run", mock_uvicorn_run)
    messages = _capture_print(monkeypatch)

    with pytest.raises(RuntimeError, match="boom"):
        app_main.main()

    mock_uvicorn_run.assert_called_once()
    assert any("Failed to start server" in message for message in messages)
