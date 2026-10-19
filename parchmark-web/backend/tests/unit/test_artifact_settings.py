"""Unit tests for app.artifact_settings: ARTIFACT_CONTENT_ORIGIN is validated at import."""

import os
from collections.abc import Iterator
from importlib import reload
from unittest.mock import patch

import pytest

import app.artifact_settings


@pytest.fixture(autouse=True)
def _restore_module() -> Iterator[None]:
    """Reload the module with the session's environment afterwards, so other tests see the real value."""
    yield
    reload(app.artifact_settings)


def _load(value: str | None) -> str:
    env = {k: v for k, v in os.environ.items() if k != "ARTIFACT_CONTENT_ORIGIN"}
    if value is not None:
        env["ARTIFACT_CONTENT_ORIGIN"] = value
    with patch.dict("os.environ", env, clear=True):
        return reload(app.artifact_settings).ARTIFACT_CONTENT_ORIGIN


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "content.example.com",
        "ftp://content.example.com",
        "https://",
        "https://content.example.com/a",
        "https://content.example.com?x=1",
        "https://content.example.com#top",
    ],
    ids=["unset", "empty", "no-scheme", "ftp", "no-host", "path", "query", "fragment"],
)
def test_an_invalid_origin_refuses_to_load(value: str | None):
    with pytest.raises(ValueError):
        _load(value)


@pytest.mark.parametrize("value", ["http://localhost:8000", "https://content.example.com"])
def test_a_valid_origin_loads_unchanged(value: str):
    assert _load(value) == value


def test_a_trailing_slash_is_stripped():
    assert _load("https://content.example.com/") == "https://content.example.com"


def _load_signing_key(value: str | None, secret_key: str = "a-secret-key-that-is-long-enough-to-pass") -> str:
    env = {k: v for k, v in os.environ.items() if k not in ("ARTIFACT_SIGNING_KEY", "SECRET_KEY")}
    env["SECRET_KEY"] = secret_key
    if value is not None:
        env["ARTIFACT_SIGNING_KEY"] = value
    with patch.dict("os.environ", env, clear=True):
        return reload(app.artifact_settings).ARTIFACT_SIGNING_KEY


@pytest.mark.parametrize("value", [None, "", "k" * 31], ids=["unset", "empty", "31-chars"])
def test_a_missing_or_short_signing_key_refuses_to_load(value: str | None):
    with pytest.raises(ValueError, match="ARTIFACT_SIGNING_KEY"):
        _load_signing_key(value)


def test_a_signing_key_equal_to_secret_key_refuses_to_load():
    with pytest.raises(ValueError, match="ARTIFACT_SIGNING_KEY"):
        _load_signing_key("s" * 40, secret_key="s" * 40)


def test_a_signing_key_of_32_characters_loads_unchanged():
    assert _load_signing_key("k" * 32) == "k" * 32
