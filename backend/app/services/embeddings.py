from __future__ import annotations

import logging
import math
import os
from typing import Any

from fastapi import Request

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = 1536


def get_openai_client(request: Request) -> Any:
    """FastAPI dependency: returns the OpenAI client stored on app.state by the lifespan."""
    return getattr(request.app.state, "openai_client", None)


async def generate_embedding(text: str, client: Any) -> list[float] | None:
    if not text or not text.strip():
        return None

    if client is None:
        return None

    try:
        truncated = text[:32000]
        response = await client.embeddings.create(
            input=truncated,
            model=EMBEDDING_MODEL,
        )
        return response.data[0].embedding
    except Exception as exc:
        logger.warning("Failed to generate embedding: %s", exc)
        return None


def compute_similarity(embedding1: list[float], embedding2: list[float]) -> float:
    if not embedding1 or not embedding2:
        return 0.0
    if len(embedding1) != len(embedding2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=True))
    magnitude1 = math.sqrt(sum(a * a for a in embedding1))
    magnitude2 = math.sqrt(sum(b * b for b in embedding2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    similarity = dot_product / (magnitude1 * magnitude2)
    return max(0.0, min(1.0, similarity))
