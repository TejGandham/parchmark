import asyncio
import json

import asyncpg
import pytest
from testcontainers.postgres import PostgresContainer

from app.services.note_events import NOTE_EVENTS_CHANNEL, NoteEvent, NoteEventBroker, PostgresNoteEventListener


def _asyncpg_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg2://", "postgresql://").replace(
        "postgresql+asyncpg://", "postgresql://"
    )


@pytest.fixture(scope="module")
def postgres_dsn():
    with PostgresContainer("postgres:17") as postgres:
        yield _asyncpg_dsn(postgres.get_connection_url())


@pytest.mark.asyncio
async def test_two_broker_instances_each_receive_every_postgres_notification(postgres_dsn):
    broker_a = NoteEventBroker()
    broker_b = NoteEventBroker()
    listener_a = PostgresNoteEventListener(dsn=postgres_dsn, broker=broker_a)
    listener_b = PostgresNoteEventListener(dsn=postgres_dsn, broker=broker_b)
    subscriber_a = broker_a.subscribe(user_id=42)
    subscriber_b = broker_b.subscribe(user_id=42)

    await listener_a.start()
    await listener_b.start()
    publisher = await asyncpg.connect(dsn=postgres_dsn)

    try:
        payload = json.dumps({"user_id": 42, "kind": "updated", "note_id": 9001})
        await publisher.execute("SELECT pg_notify($1::text, $2::text)", NOTE_EVENTS_CHANNEL, payload)

        expected = NoteEvent(user_id=42, kind="updated", note_id=9001)
        assert await asyncio.wait_for(subscriber_a.queue.get(), timeout=2) == expected
        assert await asyncio.wait_for(subscriber_b.queue.get(), timeout=2) == expected
    finally:
        await publisher.close()
        await listener_a.stop()
        await listener_b.stop()
