import asyncio
import contextlib
import json
import os
import socket
import threading
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
import uvicorn
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from app.auth.auth import create_access_token
from app.database.database import Base, get_async_db
from app.routers import notes as notes_router
from app.services.note_event_streams import NoteEventStreamManager
from app.services.note_events import NoteEventBroker, PostgresNoteEventListener

_BACKEND_ROOT = Path(__file__).parents[3]
_ALEMBIC_INI = _BACKEND_ROOT / "alembic.ini"
_F33_LEAK_WINDOW_SECONDS = 5


@dataclass
class _F33Database:
    sync_url: str
    engine: Engine
    async_session_factory: async_sessionmaker[AsyncSession]


class _UvicornThread:
    def __init__(self, app: FastAPI):
        self.app = app
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.listen(5)
        host, port = self.socket.getsockname()
        self.base_url = f"http://{host}:{port}"
        self.config = uvicorn.Config(
            app,
            host=host,
            port=port,
            lifespan="on",
            log_level="warning",
        )
        self.server = uvicorn.Server(self.config)
        self.thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self):
        self.thread.start()
        deadline = time.monotonic() + 10
        while not self.server.started and self.thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)

        if not self.server.started:
            self.server.should_exit = True
            self.thread.join(timeout=5)
            raise RuntimeError("Timed out waiting for test server startup")

        return self

    def __exit__(self, exc_type, exc, traceback):
        self.server.should_exit = True
        self.thread.join(timeout=10)
        if self.thread.is_alive():
            raise RuntimeError("Timed out waiting for test server shutdown")

    def _run(self):
        asyncio.run(self.server.serve(sockets=[self.socket]))


@pytest.fixture(scope="module")
def f33_database() -> Iterator[_F33Database]:
    saved_db_url = os.environ.get("DATABASE_URL")
    with PostgresContainer("postgres:17") as pg:
        sync_url = pg.get_connection_url()
        os.environ["DATABASE_URL"] = sync_url
        engine = create_engine(sync_url)
        async_engine = create_async_engine(
            sync_url.replace("postgresql://", "postgresql+asyncpg://").replace(
                "postgresql+psycopg2://",
                "postgresql+asyncpg://",
            ),
            poolclass=NullPool,
        )
        async_session_factory = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        try:
            with engine.begin() as conn:
                Base.metadata.create_all(bind=conn)

            alembic_cfg = Config(str(_ALEMBIC_INI))
            alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
            command.stamp(alembic_cfg, "7f1c343772e8")
            command.upgrade(alembic_cfg, "head")

            yield _F33Database(
                sync_url=sync_url,
                engine=engine,
                async_session_factory=async_session_factory,
            )
        finally:
            asyncio.run(async_engine.dispose())
            engine.dispose()
            if saved_db_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = saved_db_url


def _create_user(engine: Engine, username: str) -> int:
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


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': username})}"}


@contextlib.contextmanager
def _patched_note_event_services(broker: NoteEventBroker, stream_manager: NoteEventStreamManager):
    original_broker = notes_router.note_event_broker
    original_stream_manager = notes_router.note_event_stream_manager
    notes_router.note_event_broker = broker
    notes_router.note_event_stream_manager = stream_manager
    try:
        yield
    finally:
        notes_router.note_event_broker = original_broker
        notes_router.note_event_stream_manager = original_stream_manager


def _build_app(database: _F33Database, broker: NoteEventBroker, stream_manager: NoteEventStreamManager) -> FastAPI:
    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        stream_manager.open()
        listener = PostgresNoteEventListener(dsn=database.sync_url, broker=broker)
        await listener.start()
        try:
            yield
        finally:
            await stream_manager.close_all()
            await listener.stop()

    async def override_get_async_db():
        async with database.async_session_factory() as session:
            yield session

    app = FastAPI(lifespan=lifespan)
    app.dependency_overrides[get_async_db] = override_get_async_db
    app.include_router(notes_router.router, prefix="/api")
    return app


