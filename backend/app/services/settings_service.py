"""
Settings service for business logic related to user account management.
Extracts business logic from routers for better testability and reusability.

This service is a singleton - it uses contextvars to access the request-scoped
database session without requiring it to be passed as a parameter.
"""

import json
import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.auth.auth import get_password_hash, verify_password
from app.database.context import get_db
from app.models.models import Note, User

logger = logging.getLogger(__name__)

# Batch size for streaming notes from database
EXPORT_BATCH_SIZE = 100


class PasswordChangeError(Exception):
    """Raised when password change operation fails."""

    def __init__(self, message: str = "Password change failed"):
        super().__init__(message)


class AccountDeletionError(Exception):
    """Raised when account deletion operation fails."""

    def __init__(self, message: str = "Account deletion failed"):
        super().__init__(message)


def _sanitize_filename(title: str, used_filenames: set[str]) -> str:
    """Sanitize note title to create a valid, unique filename.

    Args:
        title: The note title to sanitize
        used_filenames: Set of already-used filenames to avoid duplicates

    Returns:
        A unique, sanitized filename ending in .md
    """
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_"))
    safe_title = safe_title.strip() or "untitled"
    base_filename = f"{safe_title[:50]}.md"

    # Handle duplicate filenames
    filename = base_filename
    counter = 1
    while filename in used_filenames:
        filename = f"{safe_title[:45]}_{counter}.md"
        counter += 1
    used_filenames.add(filename)

    return filename


def _generate_zip_entries(
    note_files: list[tuple[str, str]], notes_metadata: list[dict[str, Any]]
) -> Iterable[tuple[str, datetime, int, Any, Iterable[bytes]]]:
    """Generate ZIP file entries for stream_zip.

    Each entry is a tuple of (filename, modified_time, mode, compression, content_iterator).

    Args:
        note_files: List of (filename, content) tuples for markdown files
        notes_metadata: List of metadata dictionaries for JSON file

    Yields:
        Tuples suitable for stream_zip consumption
    """
    from stream_zip import ZIP_32

    modified_time = datetime.now(UTC)
    file_mode = 0o644

    # Yield markdown files
    for filename, content in note_files:
        content_bytes = content.encode("utf-8")
        yield filename, modified_time, file_mode, ZIP_32, (content_bytes,)

    # Yield metadata JSON file
    metadata_json = json.dumps(notes_metadata, indent=2).encode("utf-8")
    yield "notes_metadata.json", modified_time, file_mode, ZIP_32, (metadata_json,)


class SettingsService:
    """
    Service for settings and account management business logic.

    Handles user account operations including password changes, note exports,
    and account deletion with proper business rules applied.

    This is a singleton service - database session is obtained from context
    for each operation, ensuring request isolation.
    """

    async def get_user_note_count(self, user_id: int) -> int:
        """
        Get the count of notes for a user.

        Args:
            user_id: ID of the user whose notes to count.

        Returns:
            The number of notes belonging to the user.
        """
        db = get_db()
        result = await db.execute(select(func.count()).select_from(Note).filter(Note.user_id == user_id))
        notes_count = result.scalar() or 0
        return notes_count

    async def change_user_password(self, user: User, current_password: str, new_password: str) -> None:
        """
        Change a user's password after verifying the current password.

        Args:
            user: The user object whose password to change.
            current_password: The user's current password for verification.
            new_password: The new password to set.

        Raises:
            PasswordChangeError: If user is OIDC-authenticated, current password is wrong,
                                or new password is same as current.
        """
        db = get_db()

        # Check if user can change password (local auth only)
        if user.auth_provider != "local" or user.password_hash is None:
            raise PasswordChangeError(
                "Password change is not available for OIDC accounts. Please change your password through your identity provider."
            )

        # Verify current password
        if not verify_password(current_password, user.password_hash):  # type: ignore[arg-type]
            raise PasswordChangeError("Current password is incorrect")

        # Check if new password is different
        if verify_password(new_password, user.password_hash):  # type: ignore[arg-type]
            raise PasswordChangeError("New password must be different from current password")

        # Merge user into session to ensure changes are tracked
        user = await db.merge(user)

        # Update password
        user.password_hash = get_password_hash(new_password)  # type: ignore[assignment]

        try:
            await db.flush()
        except SQLAlchemyError as e:
            logger.error(f"Failed to change password for user {user.id}: {e}")
            raise PasswordChangeError("Failed to change password") from e

    async def collect_notes_for_export(self, user_id: int) -> tuple[list[tuple[str, str]], list[dict[str, Any]]]:
        """Collect all notes for a user, preparing filenames and metadata.

        This fetches notes in batches to avoid loading everything at once,
        but collects all data needed for the ZIP generation.

        Args:
            user_id: The user's ID

        Returns:
            Tuple of (list of (filename, content) pairs, list of metadata dicts)
        """
        db = get_db()
        used_filenames: set[str] = set()
        note_files: list[tuple[str, str]] = []
        notes_metadata: list[dict[str, Any]] = []

        # Stream notes in batches to reduce memory pressure during fetch
        result = await db.stream(
            select(Note).filter(Note.user_id == user_id).execution_options(yield_per=EXPORT_BATCH_SIZE)
        )

        async for note in result.scalars():
            # Prepare file entry
            filename = _sanitize_filename(str(note.title), used_filenames)
            note_files.append((filename, str(note.content)))

            # Prepare metadata entry
            notes_metadata.append(
                {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "createdAt": note.created_at.isoformat(),
                    "updatedAt": note.updated_at.isoformat(),
                }
            )

        return note_files, notes_metadata

    async def delete_user_account(self, user: User) -> str:
        """
        Delete a user account and all associated notes.

        Args:
            user: The user object to delete.

        Returns:
            The username of the deleted account.

        Raises:
            AccountDeletionError: If database operation fails.
        """
        db = get_db()
        username = user.username

        # Merge user into session to ensure it's tracked
        user = await db.merge(user)

        try:
            await db.delete(user)
            await db.flush()
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete account for user {user.id}: {e}")
            raise AccountDeletionError("Failed to delete account") from e

        return username  # type: ignore[return-value]


# Singleton instance - use this instead of creating new instances
settings_service = SettingsService()
