"""Lifecycle coordination for active note-event SSE streams."""

from __future__ import annotations

import asyncio

from app.services.note_events import NoteEventSubscriber

NOTE_EVENTS_HEARTBEAT_INTERVAL_SECONDS = 30
NOTE_EVENTS_HEARTBEAT_FRAME = ":heartbeat\n\n"


class NoteEventStreamManager:
    """Tracks active note-event streams and signals app shutdown to them."""

    def __init__(self) -> None:
        self._closing = False
        self._subscribers: dict[int, NoteEventSubscriber] = {}
        self._shutdown_events: dict[int, asyncio.Event] = {}

    @property
    def is_closing(self) -> bool:
        return self._closing

    def open(self) -> None:
        self._closing = False
        self._shutdown_events.clear()

    def register(self, subscriber: NoteEventSubscriber) -> None:
        self._subscribers[id(subscriber)] = subscriber

    def unregister(self, subscriber: NoteEventSubscriber) -> None:
        self._subscribers.pop(id(subscriber), None)

    def shutdown_event(self) -> asyncio.Event:
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
        event = self._shutdown_events.get(loop_id)
        if event is None:
            event = asyncio.Event()
            if self._closing:
                event.set()
            self._shutdown_events[loop_id] = event
        return event

    async def close_all(self) -> None:
        self._closing = True
        for event in self._shutdown_events.values():
            event.set()
        for subscriber in list(self._subscribers.values()):
            subscriber.close()


note_event_stream_manager = NoteEventStreamManager()
