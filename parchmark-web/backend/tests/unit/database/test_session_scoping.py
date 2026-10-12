"""
Static-analysis test for async-session-enforcement (backend-hygiene binder).

Every database session must be request-scoped via `Depends(get_async_db)`.
The only place allowed to construct the session factory at import time is
`app/database/database.py` (`AsyncSessionLocal = async_sessionmaker(...)`).
This test parses every ``backend/app/**/*.py`` file with the standard
library ``ast`` module and fails if any other module calls ``AsyncSession``
or ``AsyncSessionLocal`` outside a function/async function body -- i.e. at
module scope or directly in a class body, where the call would execute at
import time instead of per-request.

The tree already honors the rule; this test exists to catch regressions.
"""

from __future__ import annotations

import ast
import pathlib

_APP_ROOT = pathlib.Path(__file__).parent.parent.parent.parent / "app"
_EXEMPT_FILE = _APP_ROOT / "database" / "database.py"
_FLAGGED_NAMES = frozenset({"AsyncSession", "AsyncSessionLocal"})


class _ImportTimeSessionVisitor(ast.NodeVisitor):
    """Collects Calls to a flagged name that execute at import time.

    A call executes at import time if it is not nested inside any
    FunctionDef/AsyncFunctionDef body. Function bodies are deferred (they
    only run when called), so this visitor stops descending into them --
    only a function's decorators and default-argument expressions still
    execute at definition time and are checked.
    """

    def __init__(self) -> None:
        self.violations: list[ast.Call] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_def_time_expressions(node)
        # Do NOT recurse into node.body -- it only runs when called.

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_def_time_expressions(node)

    def _visit_def_time_expressions(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)

    def visit_Call(self, node: ast.Call) -> None:
        callee = node.func
        if isinstance(callee, ast.Name):
            name = callee.id
        elif isinstance(callee, ast.Attribute):
            name = callee.attr
        else:
            name = None
        if name in _FLAGGED_NAMES:
            self.violations.append(node)
        self.generic_visit(node)


def _find_import_time_session_calls(source: str) -> list[ast.Call]:
    """Return every flagged-name Call in ``source`` that executes at import time."""
    tree = ast.parse(source)
    visitor = _ImportTimeSessionVisitor()
    visitor.visit(tree)
    return visitor.violations


def _iter_app_files() -> list[pathlib.Path]:
    return sorted(_APP_ROOT.rglob("*.py"))


# ---------------------------------------------------------------------------
# Unit tests for the detection rule itself, against synthetic source.
# ---------------------------------------------------------------------------


def test_module_level_call_is_flagged():
    source = "from app.database.database import AsyncSessionLocal\n\ndb = AsyncSessionLocal()\n"
    violations = _find_import_time_session_calls(source)
    assert len(violations) == 1
    assert violations[0].lineno == 3


def test_class_body_call_is_flagged():
    source = "class Foo:\n    db = AsyncSessionLocal()\n"
    violations = _find_import_time_session_calls(source)
    assert len(violations) == 1
    assert violations[0].lineno == 2


def test_dotted_attribute_call_is_flagged():
    source = "import app.database.database as database\n\ndb = database.AsyncSessionLocal()\n"
    violations = _find_import_time_session_calls(source)
    assert len(violations) == 1
    assert violations[0].lineno == 3


def test_function_scoped_call_is_allowed():
    """Mirrors app/database/seed.py: construction inside a function body is fine."""
    source = "async def seed():\n    db = AsyncSessionLocal()\n    return db\n"
    violations = _find_import_time_session_calls(source)
    assert violations == []


def test_call_nested_in_method_of_module_level_class_is_allowed():
    source = "class Foo:\n    def bar(self):\n        return AsyncSessionLocal()\n"
    violations = _find_import_time_session_calls(source)
    assert violations == []


def test_unrelated_module_level_call_is_not_flagged():
    source = "from sqlalchemy import create_engine\n\nengine = create_engine('sqlite://')\n"
    violations = _find_import_time_session_calls(source)
    assert violations == []


# ---------------------------------------------------------------------------
# Integration test: scan every file under backend/app.
# ---------------------------------------------------------------------------


def test_no_app_module_constructs_session_at_import_time():
    """
    No file under backend/app (other than app/database/database.py) may call
    AsyncSession(...) or AsyncSessionLocal(...) outside a function body.
    """
    failures: list[str] = []

    for path in _iter_app_files():
        if path == _EXEMPT_FILE:
            continue
        source = path.read_text(encoding="utf-8")
        for call in _find_import_time_session_calls(source):
            rel_path = path.relative_to(_APP_ROOT.parent)
            failures.append(f"{rel_path}:{call.lineno}")

    assert not failures, (
        "Found session construction at import time (must be request-scoped via "
        f"Depends(get_async_db) instead): {', '.join(failures)}"
    )
