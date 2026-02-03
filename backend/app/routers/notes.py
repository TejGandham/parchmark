"""
Notes CRUD routes for ParchMark backend API.
Handles note creation, reading, updating, and deletion with user authorization.
This router is a thin controller that delegates business logic to NoteService.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import User
from app.schemas.schemas import (
    DeleteResponse,
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)
from app.services.note_service import (
    CreateNoteInput,
    NoteNotFoundError,
    NoteService,
    NoteServiceError,
    UpdateNoteInput,
)

logger = logging.getLogger(__name__)

# Create router for notes endpoints
router = APIRouter(prefix="/notes", tags=["notes"])


def get_note_service(db: AsyncSession = Depends(get_async_db)) -> NoteService:
    """Dependency to get NoteService instance."""
    return NoteService(db)


def _note_to_response(note) -> NoteResponse:
    """Convert a Note model to NoteResponse schema."""
    return NoteResponse.model_validate(
        {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "createdAt": note.created_at.isoformat(),
            "updatedAt": note.updated_at.isoformat(),
        }
    )


@router.get("/", response_model=list[NoteResponse])
async def get_notes(
    current_user: User = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """
    Get all notes for the authenticated user.

    Returns notes in the format expected by the frontend,
    with proper field mapping (createdAt/updatedAt).

    Args:
        current_user: Current authenticated user
        service: NoteService instance

    Returns:
        List[NoteResponse]: List of user's notes
    """
    notes = await service.get_notes_by_user(current_user.id)
    return [_note_to_response(note) for note in notes]


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
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
        service: NoteService instance

    Returns:
        NoteResponse: The created note
    """
    try:
        input_data = CreateNoteInput(content=note_data.content, title=note_data.title)
        note = await service.create_note(current_user.id, input_data)
        return _note_to_response(note)
    except NoteServiceError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
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
        service: NoteService instance

    Returns:
        NoteResponse: The updated note

    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    try:
        input_data = UpdateNoteInput(content=note_data.content, title=note_data.title)
        note = await service.update_note(note_id, current_user.id, input_data)
        return _note_to_response(note)
    except NoteNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found") from None
    except NoteServiceError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None


@router.delete("/{note_id}", response_model=DeleteResponse)
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """
    Delete a note for the authenticated user.

    Matches the frontend deleteNote operation:
    - Only allows users to delete their own notes
    - Returns confirmation of deletion

    Args:
        note_id: ID of the note to delete
        current_user: Current authenticated user
        service: NoteService instance

    Returns:
        DeleteResponse: Confirmation message with deleted note ID

    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    try:
        deleted_id = await service.delete_note(note_id, current_user.id)
        return DeleteResponse(message="Note deleted successfully", deleted_id=deleted_id)
    except NoteNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found") from None
    except NoteServiceError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error") from None


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """
    Get a specific note for the authenticated user.

    Args:
        note_id: ID of the note to retrieve
        current_user: Current authenticated user
        service: NoteService instance

    Returns:
        NoteResponse: The requested note

    Raises:
        HTTPException: 404 if note not found or not owned by user
    """
    try:
        note = await service.get_note_by_id(note_id, current_user.id)
        return _note_to_response(note)
    except NoteNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found") from None


# Health check endpoint for notes service
@router.get("/health/check")
async def notes_health_check():
    """
    Health check endpoint for notes service.

    Returns:
        dict: Status message indicating notes service is operational
    """
    return {"status": "Notes service is healthy"}
