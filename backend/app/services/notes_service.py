"""Notes CRUD orchestration business logic.

Holds the notes create/update/delete/list orchestration, note-id generation,
ORM-to-schema conversion, ownership checks, and SQLAlchemyError rollback
handling. Routers delegate to these module-level functions, mirroring
``settings_service``. The note-events SSE stream and broker wiring stay in the
router.
"""

import logging
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Note, NoteTag, User
from app.schemas.schemas import (
    DeleteResponse,
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)
from app.utils.markdown import markdown_service

logger = logging.getLogger(__name__)


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


async def list_notes(db: AsyncSession, current_user: User) -> list[NoteResponse]:
    """Return all notes for the authenticated user as response schemas."""
    result = await db.execute(select(Note).options(selectinload(Note.tags)).filter(Note.user_id == current_user.id))
    notes = result.scalars().all()

    return [_note_to_response(note) for note in notes]


async def create_note(db: AsyncSession, current_user: User, note_data: NoteCreate) -> NoteResponse:
    """Create a new note for the authenticated user.

    Generates a unique ID, uses the client-provided title if given (otherwise
    extracts the H1 from content), persists the note, and returns it.
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


async def update_note(db: AsyncSession, current_user: User, note_id: str, note_data: NoteUpdate) -> NoteResponse:
    """Update an existing note owned by the authenticated user.

    Raises:
        HTTPException: 404 if the note is not found or not owned by the user.
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


async def delete_note(db: AsyncSession, current_user: User, note_id: str) -> DeleteResponse:
    """Delete a note owned by the authenticated user.

    Raises:
        HTTPException: 404 if the note is not found or not owned by the user.
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


async def get_note(db: AsyncSession, current_user: User, note_id: str) -> NoteResponse:
    """Return a specific note owned by the authenticated user.

    Raises:
        HTTPException: 404 if the note is not found or not owned by the user.
    """
    # Get the note and verify ownership
    db_note = await _get_owned_note(db, current_user.id, note_id)  # type: ignore[arg-type]

    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    return _note_to_response(db_note)
