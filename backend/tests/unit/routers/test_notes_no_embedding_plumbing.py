"""
Static-analysis tests for F12: oracle assertions 0 and 1.

These tests do NOT execute the notes router. They parse
``backend/app/routers/notes.py`` and assert that the embedding
background-task plumbing has been removed. They are intentionally
RED on the unmodified main branch; the implementer makes them pass.

Oracle pointers:
  /features/0/oracle/assertions/0
  /features/0/oracle/assertions/1
"""

import ast
import pathlib

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOTES_PY = (
    pathlib.Path(__file__).parent.parent.parent.parent  # backend/
    / "app"
    / "routers"
    / "notes.py"
)


def _source() -> str:
    return _NOTES_PY.read_text(encoding="utf-8")


def _function_body_source(func_name: str, source: str) -> str:
    """
    Return the source text of a top-level function's body.

    Uses AST to locate the function, then slices the original source by line
    number so comments and string literals are included in the check.
    Raises AssertionError if the function is not found.
    """
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == func_name:
            # node.body: first stmt through end_lineno of last stmt
            first_line = node.body[0].lineno - 1  # 0-based
            last_line = node.end_lineno  # 1-based inclusive → exclusive slice
            return "".join(lines[first_line:last_line])
    raise AssertionError(f"Function '{func_name}' not found in {_NOTES_PY}")


# ---------------------------------------------------------------------------
# /features/0/oracle/assertions/0
# `_generate_embedding_background` must be absent from the entire file.
# ---------------------------------------------------------------------------


def test_generate_embedding_background_absent_from_file():
    """
    Oracle assertion /features/0/oracle/assertions/0.

    ``_generate_embedding_background`` must not appear anywhere in
    ``backend/app/routers/notes.py`` after F12 lands.
    """
    source = _source()
    assert "_generate_embedding_background" not in source, (
        "Contract breach: `_generate_embedding_background` still present in "
        f"{_NOTES_PY}. "
        "See /features/0/contract/_generate_embedding_background (expected: deleted)."
    )


# ---------------------------------------------------------------------------
# /features/0/oracle/assertions/1
# `background_tasks.add_task` must be absent from create_note's body.
# ---------------------------------------------------------------------------


def test_background_tasks_add_task_absent_from_create_note():
    """
    Oracle assertion /features/0/oracle/assertions/1 (create_note half).

    ``background_tasks.add_task`` must not appear inside the body of
    ``create_note`` after F12 lands.
    """
    source = _source()
    body = _function_body_source("create_note", source)
    assert "background_tasks.add_task" not in body, (
        "Contract breach: `background_tasks.add_task` still present in "
        f"create_note body in {_NOTES_PY}. "
        "See /features/0/contract/background_task_calls_in_create_note (expected: absent)."
    )


# ---------------------------------------------------------------------------
# /features/0/oracle/assertions/1
# `background_tasks.add_task` must be absent from update_note's body.
# ---------------------------------------------------------------------------


def test_background_tasks_add_task_absent_from_update_note():
    """
    Oracle assertion /features/0/oracle/assertions/1 (update_note half).

    ``background_tasks.add_task`` must not appear inside the body of
    ``update_note`` after F12 lands.
    """
    source = _source()
    body = _function_body_source("update_note", source)
    assert "background_tasks.add_task" not in body, (
        "Contract breach: `background_tasks.add_task` still present in "
        f"update_note body in {_NOTES_PY}. "
        "See /features/0/contract/background_task_calls_in_update_note (expected: absent)."
    )
