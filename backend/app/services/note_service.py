"""
Note service for business logic related to note operations.
Extracts business logic from routers for better testability and reusability.

This service is a singleton - it uses contextvars to access the request-scoped
database session without requiring it to be passed as a parameter.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database.context import get_db
from app.models.models import Note
from app.utils.markdown import markdown_service

logger = logging.getLogger(__name__)


class NoteNotFoundError(Exception):
    """Raised when a note is not found or not accessible by the user."""

    def __init__(self, note_id: str):
        self.note_id = note_id
        super().__init__(f"Note not found: {note_id}")


class NoteServiceError(Exception):
    """Raised when a database operation fails."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(message)


@dataclass
class CreateNoteInput:
    """Input data for creating a note."""

    content: str
    title: str | None = None


@dataclass
class UpdateNoteInput:
    """Input data for updating a note."""

    content: str | None = None
    title: str | None = None


class NoteService:
    """
    Service for note-related business logic.

    Handles note creation, retrieval, update, and deletion with proper
    business rules applied (title extraction, content formatting, etc.).

    This is a singleton service - database session is obtained from context
    for each operation, ensuring request isolation.
    """

    @staticmethod
    def generate_note_id() -> str:
        """Generate a unique note ID using timestamp."""
        return f"note-{int(datetime.now().timestamp() * 1000)}"

    @staticmethod
    def process_note_content(content: str, title: str | None = None) -> tuple[str, str]:
        """
        Process note content and extract/determine title.

        Args:
            content: Raw markdown content.
            title: Optional explicit title. If not provided, extracts from content.

        Returns:
            Tuple of (formatted_content, title).
        """
        formatted_content = markdown_service.format_content(content)

        if title and title.strip():
            final_title = title.strip()
        else:
            final_title = markdown_service.extract_title(formatted_content)

        return formatted_content, final_title

    async def get_notes_by_user(self, user_id: int) -> list[Note]:
        """
        Get all notes for a specific user.

        Args:
            user_id: ID of the user whose notes to retrieve.

        Returns:
            List of Note objects belonging to the user.
        """
        db = get_db()
        result = await db.execute(select(Note).filter(Note.user_id == user_id))
        return list(result.scalars().all())

    async def get_note_by_id(self, note_id: str, user_id: int) -> Note:
        """
        Get a specific note by ID, ensuring it belongs to the user.

        Args:
            note_id: ID of the note to retrieve.
            user_id: ID of the user (for ownership verification).

        Returns:
            The Note object.

        Raises:
            NoteNotFoundError: If note doesn't exist or doesn't belong to user.
        """
        db = get_db()
        result = await db.execute(select(Note).filter(Note.id == note_id, Note.user_id == user_id))
        note = result.scalar_one_or_none()

        if not note:
            raise NoteNotFoundError(note_id)

        return note

    async def create_note(self, user_id: int, input_data: CreateNoteInput) -> Note:
        """
        Create a new note for a user.

        Args:
            user_id: ID of the user creating the note.
            input_data: Note creation data (content and optional title).

        Returns:
            The created Note object.

        Raises:
            NoteServiceError: If database operation fails.
        """
        db = get_db()
        note_id = self.generate_note_id()
        formatted_content, title = self.process_note_content(input_data.content, input_data.title)

        note = Note(
            id=note_id,
            user_id=user_id,
            title=title,
            content=formatted_content,
        )

        try:
            db.add(note)
            await db.flush()
            await db.refresh(note)
        except SQLAlchemyError as e:
            logger.error(f"Failed to create note: {e}")
            raise NoteServiceError("Failed to create note", e) from e

        return note

    async def update_note(self, note_id: str, user_id: int, input_data: UpdateNoteInput) -> Note:
        """
        Update an existing note.

        Args:
            note_id: ID of the note to update.
            user_id: ID of the user (for ownership verification).
            input_data: Note update data (content and/or title).

        Returns:
            The updated Note object.

        Raises:
            NoteNotFoundError: If note doesn't exist or doesn't belong to user.
            NoteServiceError: If database operation fails.
        """
        db = get_db()
        note = await self.get_note_by_id(note_id, user_id)

        if input_data.content is not None:
            # When content changes, reprocess and extract title
            formatted_content, extracted_title = self.process_note_content(input_data.content)
            note.content = formatted_content  # type: ignore[assignment]
            note.title = extracted_title  # type: ignore[assignment]
        elif input_data.title is not None:
            # Only title update (no content change)
            note.title = input_data.title  # type: ignore[assignment]

        try:
            await db.flush()
            await db.refresh(note)
        except SQLAlchemyError as e:
            logger.error(f"Failed to update note {note_id}: {e}")
            raise NoteServiceError(f"Failed to update note {note_id}", e) from e

        return note

    async def delete_note(self, note_id: str, user_id: int) -> str:
        """
        Delete a note.

        Args:
            note_id: ID of the note to delete.
            user_id: ID of the user (for ownership verification).

        Returns:
            The ID of the deleted note.

        Raises:
            NoteNotFoundError: If note doesn't exist or doesn't belong to user.
            NoteServiceError: If database operation fails.
        """
        db = get_db()
        note = await self.get_note_by_id(note_id, user_id)

        try:
            await db.delete(note)
            await db.flush()
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete note {note_id}: {e}")
            raise NoteServiceError(f"Failed to delete note {note_id}", e) from e

        return note_id


# Singleton instance - use this instead of creating new instances
note_service = NoteService()
