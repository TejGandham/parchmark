"""
Integration tests for the api_tokens Alembic migration.

Covers a brownfield DB stamped at the parent revision (table created, cascade
works, downgrade drops it) and a fresh DB where create_all already produced the
schema (upgrade is a no-op).
"""

import os
import subprocess
import sys
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
from testcontainers.community.postgres import PostgresContainer

from app.database.database import Base

_BACKEND_ROOT = Path(__file__).parents[3]
_ALEMBIC_INI = _BACKEND_ROOT / "alembic.ini"
_PARENT_REVISION = "be7aafff4947"
_HEAD_REVISION = "dba02717ee2f"

# Schema state at be7aafff4947: users (with valid_auth_credentials), notes, note_tags.
_PARENT_SCHEMA_SQL = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    email VARCHAR(255),
    oidc_sub VARCHAR(255) UNIQUE,
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT valid_auth_credentials CHECK (
        (auth_provider = 'local' AND password_hash IS NOT NULL) OR
        (auth_provider = 'oidc' AND oidc_sub IS NOT NULL)
    )
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

CREATE TABLE note_tags (
    id SERIAL PRIMARY KEY,
    note_id VARCHAR(50) NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag VARCHAR(64) NOT NULL,
    CONSTRAINT note_tags_tag_not_empty CHECK (length(tag) > 0),
    CONSTRAINT uq_note_tags_note_id_tag UNIQUE (note_id, tag)
);
CREATE INDEX ix_note_tags_id ON note_tags(id);
CREATE INDEX ix_note_tags_note_id ON note_tags(note_id);
CREATE INDEX ix_note_tags_tag ON note_tags(tag);
"""


@pytest.fixture(scope="module")
def migration_container() -> Iterator[str]:
    """One container per module; DATABASE_URL points at it because migrations/env.py reads it."""
    saved_database_url = os.environ.get("DATABASE_URL")
    with PostgresContainer("postgres:17") as pg:
        sync_url = pg.get_connection_url()
        os.environ["DATABASE_URL"] = sync_url
        try:
            yield sync_url
        finally:
            if saved_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = saved_database_url


@pytest.fixture
def engine(migration_container: str) -> Iterator[Engine]:
    """An engine on an empty public schema, reset for every test."""
    engine = create_engine(migration_container)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    yield engine
    engine.dispose()


@pytest.fixture
def alembic_cfg(migration_container: str) -> Config:
    alembic_cfg = Config(str(_ALEMBIC_INI))
    alembic_cfg.set_main_option("sqlalchemy.url", migration_container)
    return alembic_cfg


@pytest.fixture
def brownfield(engine: Engine, alembic_cfg: Config) -> tuple[Engine, Config]:
    """A DB at the parent revision, before api_tokens existed."""
    with engine.begin() as conn:
        for statement in _PARENT_SCHEMA_SQL.strip().split(";"):
            sql = statement.strip()
            if sql:
                conn.execute(text(sql))
    command.stamp(alembic_cfg, _PARENT_REVISION)
    return engine, alembic_cfg


def test_upgrade_creates_table_and_indexes(brownfield: tuple[Engine, Config]):
    engine, alembic_cfg = brownfield

    command.upgrade(alembic_cfg, _HEAD_REVISION)

    inspector = sa.inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("api_tokens")}
    assert set(columns) == {"id", "user_id", "name", "token_hash", "created_at"}
    assert all(column["nullable"] is False for column in columns.values())

    indexes = {index["name"]: index for index in inspector.get_indexes("api_tokens")}
    assert indexes["ix_api_tokens_token_hash"]["unique"]
    assert not indexes["ix_api_tokens_user_id"]["unique"]

    (foreign_key,) = inspector.get_foreign_keys("api_tokens")
    assert foreign_key["referred_table"] == "users"
    assert foreign_key["options"].get("ondelete") == "CASCADE"


def test_token_hash_is_unique_and_user_delete_cascades(brownfield: tuple[Engine, Config]):
    engine, alembic_cfg = brownfield
    command.upgrade(alembic_cfg, _HEAD_REVISION)

    with engine.begin() as conn:
        user_id = conn.execute(
            text("INSERT INTO users (username, password_hash) VALUES (:username, 'hash') RETURNING id"),
            {"username": f"tokens-{uuid.uuid4().hex[:8]}"},
        ).scalar_one()
        conn.execute(
            text("INSERT INTO api_tokens (user_id, name, token_hash) VALUES (:user_id, 'cli', 'digest')"),
            {"user_id": user_id},
        )

    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO api_tokens (user_id, name, token_hash) VALUES (:user_id, 'dup', 'digest')"),
                {"user_id": user_id},
            )

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
        remaining = conn.execute(text("SELECT count(*) FROM api_tokens")).scalar_one()

    assert remaining == 0


def test_downgrade_drops_table(brownfield: tuple[Engine, Config]):
    engine, alembic_cfg = brownfield
    command.upgrade(alembic_cfg, _HEAD_REVISION)

    command.downgrade(alembic_cfg, _PARENT_REVISION)
    command.downgrade(alembic_cfg, _PARENT_REVISION)  # already at parent: must not raise

    assert "api_tokens" not in sa.inspect(engine).get_table_names()


def test_upgrade_is_noop_after_create_all(engine: Engine, alembic_cfg: Config):
    Base.metadata.create_all(bind=engine)
    command.stamp(alembic_cfg, _PARENT_REVISION)

    command.upgrade(alembic_cfg, _HEAD_REVISION)

    indexes = {index["name"] for index in sa.inspect(engine).get_indexes("api_tokens")}
    assert indexes == {"ix_api_tokens_user_id", "ix_api_tokens_token_hash"}


def test_upgrade_is_noop_on_empty_database(engine: Engine, alembic_cfg: Config):
    command.stamp(alembic_cfg, _PARENT_REVISION)

    command.upgrade(alembic_cfg, _HEAD_REVISION)

    assert "api_tokens" not in sa.inspect(engine).get_table_names()


def test_importing_any_model_registers_api_tokens():
    """Standalone create_all/drop_all callers (seed --reset) only import app.models.models.

    Runs in a fresh interpreter: this test process has already imported app.main.
    """
    script = (
        "import app.models.models\n"
        "from app.database.database import Base\n"
        "assert 'api_tokens' in Base.metadata.tables, sorted(Base.metadata.tables)\n"
    )

    result = subprocess.run([sys.executable, "-c", script], cwd=_BACKEND_ROOT, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
