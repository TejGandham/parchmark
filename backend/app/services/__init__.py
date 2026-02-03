"""
Services package for business logic layer.

This package contains service classes that encapsulate business logic,
separating it from HTTP concerns in routers. Services are responsible for:
- Domain logic and business rules
- Data transformation and validation
- Orchestrating database operations
- Error handling with domain-specific exceptions

Services receive database sessions via dependency injection and do not
directly handle HTTP requests/responses.
"""

from app.services.auth_service import (
    AuthenticationError,
    AuthService,
    InvalidRefreshTokenError,
    LoginInput,
    TokenResult,
)
from app.services.health_service import HealthService, health_service
from app.services.note_service import (
    CreateNoteInput,
    NoteNotFoundError,
    NoteService,
    NoteServiceError,
    UpdateNoteInput,
)

__all__ = [
    # Auth service
    "AuthService",
    "AuthenticationError",
    "InvalidRefreshTokenError",
    "LoginInput",
    "TokenResult",
    # Health service
    "HealthService",
    "health_service",
    # Note service
    "NoteService",
    "NoteNotFoundError",
    "NoteServiceError",
    "CreateNoteInput",
    "UpdateNoteInput",
]
