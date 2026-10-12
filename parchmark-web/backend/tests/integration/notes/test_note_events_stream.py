import asyncio
import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.auth import credentials_exception
from app.routers import notes as notes_router
from app.services.note_event_streams import NoteEventStreamManager
from app.services.note_events import NoteEvent


@dataclass
class _RecordedSubscriber:
    user_id: int
    queue: Any
    closed: bool = False

    def close(self):
        self.closed = True


class _FiniteEventQueue:
    def __init__(self, subscriber: _RecordedSubscriber, events: list[NoteEvent]):
        self.subscriber = subscriber
        self.events = events

    async def get(self):
        event = self.events.pop(0)
        if not self.events:
            self.subscriber.closed = True
        return event


class _RequestState:
    def __init__(self, disconnected: bool = False):
        self.disconnected = disconnected

    async def is_disconnected(self):
        return self.disconnected


class _RecordingBroker:
    def __init__(self, events: list[NoteEvent] | None = None):
        self.events = events or []
        self.subscribers: list[_RecordedSubscriber] = []
        self.unsubscribed: list[_RecordedSubscriber] = []

    def subscribe(self, user_id: int):
        subscriber = _RecordedSubscriber(user_id=user_id, queue=None)
        if self.events:
            subscriber.queue = _FiniteEventQueue(subscriber, self.events.copy())
        else:
            subscriber.queue = asyncio.Queue()
        self.subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: _RecordedSubscriber):
        subscriber.closed = True
        self.unsubscribed.append(subscriber)


def _build_client(monkeypatch, broker: _RecordingBroker, current_user):
    async def override_get_async_db():
        yield object()

    async def fake_get_current_user(credentials, db):
        if isinstance(current_user, Exception):
            raise current_user
        return current_user

    stream_manager = NoteEventStreamManager()
    monkeypatch.setattr(notes_router, "note_event_broker", broker)
    monkeypatch.setattr(notes_router, "note_event_stream_manager", stream_manager)
    monkeypatch.setattr(notes_router, "get_current_user", fake_get_current_user)

    app = FastAPI()
    app.dependency_overrides[notes_router.get_async_db] = override_get_async_db
    app.include_router(notes_router.router, prefix="/api")
    return TestClient(app)


def test_note_events_stream_registers_authenticated_user_and_returns_sse(monkeypatch):
    user = SimpleNamespace(id=7)
    broker = _RecordingBroker(events=[NoteEvent(user_id=user.id, kind="updated", note_id="note-9001")])
    client = _build_client(monkeypatch, broker, user)

    response = client.get("/api/notes/events", headers={"Authorization": "Bearer valid-token"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert [subscriber.user_id for subscriber in broker.subscribers] == [user.id]
    assert broker.unsubscribed == broker.subscribers

    lines = response.text.splitlines()
    assert lines[0] == "data: " + json.dumps({"kind": "updated", "note_id": "note-9001"})
    assert "user_id" not in lines[0]


def test_note_events_stream_rejects_missing_credentials_without_subscribing(monkeypatch):
    broker = _RecordingBroker()
    client = _build_client(monkeypatch, broker, AssertionError("auth should not be called"))

    response = client.get("/api/notes/events")

    assert response.status_code == 401
    assert broker.subscribers == []


@pytest.mark.asyncio
async def test_idle_note_events_stream_emits_heartbeat_and_can_close(monkeypatch):
    broker = _RecordingBroker()
    stream_manager = NoteEventStreamManager()
    monkeypatch.setattr(notes_router, "note_event_broker", broker)
    monkeypatch.setattr(notes_router, "note_event_stream_manager", stream_manager)

    stream = notes_router._note_events_sse_stream(
        user_id=7,
        request=_RequestState(),
        heartbeat_interval_seconds=0.01,
    )

    assert await asyncio.wait_for(anext(stream), timeout=1) == ":heartbeat\n\n"
    await stream.aclose()

    assert [subscriber.user_id for subscriber in broker.subscribers] == [7]
    assert broker.unsubscribed == broker.subscribers


@pytest.mark.asyncio
async def test_disconnected_note_events_stream_unregisters_subscriber(monkeypatch):
    broker = _RecordingBroker()
    stream_manager = NoteEventStreamManager()
    monkeypatch.setattr(notes_router, "note_event_broker", broker)
    monkeypatch.setattr(notes_router, "note_event_stream_manager", stream_manager)

    stream = notes_router._note_events_sse_stream(
        user_id=7,
        request=_RequestState(disconnected=True),
        heartbeat_interval_seconds=30,
    )

    with pytest.raises(StopAsyncIteration):
        await asyncio.wait_for(anext(stream), timeout=1)

    assert [subscriber.user_id for subscriber in broker.subscribers] == [7]
    assert broker.unsubscribed == broker.subscribers


@pytest.mark.asyncio
async def test_shutdown_closes_idle_note_events_stream_without_waiting_for_heartbeat(monkeypatch):
    broker = _RecordingBroker()
    stream_manager = NoteEventStreamManager()
    monkeypatch.setattr(notes_router, "note_event_broker", broker)
    monkeypatch.setattr(notes_router, "note_event_stream_manager", stream_manager)

    stream = notes_router._note_events_sse_stream(
        user_id=7,
        request=_RequestState(),
        heartbeat_interval_seconds=30,
    )
    next_frame = asyncio.create_task(anext(stream))
    await asyncio.sleep(0)

    await stream_manager.close_all()

    with pytest.raises(StopAsyncIteration):
        await asyncio.wait_for(next_frame, timeout=1)

    assert broker.unsubscribed == broker.subscribers


def test_note_events_stream_rejects_invalid_credentials_without_subscribing(monkeypatch):
    broker = _RecordingBroker()
    client = _build_client(monkeypatch, broker, credentials_exception)

    response = client.get("/api/notes/events", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401
    assert broker.subscribers == []
