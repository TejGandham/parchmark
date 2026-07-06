"""
Shared frontend/backend markdown title-parity fixture.

Loads testdata/markdown-parity.json (a single case list shared with the
frontend's ui/src/features/notes/__tests__/markdownParity.test.ts) and
asserts the backend markdown helpers produce the same title/stripped
output the frontend helpers produce for the same input. Keeps the two
implementations honest without relying on convention alone.
"""

import json
from pathlib import Path

import pytest

from app.utils.markdown import markdown_service

_REPO_ROOT = Path(__file__).resolve().parents[4]
_FIXTURE_PATH = _REPO_ROOT / "testdata" / "markdown-parity.json"

with _FIXTURE_PATH.open(encoding="utf-8") as _fixture_file:
    _CASES = json.load(_fixture_file)


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case["name"])
def test_markdown_parity_extract_title(case):
    """extract_title matches the shared fixture's expected title."""
    assert markdown_service.extract_title(case["markdown"]) == case["title"]


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case["name"])
def test_markdown_parity_remove_h1(case):
    """remove_h1 matches the shared fixture's expected stripped content."""
    assert markdown_service.remove_h1(case["markdown"]) == case["stripped"]


def test_markdown_parity_fixture_has_every_category():
    """The fixture covers all seven agreed title/strip categories."""
    names = {case["name"] for case in _CASES}
    assert names == {
        "plain-h1-with-body",
        "h1-extra-whitespace-and-trailing-spaces",
        "blank-lines-before-h1",
        "h1-only-document",
        "multiple-h1s",
        "sub-headings-preserved",
        "hash-in-code-fence-after-h1",
    }
