"""
Services package for business logic layer.

This package contains singleton service classes that encapsulate business logic,
separating it from HTTP concerns in routers. Services are responsible for:
- Domain logic and business rules
- Data transformation and validation
- Orchestrating database operations
- Error handling with domain-specific exceptions

Services access the database session via contextvars (set by DBSessionMiddleware),
enabling true singleton pattern without passing db to every method.
"""

from app.services.auth_service import (
    AuthenticationError,
    AuthService,
    InvalidRefreshTokenError,
    LoginInput,
    TokenResult,
    auth_service,
)
from app.services.health_service import HealthService, health_service
from app.services.note_service import (
    CreateNoteInput,
    NoteNotFoundError,
    NoteService,
    NoteServiceError,
    UpdateNoteInput,
    note_service,
)

__all__ = [
    # Auth service
    "AuthService",
    "auth_service",
    "AuthenticationError",
    "InvalidRefreshTokenError",
    "LoginInput",
    "TokenResult",
    # Health service
    "HealthService",
    "health_service",
    # Note service
    "NoteService",
    "note_service",
    "NoteNotFoundError",
    "NoteServiceError",
    "CreateNoteInput",
    "UpdateNoteInput",
]
