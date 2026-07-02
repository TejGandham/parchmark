"""
Notes CRUD routes for ParchMark backend API.
Handles note creation, reading, updating, and deletion with user authorization.

The CRUD business logic lives in ``app.services.notes_service``; this router is
dependency wiring plus service calls. The note-events SSE stream and its broker
wiring stay here.
"""

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import credentials_exception
from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import User
from app.schemas.schemas import (
    DeleteResponse,
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)
from app.services import notes_service
from app.services.note_event_streams import (
    NOTE_EVENTS_HEARTBEAT_FRAME,
    NOTE_EVENTS_HEARTBEAT_INTERVAL_SECONDS,
    note_event_stream_manager,
)
from app.services.note_events import note_event_broker

# Create router for notes endpoints
router = APIRouter(prefix="/notes", tags=["notes"])
note_events_security = HTTPBearer(auto_error=False)


async def get_current_user_for_note_events(
    credentials: HTTPAuthorizationCredentials | None = Depends(note_events_security),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """Authenticate note-event streams with a 401 for missing bearer credentials."""
    if credentials is None:
        raise credentials_exception
    return await get_current_user(credentials, db)


async def _note_events_sse_stream(
    user_id: int,
    request: Request,
    heartbeat_interval_seconds: float = NOTE_EVENTS_HEARTBEAT_INTERVAL_SECONDS,
) -> AsyncIterator[str]:
    subscriber = note_event_broker.subscribe(user_id=user_id)
    note_event_stream_manager.register(subscriber)
    try:
        while not subscriber.closed and not note_event_stream_manager.is_closing:
            if await request.is_disconnected():
                break

            event_task = asyncio.create_task(subscriber.queue.get())
            shutdown_task = asyncio.create_task(note_event_stream_manager.shutdown_event().wait())
            try:
                done, _ = await asyncio.wait(
                    {event_task, shutdown_task},
                    timeout=heartbeat_interval_seconds,
                    return_when=asyncio.FIRST_COMPLETED,
                )
            finally:
                pending_tasks = [task for task in (event_task, shutdown_task) if not task.done()]
                for task in pending_tasks:
                    task.cancel()
                if pending_tasks:
                    await asyncio.gather(*pending_tasks, return_exceptions=True)

            if shutdown_task in done or note_event_stream_manager.is_closing:
                break

            if event_task in done:
                event = event_task.result()
                data = json.dumps({"kind": event.kind, "note_id": event.note_id})
                yield f"data: {data}\n\n"
                continue

            if await request.is_disconnected():
                break

            yield NOTE_EVENTS_HEARTBEAT_FRAME
    finally:
        note_event_stream_manager.unregister(subscriber)
        note_event_broker.unsubscribe(subscriber)


@router.get("/", response_model=list[NoteResponse])
async def get_notes(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    """
    Get all notes for the authenticated user.

    Returns notes in the format expected by the frontend,
    with proper field mapping (createdAt/updatedAt).

    Args:
        current_user: Current authenticated user
        db: Async database session dependency

    Returns:
        List[NoteResponse]: List of user's notes
    """
    return await notes_service.list_notes(db, current_user)


@router.get("/events", status_code=status.HTTP_200_OK)
async def stream_note_events(
    request: Request,
    current_user: User = Depends(get_current_user_for_note_events),
):
    """Stream authenticated note-change events as Server-Sent Events."""
    return StreamingResponse(
        _note_events_sse_stream(user_id=current_user.id, request=request),  # type: ignore[arg-type]
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new note for the authenticated user.

    Matches the frontend createNote operation:
    - Generates unique ID with timestamp
    - Uses client-provided title if given, otherwise extracts from content H1
    - Sets created and updated timestamps

    Args:
        note_data: Note creation data (content required, title optional)
        current_user: Current authenticated user
        db: Async database session dependency

    Returns:
        NoteResponse: The created note
    """
    return await notes_service.create_note(db, current_user, note_data)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update an existing note for the authenticated user.

    Matches the frontend updateNote operation:
    - Extracts title from markdown content
    - Updates the updatedAt timestamp
    - Only allows users to update their own notes

    Args:
        note_id: ID of the note to update
        note_data: Note update data (title and/or content)
        current_user: Current authenticated user
        db: Async database session dependency

    Returns:
        NoteResponse: The updated note

    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    return await notes_service.update_note(db, current_user, note_id, note_data)


@router.delete("/{note_id}", response_model=DeleteResponse)
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete a note for the authenticated user.

    Matches the frontend deleteNote operation:
    - Only allows users to delete their own notes
    - Returns confirmation of deletion

    Args:
        note_id: ID of the note to delete
        current_user: Current authenticated user
        db: Async database session dependency

    Returns:
        DeleteResponse: Confirmation message with deleted note ID

    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    return await notes_service.delete_note(db, current_user, note_id)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get a specific note for the authenticated user.

    Args:
        note_id: ID of the note to retrieve
        current_user: Current authenticated user
        db: Async database session dependency

    Returns:
        NoteResponse: The requested note

    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    return await notes_service.get_note(db, current_user, note_id)


@router.get("/health/check")
async def notes_health_check():
    return {"status": "Notes service is healthy"}
