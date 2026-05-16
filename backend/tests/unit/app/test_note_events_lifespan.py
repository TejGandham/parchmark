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

    async def fake_oidc_close():
        events.append("oidc-close")

    monkeypatch.setattr("app.main.oidc_validator.close", fake_oidc_close)

    class FakeEngine:
        async def dispose(self):
            events.append("engine-dispose")

    monkeypatch.setattr(main_module, "async_engine", FakeEngine())

    async with lifespan(app):
        assert app.state.note_event_listener is listener
        assert events == ["start"]

    assert events == ["start", "stop", "oidc-close", "engine-dispose"]
