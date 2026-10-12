"""Settings account management business logic."""

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from stream_zip import ZIP_32, stream_zip

from app.auth.auth import get_password_hash, verify_password
from app.models.models import Note, User
from app.schemas.schemas import (
    AccountDeleteRequest,
    MessageResponse,
    PasswordChangeRequest,
    UserInfoResponse,
)

EXPORT_BATCH_SIZE = 100


async def get_user_info(db: AsyncSession, current_user: User) -> UserInfoResponse:
    """Return account details and note count for the authenticated user."""
    result = await db.execute(select(func.count()).select_from(Note).filter(Note.user_id == current_user.id))
    notes_count = result.scalar() or 0

    return UserInfoResponse(
        username=cast(str, current_user.username),
        email=cast(str | None, current_user.email),
        created_at=current_user.created_at.isoformat(),
        notes_count=notes_count,
        auth_provider=cast(str, current_user.auth_provider),
    )


async def change_password(db: AsyncSession, current_user: User, request: PasswordChangeRequest) -> MessageResponse:
    """Change a local user's password after validating the current password."""
    if current_user.auth_provider != "local" or current_user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change is not available for OIDC accounts. Please change your password through your identity provider.",
        )

    password_hash = cast(str, current_user.password_hash)

    if not verify_password(request.current_password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    if verify_password(request.new_password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    current_user.password_hash = get_password_hash(request.new_password)  # type: ignore[assignment]
    await db.commit()

    return MessageResponse(message="Password changed successfully")


async def delete_account(db: AsyncSession, current_user: User, request: AccountDeleteRequest) -> MessageResponse:
    """Permanently delete the authenticated user's account and all of its notes.

    Local accounts (and OIDC accounts with a linked password) must supply a
    password that verifies. OIDC accounts without a password hash rely on the
    non-empty confirmation enforced by ``AccountDeleteRequest``.
    """
    if current_user.password_hash is not None and not verify_password(
        request.password, cast(str, current_user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect",
        )

    username = current_user.username

    # Deleting the user cascades notes through the ORM relationship.
    await db.delete(current_user)
    await db.commit()

    return MessageResponse(message=f"Account '{username}' deleted successfully")


def _sanitize_filename(title: str, used_filenames: set[str]) -> str:
    """Sanitize a note title into a unique markdown filename."""
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_"))
    safe_title = safe_title.strip() or "untitled"
    base_filename = f"{safe_title[:50]}.md"

    filename = base_filename
    counter = 1
    while filename in used_filenames:
        filename = f"{safe_title[:45]}_{counter}.md"
        counter += 1
    used_filenames.add(filename)

    return filename


async def collect_notes_for_export(
    db: AsyncSession, user_id: int
) -> tuple[list[tuple[str, str]], list[dict[str, Any]]]:
    """Collect one user's notes as markdown files plus backup metadata."""
    used_filenames: set[str] = set()
    note_files: list[tuple[str, str]] = []
    notes_metadata: list[dict[str, Any]] = []

    result = await db.stream(
        select(Note).filter(Note.user_id == user_id).execution_options(yield_per=EXPORT_BATCH_SIZE)
    )

    async for note in result.scalars():
        filename = _sanitize_filename(str(note.title), used_filenames)
        note_files.append((filename, str(note.content)))
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


def generate_zip_entries(
    note_files: list[tuple[str, str]], notes_metadata: list[dict[str, Any]]
) -> Iterable[tuple[str, datetime, int, Any, Iterable[bytes]]]:
    """Yield stream_zip entries for markdown notes and metadata JSON."""
    modified_time = datetime.now(UTC)
    file_mode = 0o644

    for filename, content in note_files:
        content_bytes = content.encode("utf-8")
        yield filename, modified_time, file_mode, ZIP_32, (content_bytes,)

    metadata_json = json.dumps(notes_metadata, indent=2).encode("utf-8")
    yield "notes_metadata.json", modified_time, file_mode, ZIP_32, (metadata_json,)


def build_export_response(note_files: list[tuple[str, str]], notes_metadata: list[dict[str, Any]]) -> StreamingResponse:
    """Build the streaming ZIP response for a full-notes export."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    zip_filename = f"parchmark_notes_{timestamp}.zip"
    zip_chunks = stream_zip(
        generate_zip_entries(note_files, notes_metadata),
        chunk_size=65536,
    )

    return StreamingResponse(
        iter(zip_chunks),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"},
    )
