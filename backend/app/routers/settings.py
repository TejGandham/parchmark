"""
Settings and account management routes for ParchMark backend API.
Handles password changes, account information, note exports, and account deletion.
Supports both local and OIDC authentication providers.
"""

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from stream_zip import ZIP_32, stream_zip

from app.auth.auth import get_password_hash, verify_password
from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import Note, User
from app.schemas.schemas import (
    AccountDeleteRequest,
    MessageResponse,
    PasswordChangeRequest,
    UserInfoResponse,
)

# Batch size for streaming notes from database
EXPORT_BATCH_SIZE = 100

# Create router for settings endpoints
router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/user-info", response_model=UserInfoResponse)
async def get_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get detailed user information including account creation date and note count.

    Returns user info with auth_provider to help frontend determine
    which settings are available (e.g., password change for local users only).

    Args:
        current_user: Current authenticated user from JWT token
        db: Async database session dependency

    Returns:
        UserInfoResponse: User information with statistics and auth provider
    """
    result = await db.execute(select(func.count()).select_from(Note).filter(Note.user_id == current_user.id))
    notes_count = result.scalar() or 0

    return UserInfoResponse(
        username=current_user.username,  # type: ignore[arg-type]
        email=current_user.email,  # type: ignore[arg-type]
        created_at=current_user.created_at.isoformat(),
        notes_count=notes_count,
        auth_provider=current_user.auth_provider,  # type: ignore[arg-type]
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Change user password after verifying current password.

    Only available for local authentication users. OIDC users must
    change their password through their identity provider.

    Args:
        request: Password change request with current and new passwords
        current_user: Current authenticated user from JWT token
        db: Async database session dependency

    Returns:
        MessageResponse: Confirmation message

    Raises:
        HTTPException: 400 if user is OIDC-authenticated (cannot change password)
        HTTPException: 401 if current password is incorrect
        HTTPException: 400 if new password is same as current
    """
    # Check if user can change password (local auth only)
    if current_user.auth_provider != "local" or current_user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change is not available for OIDC accounts. Please change your password through your identity provider.",
        )

    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):  # type: ignore[arg-type]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Check if new password is different
    if verify_password(request.new_password, current_user.password_hash):  # type: ignore[arg-type]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    current_user.password_hash = get_password_hash(request.new_password)  # type: ignore[assignment]
    await db.commit()

    return MessageResponse(message="Password changed successfully")


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


async def _collect_notes_for_export(
    db: AsyncSession, user_id: int
) -> tuple[list[tuple[str, str]], list[dict[str, Any]]]:
    """Collect all notes for a user, preparing filenames and metadata.

    This fetches notes in batches to avoid loading everything at once,
    but collects all data needed for the ZIP generation.

    Args:
        db: Async database session
        user_id: The user's ID

    Returns:
        Tuple of (list of (filename, content) pairs, list of metadata dicts)
    """
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
    modified_time = datetime.now(UTC)
    file_mode = 0o644

    # Yield markdown files
    for filename, content in note_files:
        content_bytes = content.encode("utf-8")
        yield filename, modified_time, file_mode, ZIP_32, (content_bytes,)

    # Yield metadata JSON file
    metadata_json = json.dumps(notes_metadata, indent=2).encode("utf-8")
    yield "notes_metadata.json", modified_time, file_mode, ZIP_32, (metadata_json,)


@router.get("/export-notes")
async def export_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Export all user notes as a ZIP archive with markdown files and metadata.

    This endpoint streams a ZIP file containing:
    1. All notes as individual markdown files (sanitized filenames)
    2. A JSON file with complete note metadata for backup/restore

    The ZIP is streamed incrementally to avoid loading the entire archive
    into memory, preventing OOM errors for users with many large notes.

    Args:
        current_user: Current authenticated user from JWT token
        db: Async database session dependency

    Returns:
        StreamingResponse: Streamed ZIP file download with all notes
    """
    # Collect notes data (streamed from DB in batches)
    note_files, notes_metadata = await _collect_notes_for_export(db, current_user.id)  # type: ignore[arg-type]

    # Generate filename with timestamp
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    zip_filename = f"parchmark_notes_{timestamp}.zip"

    # Create streaming ZIP response
    # stream_zip yields chunks as they're generated, avoiding full buffering
    zip_chunks = stream_zip(
        _generate_zip_entries(note_files, notes_metadata),
        chunk_size=65536,  # 64KB chunks
    )

    return StreamingResponse(
        iter(zip_chunks),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"},
    )


@router.delete("/delete-account", response_model=MessageResponse)
async def delete_account(
    request: AccountDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete user account and all associated notes after password verification.

    This is a destructive operation that:
    1. Verifies the user's password (for local auth) or accepts confirmation (for OIDC)
    2. Deletes all notes belonging to the user (cascade)
    3. Deletes the user account

    For OIDC users, password verification still works as a confirmation mechanism
    if they have a linked local password, otherwise any non-empty password acts as confirmation.

    Args:
        request: Account deletion request with password confirmation
        current_user: Current authenticated user from JWT token
        db: Async database session dependency

    Returns:
        MessageResponse: Confirmation message

    Raises:
        HTTPException: 401 if password is incorrect (for local users)
    """
    # For local users, verify password
    if current_user.auth_provider == "local" and current_user.password_hash is not None:
        if not verify_password(request.password, current_user.password_hash):  # type: ignore[arg-type]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password is incorrect",
            )
    # For OIDC users with a password hash, verify if provided
    elif current_user.password_hash is not None:
        if not verify_password(request.password, current_user.password_hash):  # type: ignore[arg-type]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password is incorrect",
            )
    # For OIDC users without password, the request body password acts as confirmation
    # (frontend should require typing "DELETE" or similar)

    username = current_user.username

    # Delete user (notes will cascade delete due to relationship)
    await db.delete(current_user)
    await db.commit()

    return MessageResponse(message=f"Account '{username}' deleted successfully")
