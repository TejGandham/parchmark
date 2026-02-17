"""
Backfill embeddings for existing notes.

Usage: cd backend && uv run python -m app.services.backfill

Generates OpenAI embeddings for all notes that don't have one.
Rate-limited to avoid API throttling.
"""

import asyncio
import logging
import sys
import time
from typing import cast

from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.models.models import Note
from app.services.embeddings import generate_embedding

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

RATE_LIMIT_SECONDS = 0.5  # Delay between API calls


async def backfill_embeddings() -> tuple[int, int]:
    """
    Generate embeddings for all notes without one.

    Returns:
        Tuple of (processed_count, failed_count)
    """
    async with AsyncSessionLocal() as db:
        # Find notes without embeddings
        result = await db.execute(select(Note).filter(Note.embedding.is_(None)))
        notes = result.scalars().all()

        total = len(notes)
        if total == 0:
            logger.info("All notes already have embeddings. Nothing to do.")
            return (0, 0)

        logger.info(f"Found {total} notes without embeddings. Starting backfill...")

        processed = 0
        failed = 0

        for i, note in enumerate(notes, 1):
            logger.info(f"[{i}/{total}] Processing note '{note.title}' ({note.id})")

            embedding = await generate_embedding(cast(str, note.content))

            if embedding is not None:
                note.embedding = embedding  # type: ignore[assignment]
                await db.commit()
                processed += 1
                logger.info(f"  -> Embedded successfully ({len(embedding)} dimensions)")
            else:
                failed += 1
                logger.warning("  -> Failed to generate embedding")

            # Rate limit (skip delay on last item)
            if i < total:
                time.sleep(RATE_LIMIT_SECONDS)

        logger.info(f"Backfill complete: {processed} succeeded, {failed} failed out of {total} total")
        return (processed, failed)


def main():
    """Entry point for CLI usage."""
    import os

    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is not set. Cannot generate embeddings.")
        sys.exit(1)

    processed, failed = asyncio.run(backfill_embeddings())

    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
