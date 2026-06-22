"""
Notes CRUD routes for ParchMark backend API.
Handles note creation, reading, updating, and deletion with user authorization.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.auth import credentials_exception
from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import Note, NoteTag, User
from app.schemas.schemas import (
    DeleteResponse,
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)
from app.services.note_event_streams import (
    NOTE_EVENTS_HEARTBEAT_FRAME,
    NOTE_EVENTS_HEARTBEAT_INTERVAL_SECONDS,
    note_event_stream_manager,
)
from app.services.note_events import note_event_broker
from app.utils.markdown import markdown_service

logger = logging.getLogger(__name__)

# Create router for notes endpoints
router = APIRouter(prefix="/notes", tags=["notes"])
note_events_security = HTTPBearer(auto_error=False)


def _note_to_response(note: Note) -> NoteResponse:
    """Convert a Note ORM model to a NoteResponse schema."""
    return NoteResponse.model_validate(
        {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "tags": sorted(tag.tag for tag in note.tags),
            "createdAt": note.created_at.isoformat(),
            "updatedAt": note.updated_at.isoformat(),
        }
    )


def _replace_note_tags(note: Note, tags: list[str]) -> None:
    """Replace a note's complete normalized tag set."""
    current_tags = {note_tag.tag: note_tag for note_tag in note.tags}
    note.tags = [current_tags.get(tag) or NoteTag(tag=tag) for tag in tags]


async def _get_owned_note(db: AsyncSession, user_id: int, note_id: str) -> Note | None:
    result = await db.execute(
        select(Note).options(selectinload(Note.tags)).filter(Note.id == note_id, Note.user_id == user_id)
    )
    return result.scalar_one_or_none()


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
    # Query notes for the current user
    result = await db.execute(select(Note).options(selectinload(Note.tags)).filter(Note.user_id == current_user.id))
    notes = result.scalars().all()

    return [_note_to_response(note) for note in notes]


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
    # Generate unique ID similar to frontend (note-{timestamp})
    note_id = f"note-{int(datetime.now().timestamp() * 1000)}"

    # Format content
    formatted_content = markdown_service.format_content(note_data.content)

    # Use client-provided title if given (and not whitespace-only), otherwise extract from content
    if note_data.title and note_data.title.strip():
        title = note_data.title.strip()
    else:
        title = markdown_service.extract_title(formatted_content)

    # Create new note
    db_note = Note(
        id=note_id,
        user_id=current_user.id,
        title=title,
        content=formatted_content,
    )
    if note_data.tags is not None:
        _replace_note_tags(db_note, note_data.tags)

    try:
        db.add(db_note)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Failed to create note: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None

    try:
        created_note = await _get_owned_note(db, current_user.id, note_id)  # type: ignore[arg-type]
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Failed to load created note {note_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None
    if created_note is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    return _note_to_response(created_note)


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
    # Get the note and verify ownership
    db_note = await _get_owned_note(db, current_user.id, note_id)  # type: ignore[arg-type]

    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    # Update fields if provided
    if note_data.content is not None:
        formatted_content = markdown_service.format_content(note_data.content)
        extracted_title = markdown_service.extract_title(formatted_content)

        db_note.content = formatted_content  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue]
        db_note.title = extracted_title  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue]
    elif note_data.title is not None:
        # If only title is provided, update it directly
        db_note.title = note_data.title  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue]

    if "tags" in note_data.model_fields_set and note_data.tags is not None:
        _replace_note_tags(db_note, note_data.tags)

    try:
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Failed to update note {note_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None

    try:
        updated_note = await _get_owned_note(db, current_user.id, note_id)  # type: ignore[arg-type]
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Failed to load updated note {note_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None
    if updated_note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return _note_to_response(updated_note)


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
    # Get the note and verify ownership
    db_note = await _get_owned_note(db, current_user.id, note_id)  # type: ignore[arg-type]

    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    # Delete the note
    try:
        await db.delete(db_note)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Failed to delete note {note_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None

    return DeleteResponse(message="Note deleted successfully", deleted_id=note_id)


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
    # Get the note and verify ownership
    db_note = await _get_owned_note(db, current_user.id, note_id)  # type: ignore[arg-type]

    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    return _note_to_response(db_note)


@router.get("/health/check")
async def notes_health_check():
    return {"status": "Notes service is healthy"}
