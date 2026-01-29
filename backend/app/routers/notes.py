"""
Notes CRUD routes for ParchMark backend API.
Handles note creation, reading, updating, and deletion with user authorization.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import Note, User
from app.schemas.schemas import (
    DeleteResponse,
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)
from app.utils.markdown import markdown_service

logger = logging.getLogger(__name__)

# Create router for notes endpoints
router = APIRouter(prefix="/notes", tags=["notes"])


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
    result = await db.execute(select(Note).filter(Note.user_id == current_user.id))
    notes = result.scalars().all()

    # Convert to response format using Pydantic's model_validate
    note_responses = []
    for note in notes:
        # Create a dict with proper field mapping for Pydantic
        note_dict = {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "createdAt": note.created_at.isoformat(),
            "updatedAt": note.updated_at.isoformat(),
        }
        note_responses.append(NoteResponse.model_validate(note_dict))

    return note_responses


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

    try:
        db.add(db_note)
        await db.commit()
        await db.refresh(db_note)
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Failed to create note: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None

    return NoteResponse.model_validate(
        {
            "id": db_note.id,
            "title": db_note.title,
            "content": db_note.content,
            "createdAt": db_note.created_at.isoformat(),
            "updatedAt": db_note.updated_at.isoformat(),
        }
    )


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
    result = await db.execute(select(Note).filter(Note.id == note_id, Note.user_id == current_user.id))
    db_note = result.scalar_one_or_none()

    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    # Update fields if provided
    if note_data.content is not None:
        # Format content and extract title (matches frontend behavior)
        formatted_content = markdown_service.format_content(note_data.content)
        extracted_title = markdown_service.extract_title(formatted_content)

        db_note.content = formatted_content  # type: ignore[assignment]
        db_note.title = extracted_title  # type: ignore[assignment]
    elif note_data.title is not None:
        # If only title is provided, update it directly
        db_note.title = note_data.title  # type: ignore[assignment]

    try:
        await db.commit()
        await db.refresh(db_note)
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Failed to update note {note_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None

    return NoteResponse.model_validate(
        {
            "id": db_note.id,
            "title": db_note.title,
            "content": db_note.content,
            "createdAt": db_note.created_at.isoformat(),
            "updatedAt": db_note.updated_at.isoformat(),
        }
    )


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
    result = await db.execute(select(Note).filter(Note.id == note_id, Note.user_id == current_user.id))
    db_note = result.scalar_one_or_none()

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
    result = await db.execute(select(Note).filter(Note.id == note_id, Note.user_id == current_user.id))
    db_note = result.scalar_one_or_none()

    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    return NoteResponse.model_validate(
        {
            "id": db_note.id,
            "title": db_note.title,
            "content": db_note.content,
            "createdAt": db_note.created_at.isoformat(),
            "updatedAt": db_note.updated_at.isoformat(),
        }
    )


# Health check endpoint for notes service
@router.get("/health/check")
async def notes_health_check():
    """
    Health check endpoint for notes service.

    Returns:
        dict: Status message indicating notes service is operational
    """
    return {"status": "Notes service is healthy"}
