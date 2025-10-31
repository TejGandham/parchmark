"""
Settings and account management routes for ParchMark backend API.
Handles password changes, account information, note exports, and account deletion.
"""

import io
import json
import zipfile
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.auth import get_password_hash, verify_password
from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.models import Note, User
from app.schemas.schemas import (
    AccountDeleteRequest,
    MessageResponse,
    PasswordChangeRequest,
    UserInfoResponse,
)

# Create router for settings endpoints
router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/user-info", response_model=UserInfoResponse)
async def get_user_info(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get detailed user information including account creation date and note count.

    Args:
        current_user: Current authenticated user from JWT token
        db: Database session dependency

    Returns:
        UserInfoResponse: User information with statistics
    """
    notes_count = db.query(Note).filter(Note.user_id == current_user.id).count()

    return UserInfoResponse(
        username=current_user.username,
        created_at=current_user.created_at.isoformat(),
        notes_count=notes_count,
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change user password after verifying current password.

    Args:
        request: Password change request with current and new passwords
        current_user: Current authenticated user from JWT token
        db: Database session dependency

    Returns:
        MessageResponse: Confirmation message

    Raises:
        HTTPException: 401 if current password is incorrect
        HTTPException: 400 if new password is same as current
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Check if new password is different
    if verify_password(request.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    current_user.password_hash = get_password_hash(request.new_password)
    db.commit()

    return MessageResponse(message="Password changed successfully")


@router.get("/export-notes")
async def export_notes(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Export all user notes as a JSON file or ZIP archive with markdown files.

    This endpoint creates a ZIP file containing:
    1. All notes as individual markdown files
    2. A JSON file with complete note metadata

    Args:
        current_user: Current authenticated user from JWT token
        db: Database session dependency

    Returns:
        StreamingResponse: ZIP file download with all notes
    """
    # Get all user's notes
    notes = db.query(Note).filter(Note.user_id == current_user.id).all()

    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add individual markdown files
        for note in notes:
            # Sanitize filename (remove invalid characters)
            safe_title = "".join(c for c in note.title if c.isalnum() or c in (" ", "-", "_"))
            filename = f"{safe_title[:50]}.md"  # Limit filename length
            zip_file.writestr(filename, note.content)

        # Add JSON metadata file
        notes_data = [
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "createdAt": note.created_at.isoformat(),
                "updatedAt": note.updated_at.isoformat(),
            }
            for note in notes
        ]
        zip_file.writestr("notes_metadata.json", json.dumps(notes_data, indent=2))

    # Prepare ZIP for download
    zip_buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"parchmark_notes_{timestamp}.zip"

    return StreamingResponse(
        io.BytesIO(zip_buffer.getvalue()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/delete-account", response_model=MessageResponse)
async def delete_account(
    request: AccountDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete user account and all associated notes after password verification.

    This is a destructive operation that:
    1. Verifies the user's password
    2. Deletes all notes belonging to the user (cascade)
    3. Deletes the user account

    Args:
        request: Account deletion request with password confirmation
        current_user: Current authenticated user from JWT token
        db: Database session dependency

    Returns:
        MessageResponse: Confirmation message

    Raises:
        HTTPException: 401 if password is incorrect
    """
    # Verify password
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect",
        )

    username = current_user.username

    # Delete user (notes will cascade delete due to relationship)
    db.delete(current_user)
    db.commit()

    return MessageResponse(message=f"Account '{username}' deleted successfully")
