import asyncio

import pytest

from app.services.note_events import (
    NOTE_EVENTS_CHANNEL,
    NoteEvent,
    NoteEventBroker,
    PostgresNoteEventListener,
    create_note_event_listener,
)


def test_subscribe_rejects_non_positive_queue_limit():
    broker = NoteEventBroker()

    with pytest.raises(ValueError, match="queue_limit"):
        broker.subscribe(user_id=1, queue_limit=0)


def test_subscribe_uses_default_queue_limit_50():
    broker = NoteEventBroker()

    subscriber = broker.subscribe(user_id=1)

    assert subscriber.queue.maxsize == 50


def test_broker_routes_payloads_only_to_matching_user():
    broker = NoteEventBroker()
    user_one_tab_a = broker.subscribe(user_id=1)
    user_one_tab_b = broker.subscribe(user_id=1)
    user_two = broker.subscribe(user_id=2)

    event = NoteEvent(user_id=1, kind="updated", note_id=101)
    broker.publish(event)

    assert user_one_tab_a.queue.get_nowait() == event
    assert user_one_tab_b.queue.get_nowait() == event
    assert user_two.queue.empty()


def test_unsubscribe_closes_subscriber_and_removes_empty_user_bucket():
    broker = NoteEventBroker()
    subscriber = broker.subscribe(user_id=1)

    assert broker.subscriber_count() == 1

    broker.unsubscribe(subscriber)

    assert subscriber.closed is True
    assert broker.subscriber_count() == 0
    assert broker.subscriber_count(user_id=1) == 0


def test_publish_removes_previously_closed_subscriber():
    broker = NoteEventBroker()
    subscriber = broker.subscribe(user_id=1)
    subscriber.close()

    broker.publish(NoteEvent(user_id=1, kind="updated", note_id=101))

    assert broker.subscriber_count(user_id=1) == 0


def test_saturated_subscriber_is_disconnected_without_blocking_others():
    broker = NoteEventBroker()
    saturated = broker.subscribe(user_id=1, queue_limit=1)
    healthy = broker.subscribe(user_id=1, queue_limit=1)

    saturated.queue.put_nowait(NoteEvent(user_id=1, kind="created", note_id=100))
    event = NoteEvent(user_id=1, kind="updated", note_id=101)
    broker.publish(event)

    assert saturated.closed is True
    assert healthy.closed is False
    assert healthy.queue.get_nowait() == event
    assert broker.subscriber_count(user_id=1) == 1


def test_publish_payload_requires_declared_f23_fields():
    broker = NoteEventBroker()
    subscriber = broker.subscribe(user_id=3)

    broker.publish_payload({"user_id": 3, "kind": "deleted", "note_id": 44})

    assert subscriber.queue.get_nowait() == NoteEvent(user_id=3, kind="deleted", note_id=44)


def test_publish_payload_rejects_missing_or_invalid_fields():
    broker = NoteEventBroker()

    with pytest.raises(ValueError, match="missing fields"):
        broker.publish_payload({"user_id": 3, "kind": "deleted"})

    with pytest.raises(ValueError, match="user_id:int"):
        broker.publish_payload({"user_id": "3", "kind": "deleted", "note_id": 44})


@pytest.mark.asyncio
async def test_listener_start_registers_exactly_one_listen_connection(monkeypatch):
    connections = []

    class FakeConnection:
        def __init__(self):
            self.add_calls = []
            self.remove_calls = []
            self.closed = False

        async def add_listener(self, channel, callback):
            self.add_calls.append((channel, callback))

        async def remove_listener(self, channel, callback):
            self.remove_calls.append((channel, callback))

        async def close(self):
            self.closed = True

    async def fake_connect(*, dsn):
        assert dsn == "postgresql://user:pass@example.test/db"
        connection = FakeConnection()
        connections.append(connection)
        return connection

    monkeypatch.setattr("app.services.note_events.asyncpg.connect", fake_connect)

    listener = PostgresNoteEventListener(
        dsn="postgresql+psycopg2://user:pass@example.test/db",
        broker=NoteEventBroker(),
    )

    assert listener.started is False
    await listener.stop()
    await listener.start()
    assert listener.started is True
    await listener.start()
    await listener.stop()
    assert listener.started is False

    assert len(connections) == 1
    assert [call[0] for call in connections[0].add_calls] == [NOTE_EVENTS_CHANNEL]
    assert [call[0] for call in connections[0].remove_calls] == [NOTE_EVENTS_CHANNEL]
    assert connections[0].closed is True


