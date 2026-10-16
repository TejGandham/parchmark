"""Unit tests for artifact request schemas (app.schemas.artifact)."""

import pytest
from pydantic import ValidationError

from app.schemas.artifact import ArtifactCreate, ArtifactVersionCreate, ArtifactVisibilityUpdate


@pytest.mark.parametrize("content_type", ["html", "markdown", "svg"])
def test_supported_content_types_are_accepted(content_type: str):
    assert ArtifactVersionCreate(content_type=content_type, content="x").content_type == content_type


@pytest.mark.parametrize(
    "body",
    [
        {"title": "T", "content_type": "pdf", "content": "x"},
        {"title": "T", "content_type": "html", "content": ""},
        {"title": "", "content_type": "html", "content": "x"},
        {"title": "x" * 256, "content_type": "html", "content": "x"},
    ],
    ids=["content-type", "empty-content", "empty-title", "long-title"],
)
def test_invalid_artifact_is_rejected(body: dict[str, str]):
    with pytest.raises(ValidationError):
        ArtifactCreate(**body)


def test_visibility_is_private_or_unlisted():
    assert ArtifactVisibilityUpdate(visibility="unlisted").visibility == "unlisted"
    with pytest.raises(ValidationError):
        ArtifactVisibilityUpdate(visibility="public")
