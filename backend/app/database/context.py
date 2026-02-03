"""
Database session context management using contextvars.

Provides request-scoped database sessions accessible from anywhere in the application
without explicit parameter passing. This enables true singleton services.

Usage:
    from app.database.context import get_db

    class MyService:
        async def do_something(self):
            db = get_db()  # Gets current request's session
            result = await db.execute(...)
"""

from contextvars import ContextVar, Token

from sqlalchemy.ext.asyncio import AsyncSession

# ContextVar to store the current request's database session
# Default is None - will be set by middleware for each request
_db_session_context: ContextVar[AsyncSession | None] = ContextVar("db_session", default=None)


def get_db() -> AsyncSession:
    """
    Get the database session for the current request context.

    Returns:
        AsyncSession: The database session for the current request.

    Raises:
        RuntimeError: If called outside of a request context (no session set).
    """
    session = _db_session_context.get()
    if session is None:
        raise RuntimeError(
            "Database session is not available in the current context. "
            "Ensure this is called within an HTTP request handled by DBSessionMiddleware."
        )
    return session


def set_db(session: AsyncSession) -> Token[AsyncSession | None]:
    """
    Set the database session for the current request context.

    Args:
        session: The AsyncSession to set for this context.

    Returns:
        Token that can be used to reset the context to its previous value.
    """
    return _db_session_context.set(session)


def reset_db(token: Token[AsyncSession | None]) -> None:
    """
    Reset the database session context to its previous value.

    Args:
        token: The token returned by set_db() to restore previous state.
    """
    _db_session_context.reset(token)
