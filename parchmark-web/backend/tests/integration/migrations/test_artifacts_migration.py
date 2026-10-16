"""
Integration tests for the artifacts Alembic migration.

Covers a brownfield DB stamped at the parent revision (tables created with the
same schema create_all produces, constraints and cascades enforced, downgrade
drops them) and a fresh DB where create_all already produced the schema
(upgrade is a no-op).
"""

import os
import subprocess
import sys
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
_PARENT_REVISION = "dba02717ee2f"
_HEAD_REVISION = "7dc2de38f032"
_TABLES = ("artifacts", "artifact_versions")

# Schema state at dba02717ee2f: users (with valid_auth_credentials), notes, note_tags, api_tokens.
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

CREATE TABLE api_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
CREATE INDEX ix_api_tokens_user_id ON api_tokens(user_id);
CREATE UNIQUE INDEX ix_api_tokens_token_hash ON api_tokens(token_hash);
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
    _reset_schema(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def alembic_cfg(migration_container: str) -> Config:
    alembic_cfg = Config(str(_ALEMBIC_INI))
    alembic_cfg.set_main_option("sqlalchemy.url", migration_container)
    return alembic_cfg


@pytest.fixture
def brownfield(engine: Engine, alembic_cfg: Config) -> tuple[Engine, Config]:
    """A DB at the parent revision, before artifacts existed."""
    with engine.begin() as conn:
        for statement in _PARENT_SCHEMA_SQL.strip().split(";"):
            sql = statement.strip()
            if sql:
                conn.execute(text(sql))
    command.stamp(alembic_cfg, _PARENT_REVISION)
    return engine, alembic_cfg


def _reset_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


def _artifact_schema(engine: Engine) -> dict[str, dict[str, list[tuple]]]:
    """Columns, indexes and constraints of the artifact tables, in a comparable form."""
    inspector = sa.inspect(engine)
    return {
        table: {
            "columns": sorted(
                (c["name"], str(c["type"]), c["nullable"], c.get("default")) for c in inspector.get_columns(table)
            ),
            "indexes": sorted((i["name"], tuple(i["column_names"]), i["unique"]) for i in inspector.get_indexes(table)),
            "unique": sorted((u["name"], tuple(u["column_names"])) for u in inspector.get_unique_constraints(table)),
            "checks": sorted((c["name"], c["sqltext"]) for c in inspector.get_check_constraints(table)),
            "foreign_keys": sorted(
                (f["name"], tuple(f["constrained_columns"]), f["referred_table"], f["options"].get("ondelete"))
                for f in inspector.get_foreign_keys(table)
            ),
        }
        for table in _TABLES
    }


def _insert_artifact(conn: sa.Connection, user_id: int, slug: str) -> tuple[int, int]:
    """Insert an artifact with version 1 made current; return (artifact_id, version_id)."""
    artifact_id = conn.execute(
        text(
            "INSERT INTO artifacts (owner_id, slug, title, visibility) VALUES (:owner, :slug, 'T', 'private') RETURNING id"
        ),
        {"owner": user_id, "slug": slug},
    ).scalar_one()
    version_id = conn.execute(
        text(
            "INSERT INTO artifact_versions (artifact_id, version, content_type, content) "
            "VALUES (:artifact_id, 1, 'html', '<p>x</p>') RETURNING id"
        ),
        {"artifact_id": artifact_id},
    ).scalar_one()
    conn.execute(
        text("UPDATE artifacts SET current_version_id = :version_id WHERE id = :artifact_id"),
        {"version_id": version_id, "artifact_id": artifact_id},
    )
    return artifact_id, version_id


def test_upgrade_matches_the_create_all_schema(brownfield: tuple[Engine, Config]):
    engine, alembic_cfg = brownfield
    command.upgrade(alembic_cfg, _HEAD_REVISION)
    migrated = _artifact_schema(engine)

    _reset_schema(engine)
    Base.metadata.create_all(bind=engine)

    assert migrated == _artifact_schema(engine)
    assert "fk_artifacts_current_version_id" in {fk[0] for fk in migrated["artifacts"]["foreign_keys"]}


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO artifact_versions (artifact_id, version, content_type, content) "
        "VALUES (:artifact_id, 1, 'html', 'duplicate number')",
        "INSERT INTO artifact_versions (artifact_id, version, content_type, content) "
        "VALUES (:artifact_id, 2, 'pdf', 'unsupported type')",
        "INSERT INTO artifact_versions (artifact_id, version, content_type, content) "
        "VALUES (:artifact_id, 0, 'svg', 'version numbers start at 1')",
        "UPDATE artifacts SET visibility = 'public' WHERE id = :artifact_id",
        "UPDATE artifacts SET current_version_id = 999999 WHERE id = :artifact_id",
        "INSERT INTO artifacts (owner_id, slug, title, visibility) "
        "SELECT owner_id, slug, 'same slug', 'private' FROM artifacts WHERE id = :artifact_id",
    ],
    ids=["duplicate-version", "content-type", "version-zero", "visibility", "dangling-current", "duplicate-slug"],
)
def test_constraints_reject_invalid_rows(brownfield: tuple[Engine, Config], statement: str):
    engine, alembic_cfg = brownfield
    command.upgrade(alembic_cfg, _HEAD_REVISION)
    with engine.begin() as conn:
        user_id = conn.execute(
            text("INSERT INTO users (username, password_hash) VALUES ('owner', 'hash') RETURNING id")
        ).scalar_one()
        artifact_id, _version_id = _insert_artifact(conn, user_id, "slug-one")

    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(text(statement), {"artifact_id": artifact_id})


