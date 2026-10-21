"""Pydantic schemas for personal API token requests and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiTokenCreate(BaseModel):
    """Request body for creating a token."""

    name: str = Field(..., min_length=1, max_length=100, description="Label that identifies the token")

    model_config = ConfigDict(str_strip_whitespace=True)


class ApiTokenResponse(BaseModel):
    """Token metadata. Never carries the plaintext token."""

    id: int = Field(..., description="Token identifier, used to revoke it")
    name: str = Field(..., description="Label that identifies the token")
    created_at: datetime = Field(..., description="When the token was created")

    model_config = ConfigDict(from_attributes=True)


class ApiTokenCreated(ApiTokenResponse):
    """Creation response: metadata plus the plaintext, which is returned only this once."""

    token: str = Field(..., description="Plaintext bearer token. Shown only at creation; store it now.")
