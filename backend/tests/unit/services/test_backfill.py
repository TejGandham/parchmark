"""
Unit tests for the backfill embeddings service.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.models import Note
from app.services.backfill import backfill_embeddings, main


@pytest.mark.asyncio
async def test_backfill_embeddings_processes_notes_without_embeddings():
    """Test that backfill_embeddings processes notes without embeddings."""
    mock_note1 = MagicMock(spec=Note)
    mock_note1.id = "note-1"
    mock_note1.title = "Note 1"
    mock_note1.content = "Content 1"
    mock_note1.embedding = None

    mock_note2 = MagicMock(spec=Note)
    mock_note2.id = "note-2"
    mock_note2.title = "Note 2"
    mock_note2.content = "Content 2"
    mock_note2.embedding = None

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_note1, mock_note2]
    mock_db.execute.return_value = mock_result

    with patch("app.services.backfill.AsyncSessionLocal") as mock_session_factory:
        mock_session_factory.return_value.__aenter__.return_value = mock_db
        with patch("app.services.backfill.generate_embedding") as mock_generate:
            mock_generate.side_effect = [[0.1, 0.2], [0.3, 0.4]]

            processed, failed = await backfill_embeddings()

            assert processed == 2
            assert failed == 0
            assert mock_note1.embedding == [0.1, 0.2]
            assert mock_note2.embedding == [0.3, 0.4]
            assert mock_db.commit.call_count == 2


@pytest.mark.asyncio
async def test_backfill_embeddings_skips_when_all_have_embeddings():
    """Test that backfill_embeddings returns (0, 0) when all notes have embeddings."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    with patch("app.services.backfill.AsyncSessionLocal") as mock_session_factory:
        mock_session_factory.return_value.__aenter__.return_value = mock_db

        processed, failed = await backfill_embeddings()

        assert processed == 0
        assert failed == 0
        assert mock_db.commit.call_count == 0


@pytest.mark.asyncio
async def test_backfill_embeddings_counts_failures():
    """Test that backfill_embeddings counts failures correctly."""
    mock_note1 = MagicMock(spec=Note)
    mock_note1.id = "note-1"
    mock_note1.title = "Note 1"
    mock_note1.content = "Content 1"
    mock_note1.embedding = None

    mock_note2 = MagicMock(spec=Note)
    mock_note2.id = "note-2"
    mock_note2.title = "Note 2"
    mock_note2.content = "Content 2"
    mock_note2.embedding = None

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_note1, mock_note2]
    mock_db.execute.return_value = mock_result

    with patch("app.services.backfill.AsyncSessionLocal") as mock_session_factory:
        mock_session_factory.return_value.__aenter__.return_value = mock_db
        with patch("app.services.backfill.generate_embedding") as mock_generate:
            mock_generate.side_effect = [None, [0.5, 0.6]]

            processed, failed = await backfill_embeddings()

            assert processed == 1
            assert failed == 1
            assert mock_db.commit.call_count == 1


def test_main_exits_with_error_when_openai_api_key_not_set():
    """Test that main() exits with error when OPENAI_API_KEY is not set."""
    with patch.dict(os.environ, {}, clear=False):
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1


def test_main_exits_with_code_1_when_failures_occur():
    """Test that main() exits with code 1 when failures occur."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        with patch("app.services.backfill.asyncio.run") as mock_run:
            mock_run.return_value = (1, 1)

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1


def test_main_exits_with_code_0_when_all_succeed():
    """Test that main() exits with code 0 when all embeddings succeed."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        with patch("app.services.backfill.asyncio.run") as mock_run:
            mock_run.return_value = (5, 0)

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0