def test_deleting_the_owner_cascades_to_artifacts_and_versions(brownfield: tuple[Engine, Config]):
    engine, alembic_cfg = brownfield
    command.upgrade(alembic_cfg, _HEAD_REVISION)
    with engine.begin() as conn:
        user_id = conn.execute(
            text("INSERT INTO users (username, password_hash) VALUES ('owner', 'hash') RETURNING id")
        ).scalar_one()
        _insert_artifact(conn, user_id, "slug-one")
        _insert_artifact(conn, user_id, "slug-two")

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
        remaining = conn.execute(
            text("SELECT (SELECT count(*) FROM artifacts) + (SELECT count(*) FROM artifact_versions)")
        ).scalar_one()

    assert remaining == 0


def test_downgrade_drops_tables(brownfield: tuple[Engine, Config]):
    engine, alembic_cfg = brownfield
    command.upgrade(alembic_cfg, _HEAD_REVISION)

    command.downgrade(alembic_cfg, _PARENT_REVISION)
    command.downgrade(alembic_cfg, _PARENT_REVISION)  # already at parent: must not raise

    assert not set(_TABLES) & set(sa.inspect(engine).get_table_names())


def test_upgrade_is_noop_after_create_all(engine: Engine, alembic_cfg: Config):
    Base.metadata.create_all(bind=engine)
    expected = _artifact_schema(engine)
    command.stamp(alembic_cfg, _PARENT_REVISION)

    command.upgrade(alembic_cfg, _HEAD_REVISION)

    assert _artifact_schema(engine) == expected


def test_upgrade_is_noop_on_empty_database(engine: Engine, alembic_cfg: Config):
    command.stamp(alembic_cfg, _PARENT_REVISION)

    command.upgrade(alembic_cfg, _HEAD_REVISION)

    assert not set(_TABLES) & set(sa.inspect(engine).get_table_names())


def test_drop_all_breaks_the_foreign_key_cycle(engine: Engine):
    """seed --reset runs drop_all then create_all; the artifacts <-> artifact_versions cycle must not block it."""
    Base.metadata.create_all(bind=engine)

    Base.metadata.drop_all(bind=engine)

    assert sa.inspect(engine).get_table_names() == []


def test_importing_any_model_registers_artifact_tables():
    """Standalone create_all/drop_all callers (seed --reset) only import app.models.models.

    Runs in a fresh interpreter: this test process has already imported app.main.
    """
    script = (
        "import app.models.models\n"
        "from app.database.database import Base\n"
        f"assert set({_TABLES!r}) <= set(Base.metadata.tables), sorted(Base.metadata.tables)\n"
    )

    result = subprocess.run([sys.executable, "-c", script], cwd=_BACKEND_ROOT, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
