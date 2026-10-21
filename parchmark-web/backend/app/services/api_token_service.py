"""Personal API token business logic: issue, list, revoke, and resolve to a user.

Tokens are ``pmat_`` followed by 256 bits of randomness. Only the SHA-256 hex
digest is stored, so a database leak does not expose usable tokens; a plain
digest (not bcrypt) is enough for a high-entropy secret and keeps the auth
lookup a single indexed query.
"""

import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_token import ApiToken
from app.models.models import User
from app.schemas.api_token import ApiTokenCreate, ApiTokenCreated, ApiTokenResponse
from app.schemas.schemas import DeleteResponse

TOKEN_PREFIX = "pmat_"


def is_api_token(token: str) -> bool:
    """Whether a bearer credential is a personal API token rather than a JWT or OIDC token."""
    return token.startswith(TOKEN_PREFIX)


def hash_token(token: str) -> str:
    """Return the stored digest for a plaintext token."""
    return hashlib.sha256(token.encode()).hexdigest()


async def create_token(db: AsyncSession, current_user: User, request: ApiTokenCreate) -> ApiTokenCreated:
    """Issue a new token for the user and return its plaintext, the only time it is available."""
    plaintext = TOKEN_PREFIX + secrets.token_urlsafe(32)
    api_token = ApiToken(user_id=current_user.id, name=request.name, token_hash=hash_token(plaintext))
    db.add(api_token)
    await db.commit()
    await db.refresh(api_token)
    metadata = ApiTokenResponse.model_validate(api_token)
    return ApiTokenCreated(**metadata.model_dump(), token=plaintext)


async def list_tokens(db: AsyncSession, current_user: User) -> list[ApiTokenResponse]:
    """Return metadata for the user's tokens, newest first."""
    result = await db.execute(select(ApiToken).filter(ApiToken.user_id == current_user.id).order_by(ApiToken.id.desc()))
    return [ApiTokenResponse.model_validate(api_token) for api_token in result.scalars().all()]


async def revoke_token(db: AsyncSession, current_user: User, token_id: int) -> DeleteResponse:
    """Delete one of the user's tokens so it no longer authenticates.

    Raises:
        HTTPException: 404 if the token does not exist or belongs to another user.
    """
    result = await db.execute(select(ApiToken).filter(ApiToken.id == token_id, ApiToken.user_id == current_user.id))
    api_token = result.scalar_one_or_none()
    if api_token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    await db.delete(api_token)
    await db.commit()
    return DeleteResponse(message="Token revoked successfully", deleted_id=str(token_id))


async def get_user_by_token(db: AsyncSession, token: str) -> User | None:
    """Resolve a plaintext token to its owner, or None when it is unknown or revoked."""
    result = await db.execute(
        select(User).join(ApiToken, ApiToken.user_id == User.id).filter(ApiToken.token_hash == hash_token(token))
    )
    return result.scalar_one_or_none()
