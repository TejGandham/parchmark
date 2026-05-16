import pytest

import app.main as main_module
from app.main import app, lifespan


@pytest.mark.asyncio
async def test_lifespan_starts_one_note_event_listener_after_database_init(monkeypatch):
    events = []

    class FakeListener:
        async def start(self):
            events.append("start")

        async def stop(self):
            events.append("stop")

    listener = FakeListener()

    monkeypatch.setattr("app.main.init_database", lambda: True)
    monkeypatch.setattr("app.main.create_note_event_listener", lambda: listener)

    class FakeStreamManager:
        def open(self):
            events.append("streams-open")

        async def close_all(self):
            events.append("streams-close")

    monkeypatch.setattr(main_module, "note_event_stream_manager", FakeStreamManager())

    async def fake_oidc_close():
        events.append("oidc-close")

    monkeypatch.setattr("app.main.oidc_validator.close", fake_oidc_close)

    class FakeEngine:
        async def dispose(self):
            events.append("engine-dispose")

    monkeypatch.setattr(main_module, "async_engine", FakeEngine())

    async with lifespan(app):
        assert app.state.note_event_listener is listener
        assert events == ["streams-open", "start"]

    assert events == ["streams-open", "start", "streams-close", "stop", "oidc-close", "engine-dispose"]