@pytest.mark.asyncio
async def test_listener_callback_publishes_valid_json_payload(monkeypatch):
    callback_holder = {}

    class FakeConnection:
        async def add_listener(self, channel, callback):
            callback_holder["callback"] = callback

        async def remove_listener(self, channel, callback):
            return None

        async def close(self):
            return None

    async def fake_connect(*, dsn):
        return FakeConnection()

    monkeypatch.setattr("app.services.note_events.asyncpg.connect", fake_connect)

    broker = NoteEventBroker()
    subscriber = broker.subscribe(user_id=5)
    listener = PostgresNoteEventListener(dsn="postgresql://example.test/db", broker=broker)
    await listener.start()

    callback_holder["callback"](None, 123, NOTE_EVENTS_CHANNEL, '{"user_id": 5, "kind": "created", "note_id": 77}')
    await asyncio.sleep(0)

    assert subscriber.queue.get_nowait() == NoteEvent(user_id=5, kind="created", note_id=77)

    await listener.stop()


@pytest.mark.asyncio
async def test_listener_start_failure_closes_connection(monkeypatch):
    class FakeConnection:
        def __init__(self):
            self.closed = False

        async def add_listener(self, channel, callback):
            raise RuntimeError("listen failed")

        async def close(self):
            self.closed = True

    connection = FakeConnection()

    async def fake_connect(*, dsn):
        return connection

    monkeypatch.setattr("app.services.note_events.asyncpg.connect", fake_connect)

    listener = PostgresNoteEventListener(dsn="postgresql://example.test/db", broker=NoteEventBroker())

    with pytest.raises(RuntimeError, match="listen failed"):
        await listener.start()

    assert connection.closed is True
    assert listener.started is False


@pytest.mark.asyncio
async def test_listener_stop_closes_connection_when_remove_listener_fails(monkeypatch):
    class FakeConnection:
        def __init__(self):
            self.closed = False

        async def add_listener(self, channel, callback):
            return None

        async def remove_listener(self, channel, callback):
            raise RuntimeError("remove failed")

        async def close(self):
            self.closed = True

    connection = FakeConnection()

    async def fake_connect(*, dsn):
        return connection

    monkeypatch.setattr("app.services.note_events.asyncpg.connect", fake_connect)

    listener = PostgresNoteEventListener(dsn="postgresql://example.test/db", broker=NoteEventBroker())
    await listener.start()
    await listener.stop()

    assert connection.closed is True
    assert listener.started is False


@pytest.mark.asyncio
async def test_listener_callback_ignores_wrong_channel_and_invalid_payload(monkeypatch):
    callback_holder = {}

    class FakeConnection:
        async def add_listener(self, channel, callback):
            callback_holder["callback"] = callback

        async def remove_listener(self, channel, callback):
            return None

        async def close(self):
            return None

    async def fake_connect(*, dsn):
        return FakeConnection()

    monkeypatch.setattr("app.services.note_events.asyncpg.connect", fake_connect)

    broker = NoteEventBroker()
    subscriber = broker.subscribe(user_id=5)
    listener = PostgresNoteEventListener(dsn="postgresql://example.test/db", broker=broker)
    await listener.start()

    callback_holder["callback"](None, 123, "other_channel", '{"user_id": 5, "kind": "created", "note_id": 77}')
    callback_holder["callback"](None, 123, NOTE_EVENTS_CHANNEL, "not-json")
    callback_holder["callback"](None, 123, NOTE_EVENTS_CHANNEL, "[]")
    callback_holder["callback"](None, 123, NOTE_EVENTS_CHANNEL, '{"user_id": "5", "kind": "created", "note_id": 77}')

    assert subscriber.queue.empty()

    await listener.stop()


def test_create_note_event_listener_uses_default_broker():
    listener = create_note_event_listener()

    assert isinstance(listener, PostgresNoteEventListener)
