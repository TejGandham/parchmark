"""
Integration tests for the backfill_valid_auth_credentials Alembic migration.
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
_PARENT_REVISION = "1b2c3d4e5f6a"
_HEAD_REVISION = "be7aafff4947"
_CONSTRAINT_NAME = "valid_auth_credentials"

# Schema state at 1b2c3d4e5f6a: users has no valid_auth_credentials CHECK yet
# (that gap is exactly what this migration backfills), notes and note_tags
# already exist.
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
def brownfield_migration_container() -> Iterator[tuple[Engine, Config]]:
    """Brownfield DB stamped at the parent revision, missing the CHECK."""
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


@pytest.fixture(scope="module")
def fresh_migration_container() -> Iterator[tuple[Engine, Config]]:
    """Fresh DB where Base.metadata.create_all() already produced the schema.

    Mirrors the app-startup order (init_db.create_tables() -> create_all())
    running ahead of a later `alembic upgrade head`, e.g. a local dev DB that
    was created via create_all before alembic was ever pointed at it. Stamp
    at the parent revision (rather than replaying the whole prior chain,
    already covered by other migration test modules) and upgrade only to
    this migration's head.
    """
    saved_database_url = os.environ.get("DATABASE_URL")
    with PostgresContainer("postgres:17") as pg:
        sync_url = pg.get_connection_url()
        os.environ["DATABASE_URL"] = sync_url

        try:
            engine = create_engine(sync_url)

            import app.models.models  # noqa: F401 — side-effect: registers ORM classes
            from app.database.database import Base

            with engine.begin() as conn:
                Base.metadata.create_all(bind=conn)

            alembic_cfg = Config(str(_ALEMBIC_INI))
            alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
            command.stamp(alembic_cfg, _PARENT_REVISION)

            yield engine, alembic_cfg
        finally:
            if saved_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = saved_database_url


def test_backfill_upgrade_creates_constraint_on_brownfield_db(
    brownfield_migration_container: tuple[Engine, Config],
):
    engine, alembic_cfg = brownfield_migration_container

    command.upgrade(alembic_cfg, _HEAD_REVISION)

    inspector = sa.inspect(engine)
    check_constraints = {constraint["name"] for constraint in inspector.get_check_constraints("users")}
    assert _CONSTRAINT_NAME in check_constraints


def test_backfill_constraint_rejects_invalid_local_row(
    brownfield_migration_container: tuple[Engine, Config],
):
    engine, alembic_cfg = brownfield_migration_container
    command.upgrade(alembic_cfg, _HEAD_REVISION)

    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO users (username, password_hash, auth_provider)
                    VALUES (:username, NULL, 'local')
                    """
                ),
                {"username": f"bad-local-{uuid.uuid4()}"},
            )


def test_backfill_constraint_rejects_invalid_oidc_row(
    brownfield_migration_container: tuple[Engine, Config],
):
    engine, alembic_cfg = brownfield_migration_container
    command.upgrade(alembic_cfg, _HEAD_REVISION)

    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO users (username, oidc_sub, auth_provider)
                    VALUES (:username, NULL, 'oidc')
                    """
                ),
                {"username": f"bad-oidc-{uuid.uuid4()}"},
            )


def test_backfill_constraint_accepts_valid_rows(
    brownfield_migration_container: tuple[Engine, Config],
):
    engine, alembic_cfg = brownfield_migration_container
    command.upgrade(alembic_cfg, _HEAD_REVISION)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO users (username, password_hash, auth_provider)
                VALUES (:username, 'hash', 'local')
                """
            ),
            {"username": f"good-local-{uuid.uuid4()}"},
        )
        conn.execute(
            text(
                """
                INSERT INTO users (username, oidc_sub, auth_provider)
                VALUES (:username, :oidc_sub, 'oidc')
                """
            ),
            {"username": f"good-oidc-{uuid.uuid4()}", "oidc_sub": str(uuid.uuid4())},
        )


def test_backfill_downgrade_drops_constraint(brownfield_migration_container: tuple[Engine, Config]):
    engine, alembic_cfg = brownfield_migration_container
    command.upgrade(alembic_cfg, _HEAD_REVISION)

    command.downgrade(alembic_cfg, _PARENT_REVISION)

    inspector = sa.inspect(engine)
    check_constraints = {constraint["name"] for constraint in inspector.get_check_constraints("users")}
    assert _CONSTRAINT_NAME not in check_constraints


def test_backfill_downgrade_is_noop_when_already_absent(brownfield_migration_container: tuple[Engine, Config]):
    """
    Self-contained: drives upgrade -> downgrade -> downgrade rather than relying
    on state left behind by another test function, since xdist's worksteal
    distribution may schedule each test in this module onto its own worker
    (and hence its own independent module-scoped fixture instance).
    """
    engine, alembic_cfg = brownfield_migration_container
    command.upgrade(alembic_cfg, _HEAD_REVISION)
    command.downgrade(alembic_cfg, _PARENT_REVISION)  # constraint now absent

    command.downgrade(alembic_cfg, _PARENT_REVISION)  # must not raise on an already-absent constraint

    inspector = sa.inspect(engine)
    check_constraints = {constraint["name"] for constraint in inspector.get_check_constraints("users")}
    assert _CONSTRAINT_NAME not in check_constraints


def test_backfill_upgrade_noop_on_fresh_db_with_create_all(fresh_migration_container: tuple[Engine, Config]):
    """
    Fresh DB: Base.metadata.create_all() already built valid_auth_credentials
    (declared in User.__table_args__). The migration's inspector guard must
    detect it and return early — no duplicate-constraint error, no duplicate
    constraint.
    """
    engine, alembic_cfg = fresh_migration_container

    command.upgrade(alembic_cfg, _HEAD_REVISION)  # must not raise

    inspector = sa.inspect(engine)
    check_constraints = inspector.get_check_constraints("users")
    matching = [constraint for constraint in check_constraints if constraint["name"] == _CONSTRAINT_NAME]
    assert len(matching) == 1
