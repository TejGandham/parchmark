"""
Integration tests for the note_tags Alembic migration.
"""

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from testcontainers.postgres import PostgresContainer

_BACKEND_ROOT = Path(__file__).parents[3]
_ALEMBIC_INI = _BACKEND_ROOT / "alembic.ini"
_PARENT_REVISION = "8f4d2b1c9a7e"
_HEAD_REVISION = "1b2c3d4e5f6a"

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

            yield engine, alembic_cfg
        finally:
            if saved_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = saved_database_url


def test_note_tags_upgrade_creates_table_constraints_and_indexes(migration_container: tuple[Engine, Config]):
    engine, alembic_cfg = migration_container

    command.upgrade(alembic_cfg, _HEAD_REVISION)

    inspector = sa.inspect(engine)
    assert "note_tags" in inspector.get_table_names()

    columns = {column["name"]: column for column in inspector.get_columns("note_tags")}
    assert set(columns) == {"id", "note_id", "tag"}
    assert columns["note_id"]["nullable"] is False
    assert columns["tag"]["nullable"] is False

    indexes = {index["name"] for index in inspector.get_indexes("note_tags")}
    assert {"ix_note_tags_id", "ix_note_tags_note_id", "ix_note_tags_tag"}.issubset(indexes)

    unique_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("note_tags")}
    assert "uq_note_tags_note_id_tag" in unique_constraints

    check_constraints = {constraint["name"] for constraint in inspector.get_check_constraints("note_tags")}
    assert "note_tags_tag_not_empty" in check_constraints


def test_note_tags_constraints_and_cascade_work(migration_container: tuple[Engine, Config]):
    engine, alembic_cfg = migration_container
    command.upgrade(alembic_cfg, _HEAD_REVISION)
    username = f"note-tags-{uuid.uuid4()}"

    with engine.begin() as conn:
        user_id = conn.execute(
            text(
                """
                INSERT INTO users (username, password_hash, auth_provider)
                VALUES (:username, 'hash', 'local')
                RETURNING id
                """
            ),
            {"username": username},
        ).scalar_one()
        conn.execute(
            text(
                """
                INSERT INTO notes (id, user_id, title, content)
                VALUES ('note-tags-1', :user_id, 'Tagged', '# Tagged')
                """
            ),
            {"user_id": user_id},
        )
        conn.execute(text("INSERT INTO note_tags (note_id, tag) VALUES ('note-tags-1', 'work')"))

    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO note_tags (note_id, tag) VALUES ('note-tags-1', 'work')"))

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM notes WHERE id = 'note-tags-1'"))
        remaining = conn.execute(text("SELECT count(*) FROM note_tags WHERE note_id = 'note-tags-1'")).scalar_one()

    assert remaining == 0


def test_note_tags_downgrade_drops_table(migration_container: tuple[Engine, Config]):
    engine, alembic_cfg = migration_container

    command.downgrade(alembic_cfg, _PARENT_REVISION)

    inspector = sa.inspect(engine)
    assert "note_tags" not in inspector.get_table_names()