async def _wait_for_stream_registration(broker: NoteEventBroker, user_id: int) -> None:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if broker.subscriber_count(user_id) == 1:
            return
        await asyncio.sleep(0.01)
    raise AssertionError("user B's note-event stream did not register with the broker")


async def _read_sse_events(line_iterator, event_queue: asyncio.Queue[dict[str, str]]) -> None:
    async for line in line_iterator:
        if not line.startswith("data: "):
            continue
        event_queue.put_nowait(json.loads(line.removeprefix("data: ")))


async def _post_note(client: httpx.AsyncClient, headers: dict[str, str], title: str) -> str:
    await asyncio.sleep(0.002)
    response = await client.post(
        "/api/notes/",
        headers=headers,
        json={"title": title, "content": f"# {title}\n\nF33 isolation test content."},
    )
    assert response.status_code == 200
    note_id = response.json()["id"]
    assert isinstance(note_id, str)
    return note_id


async def _patch_note(client: httpx.AsyncClient, headers: dict[str, str], note_id: str, title: str) -> None:
    response = await client.put(
        f"/api/notes/{note_id}",
        headers=headers,
        json={"content": f"# {title}\n\nUpdated by F33 isolation test."},
    )
    assert response.status_code == 200


async def _delete_note(client: httpx.AsyncClient, headers: dict[str, str], note_id: str) -> None:
    response = await client.delete(f"/api/notes/{note_id}", headers=headers)
    assert response.status_code == 200


async def _perform_ten_user_a_mutations(client: httpx.AsyncClient, headers: dict[str, str]) -> None:
    first_note_id = await _post_note(client, headers, "F33 user A note 1")
    await _patch_note(client, headers, first_note_id, "F33 user A note 1 patched")
    second_note_id = await _post_note(client, headers, "F33 user A note 2")
    await _delete_note(client, headers, first_note_id)
    await _patch_note(client, headers, second_note_id, "F33 user A note 2 patched")
    third_note_id = await _post_note(client, headers, "F33 user A note 3")
    await _delete_note(client, headers, second_note_id)
    await _patch_note(client, headers, third_note_id, "F33 user A note 3 patched")
    await _post_note(client, headers, "F33 user A note 4")
    await _delete_note(client, headers, third_note_id)


@pytest.mark.asyncio
async def test_note_event_stream_does_not_leak_events_between_users(f33_database: _F33Database):
    user_a_name = f"f33-user-a-{uuid.uuid4()}"
    user_b_name = f"f33-user-b-{uuid.uuid4()}"
    _create_user(f33_database.engine, user_a_name)
    user_b_id = _create_user(f33_database.engine, user_b_name)

    broker = NoteEventBroker()
    stream_manager = NoteEventStreamManager()
    app = _build_app(f33_database, broker, stream_manager)

    with _patched_note_event_services(broker, stream_manager), _UvicornThread(app) as server:
        async with httpx.AsyncClient(
            base_url=server.base_url,
            timeout=httpx.Timeout(10.0, read=None),
        ) as client:
            user_a_headers = _auth_headers(user_a_name)
            user_b_headers = _auth_headers(user_b_name)

            async with client.stream("GET", "/api/notes/events", headers=user_b_headers) as stream:
                assert stream.status_code == 200
                assert stream.headers["content-type"].startswith("text/event-stream")
                event_queue: asyncio.Queue[dict[str, str]] = asyncio.Queue()
                reader_task = asyncio.create_task(_read_sse_events(stream.aiter_lines(), event_queue))
                try:
                    await _wait_for_stream_registration(broker, user_b_id)

                    await _perform_ten_user_a_mutations(client, user_a_headers)
                    await asyncio.sleep(_F33_LEAK_WINDOW_SECONDS)
                    assert event_queue.empty()

                    user_b_note_id = await _post_note(client, user_b_headers, "F33 user B control note")
                    control_event = await asyncio.wait_for(event_queue.get(), timeout=2)

                    assert control_event == {"kind": "created", "note_id": user_b_note_id}
                    assert event_queue.empty()
                finally:
                    reader_task.cancel()
                    await asyncio.gather(reader_task, return_exceptions=True)
