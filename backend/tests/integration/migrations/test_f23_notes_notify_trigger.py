"""
Integration tests for F23: Postgres trigger emits NOTIFY on note title/content/delete.

Oracle: /features/0/oracle
Contract: /features/0/contract
"""

import json
import os
import select
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from testcontainers.postgres import PostgresContainer

_BACKEND_ROOT = Path(__file__).parents[3]
_ALEMBIC_INI = _BACKEND_ROOT / "alembic.ini"
_PARENT_REVISION = "7f1c343772e8"
_NOTIFY_CHANNEL = "notes_events"

_PARENT_SCHEMA_SQL = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    email VARCHAR(255),
    oidc_sub VARCHAR(255) UNIQUE,
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
CREATE INDEX ix_users_id ON users(id);
CREATE INDEX ix_users_username ON users(username);
CREATE INDEX ix_users_oidc_sub ON users(oidc_sub);

CREATE TABLE notes (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
CREATE INDEX ix_notes_id ON notes(id);
CREATE INDEX ix_notes_user_id ON notes(user_id);
"""


@pytest.fixture(scope="module")
def migration_container() -> Iterator[tuple[Engine, Config]]:
    """Postgres container stamped at F23's parent revision."""
    saved_database_url = os.environ.get("DATABASE_URL")
    with PostgresContainer("postgres:17") as pg:
        sync_url = pg.get_connection_url()
        os.environ["DATABASE_URL"] = sync_url

        try:
            engine = create_engine(sync_url)
            with engine.begin() as conn:
                for statement in _PARENT_SCHEMA_SQL.strip().split(";"):
                    sql = statement.strip()
                    if sql:
                        conn.execute(text(sql))

            alembic_cfg = Config(str(_ALEMBIC_INI))
            alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
            command.stamp(alembic_cfg, _PARENT_REVISION)
            command.upgrade(alembic_cfg, "head")

            yield engine, alembic_cfg
        finally:
            if saved_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = saved_database_url


@pytest.fixture()
def upgraded_engine(migration_container: tuple[Engine, Config]) -> Iterator[Engine]:
    """Clean user/note rows before each trigger behavior test."""
    engine, _ = migration_container
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM notes"))
        conn.execute(text("DELETE FROM users"))
    yield engine


@pytest.fixture()
def listener(upgraded_engine: Engine):
    """Open a dedicated LISTEN connection for notes_events."""
    raw = upgraded_engine.raw_connection()
    raw.set_session(autocommit=True)
    cursor = raw.cursor()
    cursor.execute(f"LISTEN {_NOTIFY_CHANNEL}")
    try:
        yield raw
    finally:
        cursor.execute(f"UNLISTEN {_NOTIFY_CHANNEL}")
        cursor.close()
        raw.close()


def _collect_notifications(raw_connection, expected: int, timeout: float = 2.0) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    payloads: list[dict[str, Any]] = []

    while len(payloads) < expected and time.monotonic() < deadline:
        remaining = max(0.0, deadline - time.monotonic())
        readable, _, _ = select.select([raw_connection], [], [], remaining)
        if not readable:
            break
        raw_connection.poll()
        while raw_connection.notifies:
            notification = raw_connection.notifies.pop(0)
            payloads.append(json.loads(notification.payload))

    return payloads


def _create_user(engine: Engine) -> int:
    username = f"f23-user-{uuid.uuid4()}"
    with engine.begin() as conn:
        return conn.execute(
            text(
                """
                INSERT INTO users (username, password_hash, auth_provider)
                VALUES (:username, 'hash', 'local')
                RETURNING id
                """
            ),
            {"username": username},
        ).scalar_one()


def _insert_note(engine: Engine, user_id: int, note_id: str = "note-f23-1") -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO notes (id, user_id, title, content)
                VALUES (:id, :user_id, 'Original title', 'Original content')
                """
            ),
            {"id": note_id, "user_id": user_id},
        )


def test_insert_update_delete_each_emit_one_notification(upgraded_engine: Engine, listener):
    user_id = _create_user(upgraded_engine)

    _insert_note(upgraded_engine, user_id)
    insert_payload = _collect_notifications(listener, expected=1)
    assert insert_payload == [{"user_id": user_id, "kind": "created", "note_id": "note-f23-1"}]

    with upgraded_engine.begin() as conn:
        conn.execute(
            text("UPDATE notes SET title = 'Updated title' WHERE id = 'note-f23-1'"),
        )
    update_payload = _collect_notifications(listener, expected=1)
    assert update_payload == [{"user_id": user_id, "kind": "updated", "note_id": "note-f23-1"}]

    with upgraded_engine.begin() as conn:
        conn.execute(text("DELETE FROM notes WHERE id = 'note-f23-1'"))
    delete_payload = _collect_notifications(listener, expected=1)
    assert delete_payload == [{"user_id": user_id, "kind": "deleted", "note_id": "note-f23-1"}]


def test_rolled_back_insert_emits_no_notification(upgraded_engine: Engine, listener):
    user_id = _create_user(upgraded_engine)

    conn = upgraded_engine.connect()
    transaction = conn.begin()
    try:
        conn.execute(
            text(
                """
                INSERT INTO notes (id, user_id, title, content)
                VALUES ('note-f23-rollback', :user_id, 'Rollback title', 'Rollback content')
                """
            ),
            {"user_id": user_id},
        )
        transaction.rollback()
    finally:
        conn.close()

    assert _collect_notifications(listener, expected=1, timeout=0.5) == []


def test_non_title_content_update_emits_no_notification(upgraded_engine: Engine, listener):
    user_id = _create_user(upgraded_engine)
    _insert_note(upgraded_engine, user_id, note_id="note-f23-quiet")
    assert len(_collect_notifications(listener, expected=1)) == 1

    with upgraded_engine.begin() as conn:
        conn.execute(text("UPDATE notes SET updated_at = now() WHERE id = 'note-f23-quiet'"))

    assert _collect_notifications(listener, expected=1, timeout=0.5) == []


def test_title_update_to_same_value_emits_no_notification(upgraded_engine: Engine, listener):
    user_id = _create_user(upgraded_engine)
    _insert_note(upgraded_engine, user_id, note_id="note-f23-same-title")
    assert len(_collect_notifications(listener, expected=1)) == 1

    with upgraded_engine.begin() as conn:
        conn.execute(text("UPDATE notes SET title = title WHERE id = 'note-f23-same-title'"))

    assert _collect_notifications(listener, expected=1, timeout=0.5) == []
