"""
Database session middleware for request-scoped session management.

This middleware creates a new database session for each HTTP request and stores it
in a ContextVar, making it accessible to singleton services without explicit passing.

The middleware ensures:
1. Each request gets its own isolated database session
2. Sessions are properly committed on success
3. Sessions are rolled back on errors
4. Sessions are always closed in the finally block
5. Context is properly reset using tokens (handles nested contexts)
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.database.context import reset_db, set_db
from app.database.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DBSessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages database session lifecycle per request.

    Creates a new AsyncSession for each request, stores it in ContextVar,
    and ensures proper cleanup (commit/rollback/close) after the request.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.

        Args:
            app: The ASGI application to wrap.
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request with a database session.

        Creates a new session, sets it in the context, processes the request,
        and handles commit/rollback/cleanup.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The HTTP response.
        """
        # Create a new session for this request
        async with AsyncSessionLocal() as session:
            # Set the session in the context and get the token for cleanup
            token = set_db(session)

            try:
                # Process the request
                response = await call_next(request)

                # Commit on success (2xx, 3xx status codes)
                # Note: 4xx errors are often expected (validation, not found, etc.)
                # so we still commit those - they didn't cause a database error
                if response.status_code < 500:
                    await session.commit()
                else:
                    # 5xx errors indicate something went wrong - rollback
                    await session.rollback()

                return response

            except Exception as e:
                # Rollback on any unhandled exception
                logger.error(f"Request failed with exception: {e}")
                await session.rollback()
                raise

            finally:
                # Always reset the context to prevent leaks
                # Using token.reset() properly handles nested contexts
                reset_db(token)
                # Session is automatically closed by the async context manager
