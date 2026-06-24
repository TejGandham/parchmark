"""Settings account-summary business logic."""

from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_password_hash, verify_password
from app.models.models import Note, User
from app.schemas.schemas import MessageResponse, PasswordChangeRequest, UserInfoResponse


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
