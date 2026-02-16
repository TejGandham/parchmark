from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import embeddings


@pytest.mark.asyncio
async def test_generate_embedding_returns_embedding_when_openai_call_succeeds(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    expected_embedding = [0.1, 0.2, 0.3]
    mock_response = SimpleNamespace(data=[SimpleNamespace(embedding=expected_embedding)])
    mock_client = SimpleNamespace(embeddings=SimpleNamespace(create=AsyncMock(return_value=mock_response)))

    monkeypatch.setattr(embeddings, "_get_client", lambda: mock_client)

    result = await embeddings.generate_embedding("hello world")

    assert result == expected_embedding
    mock_client.embeddings.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_embedding_returns_none_when_api_key_not_set(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = await embeddings.generate_embedding("hello world")

    assert result is None


@pytest.mark.asyncio
async def test_generate_embedding_returns_none_for_empty_text(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    assert await embeddings.generate_embedding("") is None
    assert await embeddings.generate_embedding("   ") is None


@pytest.mark.asyncio
async def test_generate_embedding_returns_none_when_openai_call_fails(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    mock_client = SimpleNamespace(
        embeddings=SimpleNamespace(create=AsyncMock(side_effect=RuntimeError("upstream error"))),
    )
    monkeypatch.setattr(embeddings, "_get_client", lambda: mock_client)

    result = await embeddings.generate_embedding("hello world")

    assert result is None


def test_compute_similarity_returns_one_for_identical_embeddings():
    embedding = [1.0, 2.0, 3.0]

    similarity = embeddings.compute_similarity(embedding, embedding)

    assert similarity == pytest.approx(1.0)


def test_compute_similarity_returns_zero_for_empty_embeddings():
    assert embeddings.compute_similarity([], [1.0, 2.0]) == 0.0
    assert embeddings.compute_similarity([1.0, 2.0], []) == 0.0


def test_compute_similarity_returns_zero_for_mismatched_lengths():
    similarity = embeddings.compute_similarity([1.0, 2.0], [1.0, 2.0, 3.0])

    assert similarity == 0.0


def test_compute_similarity_returns_zero_for_zero_magnitude_vectors():
    similarity = embeddings.compute_similarity([0.0, 0.0], [1.0, 2.0])

    assert similarity == 0.0


def test_compute_similarity_returns_between_zero_and_one_for_valid_embeddings():
    similarity = embeddings.compute_similarity([1.0, 2.0, 3.0], [3.0, 2.0, 1.0])

    assert 0.0 <= similarity <= 1.0


def test_compute_similarity_returns_expected_cosine_similarity_for_known_vectors():
    similarity = embeddings.compute_similarity([1.0, 0.0], [1.0, 1.0])

    assert similarity == pytest.approx(0.70710678118, rel=1e-9)
