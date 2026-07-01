"""
Settings and account management routes for ParchMark backend API.
Handles password changes, account information, note exports, and account deletion.
Supports both local and OIDC authentication providers.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import User
from app.schemas.schemas import (
    AccountDeleteRequest,
    MessageResponse,
    PasswordChangeRequest,
    UserInfoResponse,
)
from app.services import settings_service

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
    return await settings_service.get_user_info(db, current_user)


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
    return await settings_service.change_password(db, current_user, request)


@router.get("/export-notes")
async def export_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StreamingResponse:
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
    note_files, notes_metadata = await settings_service.collect_notes_for_export(
        db,
        current_user.id,  # type: ignore[arg-type]
    )
    return settings_service.build_export_response(note_files, notes_metadata)


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
    return await settings_service.delete_account(db, current_user, request)
