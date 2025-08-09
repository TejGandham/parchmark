"""
Notes CRUD routes for ParchMark backend API.
Handles note creation, reading, updating, and deletion with user authorization.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import re
from datetime import datetime

from app.database.database import get_db
from app.models.models import User, Note
from app.schemas.schemas import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    DeleteResponse,
)
from app.auth.dependencies import get_current_user

# Create router for notes endpoints
router = APIRouter(prefix="/notes", tags=["notes"])


def extract_title_from_markdown(content: str) -> str:
    """
    Extract title from markdown content.
    Looks for the first H1 heading (# Title).
    Matches the frontend extractTitleFromMarkdown function.
    """
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return title_match.group(1).strip() if title_match else "Untitled Note"


def format_note_content(content: str) -> str:
    """
    Format note content to ensure proper structure.
    Matches the frontend formatNoteContent function.
    """
    cleaned_content = content.strip()
    title = extract_title_from_markdown(cleaned_content)

    # If content is only a title, ensure it has spacing for editing
    return f"# {title}\n\n" if cleaned_content == f"# {title}" else cleaned_content


def create_empty_note_content(title: str = "New Note") -> str:
    """
    Create a new empty note content template.
    Matches the frontend createEmptyNoteContent function.
    """
    return f"# {title}\n\n"


@router.get("/", response_model=List[NoteResponse])
async def get_notes(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get all notes for the authenticated user.

    Returns notes in the format expected by the frontend,
    with proper field mapping (createdAt/updatedAt).

    Args:
        current_user: Current authenticated user
        db: Database session dependency

    Returns:
        List[NoteResponse]: List of user's notes
    """
    # Query notes for the current user
    notes = db.query(Note).filter(Note.user_id == current_user.id).all()

    # Convert to response format with proper field mapping
    note_responses = []
    for note in notes:
        note_responses.append(
            NoteResponse(
                id=note.id,
                title=note.title,
                content=note.content,
                createdAt=note.created_at.isoformat(),
                updatedAt=note.updated_at.isoformat(),
            )
        )

    return note_responses


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new note for the authenticated user.

    Matches the frontend createNote operation:
    - Generates unique ID with timestamp
    - Extracts title from markdown content
    - Sets created and updated timestamps

    Args:
        note_data: Note creation data (title and content)
        current_user: Current authenticated user
        db: Database session dependency

    Returns:
        NoteResponse: The created note
    """
    # Generate unique ID similar to frontend (note-{timestamp})
    note_id = f"note-{int(datetime.now().timestamp() * 1000)}"

    # Format content and extract title
    formatted_content = format_note_content(note_data.content)
    extracted_title = extract_title_from_markdown(formatted_content)

    # Create new note
    db_note = Note(
        id=note_id,
        user_id=current_user.id,
        title=extracted_title,
        content=formatted_content,
    )

    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    return NoteResponse(
        id=db_note.id,
        title=db_note.title,
        content=db_note.content,
        createdAt=db_note.created_at.isoformat(),
        updatedAt=db_note.updated_at.isoformat(),
    )


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        db: Database session dependency

    Returns:
        NoteResponse: The updated note

    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    # Get the note and verify ownership
    db_note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == current_user.id)
        .first()
    )

    if not db_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    # Update fields if provided
    if note_data.content is not None:
        # Format content and extract title (matches frontend behavior)
        formatted_content = format_note_content(note_data.content)
        extracted_title = extract_title_from_markdown(formatted_content)

        db_note.content = formatted_content
        db_note.title = extracted_title
    elif note_data.title is not None:
        # If only title is provided, update it directly
        db_note.title = note_data.title

    db.commit()
    db.refresh(db_note)

    return NoteResponse(
        id=db_note.id,
        title=db_note.title,
        content=db_note.content,
        createdAt=db_note.created_at.isoformat(),
        updatedAt=db_note.updated_at.isoformat(),
    )


@router.delete("/{note_id}", response_model=DeleteResponse)
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a note for the authenticated user.

    Matches the frontend deleteNote operation:
    - Only allows users to delete their own notes
    - Returns confirmation of deletion

    Args:
        note_id: ID of the note to delete
        current_user: Current authenticated user
        db: Database session dependency

    Returns:
        DeleteResponse: Confirmation message with deleted note ID

    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    # Get the note and verify ownership
    db_note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == current_user.id)
        .first()
    )

    if not db_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    # Delete the note
    db.delete(db_note)
    db.commit()

    return DeleteResponse(message="Note deleted successfully", deleted_id=note_id)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific note for the authenticated user.

    Args:
        note_id: ID of the note to retrieve
        current_user: Current authenticated user
        db: Database session dependency

    Returns:
        NoteResponse: The requested note

    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    # Get the note and verify ownership
    db_note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == current_user.id)
        .first()
    )

    if not db_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    return NoteResponse(
        id=db_note.id,
        title=db_note.title,
        content=db_note.content,
        createdAt=db_note.created_at.isoformat(),
        updatedAt=db_note.updated_at.isoformat(),
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

