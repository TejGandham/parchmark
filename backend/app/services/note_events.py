"""
In-process note event broker and Postgres LISTEN consumer.

F23 emits note-change payloads on the ``notes_events`` channel. This module
keeps the per-worker listener and broker independent from the future SSE route.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import asyncpg

from app.database.database import SQLALCHEMY_DATABASE_URL

NOTE_EVENTS_CHANNEL = "notes_events"
DEFAULT_SUBSCRIBER_QUEUE_LIMIT = 50

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class NoteEvent:
    """A normalized note-change event delivered to subscribers."""

    user_id: int
    kind: str
    note_id: int


class NoteEventSubscriber:
    """One independent subscriber queue for a single user."""

    def __init__(self, user_id: int, queue_limit: int = DEFAULT_SUBSCRIBER_QUEUE_LIMIT) -> None:
        if queue_limit <= 0:
            raise ValueError("queue_limit must be greater than zero")

        self.user_id = user_id
        self.queue: asyncio.Queue[NoteEvent] = asyncio.Queue(maxsize=queue_limit)
        self.closed = False

    def close(self) -> None:
        self.closed = True


class NoteEventBroker:
    """Fan out note events to in-process subscribers keyed by user_id."""

    def __init__(self) -> None:
        self._subscribers_by_user: dict[int, set[NoteEventSubscriber]] = defaultdict(set)

    def subscribe(
        self,
        user_id: int,
        queue_limit: int = DEFAULT_SUBSCRIBER_QUEUE_LIMIT,
    ) -> NoteEventSubscriber:
        subscriber = NoteEventSubscriber(user_id=user_id, queue_limit=queue_limit)
        self._subscribers_by_user[user_id].add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: NoteEventSubscriber) -> None:
        subscribers = self._subscribers_by_user.get(subscriber.user_id)
        if subscribers is not None:
            subscribers.discard(subscriber)
            if not subscribers:
                self._subscribers_by_user.pop(subscriber.user_id, None)
        subscriber.close()

    def subscriber_count(self, user_id: int | None = None) -> int:
        if user_id is not None:
            return len(self._subscribers_by_user.get(user_id, set()))
        return sum(len(subscribers) for subscribers in self._subscribers_by_user.values())

    def publish(self, event: NoteEvent) -> None:
        subscribers = list(self._subscribers_by_user.get(event.user_id, set()))
        for subscriber in subscribers:
            if subscriber.closed:
                self.unsubscribe(subscriber)
                continue

            try:
                subscriber.queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Disconnecting saturated note event subscriber for user_id=%s", subscriber.user_id)
                self.unsubscribe(subscriber)

    def publish_payload(self, payload: Mapping[str, Any]) -> None:
        self.publish(_note_event_from_payload(payload))


class PostgresNoteEventListener:
    """Dedicated asyncpg LISTEN connection for one FastAPI worker process."""

    def __init__(
        self,
        dsn: str,
        broker: NoteEventBroker,
        channel: str = NOTE_EVENTS_CHANNEL,
    ) -> None:
        self._dsn = normalize_asyncpg_dsn(dsn)
        self._broker = broker
        self._channel = channel
        self._connection: asyncpg.Connection | None = None

    @property
    def started(self) -> bool:
        return self._connection is not None

    async def start(self) -> None:
        if self._connection is not None:
            return

        connection = await asyncpg.connect(dsn=self._dsn)
        try:
            await connection.add_listener(self._channel, self._handle_notification)
        except Exception:
            await connection.close()
            raise

        self._connection = connection
        logger.info("Started Postgres note-event LISTEN consumer on channel %s", self._channel)

    async def stop(self) -> None:
        connection = self._connection
        if connection is None:
            return

        self._connection = None
        try:
            await connection.remove_listener(self._channel, self._handle_notification)
        except Exception as exc:
            logger.warning("Failed to remove Postgres note-event listener: %s", exc)
        finally:
            await connection.close()
            logger.info("Stopped Postgres note-event LISTEN consumer")

    def _handle_notification(
        self,
        connection: asyncpg.Connection,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        if channel != self._channel:
            return

        try:
            raw_payload = json.loads(payload)
            if not isinstance(raw_payload, dict):
                raise ValueError("payload must be a JSON object")
            self._broker.publish_payload(raw_payload)
        except (TypeError, ValueError) as exc:
            logger.warning("Ignoring invalid note-event notification payload: %s", exc)


def normalize_asyncpg_dsn(database_url: str) -> str:
    """Convert SQLAlchemy PostgreSQL URLs into asyncpg-compatible DSNs."""

    return database_url.replace("postgresql+psycopg2://", "postgresql://").replace(
        "postgresql+asyncpg://",
        "postgresql://",
    )


def create_note_event_listener(broker: NoteEventBroker | None = None) -> PostgresNoteEventListener:
    return PostgresNoteEventListener(dsn=SQLALCHEMY_DATABASE_URL, broker=broker or note_event_broker)


def _note_event_from_payload(payload: Mapping[str, Any]) -> NoteEvent:
    missing_fields = {"user_id", "kind", "note_id"} - set(payload)
    if missing_fields:
        raise ValueError(f"note event payload missing fields: {', '.join(sorted(missing_fields))}")

    user_id = payload["user_id"]
    kind = payload["kind"]
    note_id = payload["note_id"]

    if not isinstance(user_id, int) or not isinstance(note_id, int) or not isinstance(kind, str):
        raise ValueError("note event payload fields must be user_id:int, kind:str, note_id:int")

    return NoteEvent(user_id=user_id, kind=kind, note_id=note_id)


note_event_broker = NoteEventBroker()
