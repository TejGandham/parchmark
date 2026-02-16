from __future__ import annotations

import logging
import math
import os

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = 1536


def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI

        return AsyncOpenAI(api_key=api_key)
    except Exception:
        logger.warning("Failed to create OpenAI client")
        return None


async def generate_embedding(text: str) -> list[float] | None:
    if not text or not text.strip():
        return None

    client = _get_client()
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
