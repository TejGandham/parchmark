"""Settings account-summary business logic."""

from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Note, User
from app.schemas.schemas import UserInfoResponse


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
