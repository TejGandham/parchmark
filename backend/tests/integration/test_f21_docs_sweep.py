"""
Static-check tests for F21: Documentation sweep — remove embedding /
access-tracking references and retire invariants 6 + 7.

Oracle: /features/9/oracle
Contract: /features/9/contract

Assertions covered here:

  /features/9/oracle/assertions/0  — ripgrep of each literal in
    `grep_clean_literals` across the working tree (excluding the PRD file,
    .git/, and the F19 round-trip test file) returns zero matches.

  /features/9/oracle/assertions/1  — docs/design-docs/core-beliefs.md no
    longer documents invariants 6 or 7 as active rules.

  /features/9/oracle/assertions/2  — docs/design-docs/core-beliefs.md no
    longer lists _generate_embedding_background or services/backfill.py
    under invariant 1's exempt helpers.

  /features/9/oracle/assertions/3  — docs/design-docs/core-beliefs.md no
    longer lists the CREATE EXTENSION IF NOT EXISTS vector site under
    invariant 3.

  /features/9/oracle/assertions/4  — docs/design-docs/core-beliefs.md no
    longer cites /notes/{id}/access as an example under invariant 4.

  /features/9/oracle/assertions/5  — ARCHITECTURE.md no longer contains an
    ### Embeddings & Similarity heading.

  /features/9/oracle/assertions/6  — docs/ai-embeddings-design.md is either
    absent from docs/ or relocated under docs/design-docs/archive/.

All checks use pure-Python (re + Path.read_text) — matching the idiom of
test_f20_static_checks.py.
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Root paths
# ---------------------------------------------------------------------------
# This file lives at backend/tests/integration/test_f21_docs_sweep.py
# parents[0] = integration/
# parents[1] = tests/
# parents[2] = backend/
# parents[3] = repo root
_BACKEND_ROOT = Path(__file__).parents[2]  # backend/
_REPO_ROOT = _BACKEND_ROOT.parent  # repo root

_CORE_BELIEFS = _REPO_ROOT / "docs" / "design-docs" / "core-beliefs.md"
_ARCHITECTURE_MD = _REPO_ROOT / "ARCHITECTURE.md"
_AI_EMBEDDINGS_DESIGN_DOCS_ROOT = _REPO_ROOT / "docs" / "ai-embeddings-design.md"
_AI_EMBEDDINGS_ARCHIVE = _REPO_ROOT / "docs" / "design-docs" / "archive" / "ai-embeddings-design.md"

# ---------------------------------------------------------------------------
# Whitelisted residual paths and directories.
#
# Justification categories (mirrors PRD acceptable_residual_locations):
#   (A) PRD source-of-record — names every literal by definition.
#   (B) git-history / historical record — immutable, must not be touched.
#   (C) Prior-feature absence-assertion contract tests — intentionally contain
#       the literals in order to assert those literals are absent from product
#       code.  Deleting or scrubbing them would remove prior-feature regression
#       gates.
#   (D) Python / JS / build cache artefacts — transient, gitignored; walking
#       them would produce unstable, environment-dependent results.
#   (E) Alembic migration history — immutable per CLAUDE.md §"Migration history
#       conventions"; filenames and bodies legitimately contain embedding /
#       pgvector.
#   (F) Active pipeline records that reference retired literals as PRD-derived
#       titles or historical annotations.
# ---------------------------------------------------------------------------

# Individual file exclusions (exact-path match after resolve()).
_GREP_EXCLUSIONS: set[Path] = {
    # (A) The PRD itself
    _REPO_ROOT / "docs" / "exec-plans" / "prds" / "remove-for-you.json",
    # (B) F19 round-trip test — keeps "pgvector/pgvector:pg17" per F20 contract
    _BACKEND_ROOT / "tests" / "integration" / "migrations" / "test_f19_drop_embedding.py",
    # (B) F21 handoff — lists the literals being swept
    _REPO_ROOT / "docs" / "exec-plans" / "active" / "handoffs" / "F21-docs-sweep-remove-for-you.md",
    # (C) This very file — declares the literal list on its own lines
    Path(__file__),
    # (C) F20 contract tests — assert embedding/pgvector absent from app code
    _BACKEND_ROOT / "tests" / "integration" / "migrations" / "test_f20_static_checks.py",
    _BACKEND_ROOT / "tests" / "integration" / "migrations" / "test_f20_brownfield_rewrites.py",
    _BACKEND_ROOT / "tests" / "integration" / "migrations" / "test_f19_consumer_cleanup.py",
    # (C) F19/F15 boot / plumbing absence tests
    _BACKEND_ROOT / "tests" / "integration" / "test_app_boot_no_openai.py",
    _BACKEND_ROOT / "tests" / "integration" / "notes" / "test_notes_no_embedding_plumbing.py",
    _BACKEND_ROOT / "tests" / "unit" / "routers" / "test_notes_no_embedding_plumbing.py",
    # (C) F13/F14 endpoint-removal contract tests
    _BACKEND_ROOT / "tests" / "integration" / "notes" / "test_endpoint_removal.py",
    # (C) UI deletion-contract tests (F16/F17/F18) — assert absence of retired symbols
    _REPO_ROOT / "ui" / "src" / "__tests__" / "utils" / "noteScoring.f18-deletion.test.ts",
    _REPO_ROOT / "ui" / "src" / "__tests__" / "features" / "ui" / "components" / "CommandPalette.f16-deletion.test.tsx",
    _REPO_ROOT
    / "ui"
    / "src"
    / "__tests__"
    / "features"
    / "notes"
    / "components"
    / "NotesExplorer.f17-deletion.test.tsx",
    # (C) UI deletion-contract test (F17) — asserts absence of For-You header via data-testid + /for you/i regex
    _REPO_ROOT / "ui" / "src" / "__tests__" / "features" / "notes" / "components" / "NotesExplorer.test.tsx",
}

# Directory-prefix exclusions (relative to repo root; matched as prefix or part).
# Each entry must be justified by a category above.
_EXCLUDED_DIR_PARTS: tuple[str, ...] = (
    # (D) Python cache trees — transient, unstable, gitignored
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".venv",
    # (D) JS / build cache and output trees
    "node_modules",
    ".next",
    ".vite",
    "dist",
    "build",
    "coverage",
    "out",
    # (E) Alembic migration history — immutable per CLAUDE.md
    "backend/migrations/versions",
    # (B) Historical pipeline records (completed handoffs, archived plans)
    "docs/exec-plans/completed",
    # (A/B) All PRD JSON files are source-of-record documents
    "docs/exec-plans/prds",
    # (B) Archived deployment and design docs — historical, pre-KEEL artefacts
    "docs/deployment_upgrade/archive",
    "docs/design-docs/archive",
    # (F) Active backlog + tech-debt tracker reference literals as PRD-derived titles
    "docs/exec-plans/active/feature-backlog.md",
    "docs/exec-plans/tech-debt-tracker.md",
)


def _is_excluded_path(path: Path) -> bool:
    """Return True if *path* should be skipped during the literal scan."""
    if path.resolve() in {p.resolve() for p in _GREP_EXCLUSIONS}:
        return True
    rel = path.relative_to(_REPO_ROOT)
    rel_str = str(rel)
    for part in _EXCLUDED_DIR_PARTS:
        # Match both the exact path and as a path prefix component.
        if rel_str == part or rel_str.startswith(part + "/"):
            return True
        # Also match any segment in parts (handles .git, .venv, node_modules
        # no matter where they appear in the tree)
        if part in rel.parts:
            return True
    return False


def _scan_repo_for_literal(literal: str) -> list[tuple[Path, int, str]]:
    """
    Walk the entire repo tree and return (file, line_number, line_text) for
    every line containing *literal* (case-sensitive substring match), excluding
    whitelisted paths and build directories.
    """
    hits: list[tuple[Path, int, str]] = []
    for candidate in _REPO_ROOT.rglob("*"):
        if not candidate.is_file():
            continue
        if _is_excluded_path(candidate):
            continue
        try:
            text = candidate.read_text(errors="replace")
        except (OSError, PermissionError):
            continue
        if literal in text:
            for i, line in enumerate(text.splitlines(), start=1):
                if literal in line:
                    hits.append((candidate, i, line.strip()))
    return hits


# ---------------------------------------------------------------------------
# /features/9/oracle/assertions/0
# grep_clean_literals scan — zero hits across working tree (excl. whitelist).
# ---------------------------------------------------------------------------


class TestGrepCleanLiterals:
    """
    Oracle: /features/9/oracle/assertions/0
    Contract: /features/9/contract/grep_clean_literals

    For every literal in the contract list, a full working-tree scan must
    return zero matches outside the whitelisted residual locations.
    """

    # Literals are drawn verbatim from /features/9/contract/grep_clean_literals
    _LITERALS = [
        "For You",
        "noteScoring",
        "embedding",
        "OPENAI_API_KEY",
        "EMBEDDING_MODEL",
        "/similar",
        "/access",
        "pgvector",
        "SimilarNote",
    ]

    def _assert_clean(self, literal: str) -> None:
        hits = _scan_repo_for_literal(literal)
        assert hits == [], (
            f"Literal {literal!r} found in working tree after F21 sweep "
            f"({len(hits)} match(es)):\n"
            + "\n".join(f"  {p}:{i}: {line}" for p, i, line in hits[:20])
            + ("\n  ... (truncated)" if len(hits) > 20 else "")
            + "\nAll occurrences must be removed or whitelisted per F21 contract."
        )

    def test_for_you_absent(self):
        self._assert_clean("For You")

    def test_note_scoring_absent(self):
        self._assert_clean("noteScoring")

    def test_embedding_absent(self):
        self._assert_clean("embedding")

    def test_openai_api_key_absent(self):
        self._assert_clean("OPENAI_API_KEY")

    def test_embedding_model_absent(self):
        self._assert_clean("EMBEDDING_MODEL")

    def test_similar_endpoint_absent(self):
        self._assert_clean("/similar")

    def test_access_endpoint_absent(self):
        self._assert_clean("/access")

    def test_pgvector_absent(self):
        self._assert_clean("pgvector")

    def test_similar_note_type_absent(self):
        self._assert_clean("SimilarNote")


# ---------------------------------------------------------------------------
# /features/9/oracle/assertions/1
# core-beliefs.md: invariants 6 and 7 no longer present as active rules.
# ---------------------------------------------------------------------------


class TestCoreBeliefsinvariantsRetired:
    """
    Oracle: /features/9/oracle/assertions/1
    Contract: /features/9/contract/core_beliefs_md/invariant_6 == "retired"
              /features/9/contract/core_beliefs_md/invariant_7 == "retired"

    The file must not contain '### 6.' or '### 7.' headings (or equivalent
    numbered heading patterns for those invariants).  Matching on the
    heading-number prefix is sufficient — the actual wording is not under test.
    """

    def test_invariant_6_heading_absent(self):
        assert _CORE_BELIEFS.exists(), f"Missing: {_CORE_BELIEFS}"
        text = _CORE_BELIEFS.read_text()
        # Match markdown headings of any depth that start the invariant-6 block:
        # e.g. "### 6.", "## 6.", "**6."
        pattern = re.compile(r"^#+\s*6\.", re.MULTILINE)
        matches = pattern.findall(text)
        assert matches == [], (
            f"Invariant 6 heading still present in {_CORE_BELIEFS}: {matches}. " "Retire invariant 6 per F21 contract."
        )

    def test_invariant_7_heading_absent(self):
        assert _CORE_BELIEFS.exists(), f"Missing: {_CORE_BELIEFS}"
        text = _CORE_BELIEFS.read_text()
        pattern = re.compile(r"^#+\s*7\.", re.MULTILINE)
        matches = pattern.findall(text)
        assert matches == [], (
            f"Invariant 7 heading still present in {_CORE_BELIEFS}: {matches}. " "Retire invariant 7 per F21 contract."
        )


# ---------------------------------------------------------------------------
# /features/9/oracle/assertions/2
# core-beliefs.md: exempt-helpers block under invariant 1 removed.
# ---------------------------------------------------------------------------


class TestCoreBeliefsinvariant1ExemptHelpersRemoved:
    """
    Oracle: /features/9/oracle/assertions/2
    Contract: /features/9/contract/core_beliefs_md/invariant_1_exempt_helpers_block
              == "removed"

    The file must not mention _generate_embedding_background or
    services/backfill.py anywhere (these were the sole entries in the
    exempt-helpers list and have no active role post-F21).
    """

    def test_generate_embedding_background_absent(self):
        assert _CORE_BELIEFS.exists(), f"Missing: {_CORE_BELIEFS}"
        text = _CORE_BELIEFS.read_text()
        assert "_generate_embedding_background" not in text, (
            f"'_generate_embedding_background' still referenced in {_CORE_BELIEFS}. "
            "Remove from invariant 1's exempt-helpers block per F21 contract."
        )

    def test_services_backfill_absent(self):
        assert _CORE_BELIEFS.exists(), f"Missing: {_CORE_BELIEFS}"
        text = _CORE_BELIEFS.read_text()
        assert "services/backfill.py" not in text, (
            f"'services/backfill.py' still referenced in {_CORE_BELIEFS}. "
            "Remove from invariant 1's exempt-helpers block per F21 contract."
        )


# ---------------------------------------------------------------------------
# /features/9/oracle/assertions/3
# core-beliefs.md: CREATE EXTENSION IF NOT EXISTS vector site under inv. 3 removed.
# ---------------------------------------------------------------------------


class TestCoreBeliefsinvariant3VectorExtensionRemoved:
    """
    Oracle: /features/9/oracle/assertions/3
    Contract: /features/9/contract/core_beliefs_md/invariant_3_init_db_raw_sql_site
              == "removed"

    The file must not contain 'CREATE EXTENSION IF NOT EXISTS vector'.
    """

    def test_create_extension_vector_absent(self):
        assert _CORE_BELIEFS.exists(), f"Missing: {_CORE_BELIEFS}"
        text = _CORE_BELIEFS.read_text()
        assert "CREATE EXTENSION IF NOT EXISTS vector" not in text, (
            f"'CREATE EXTENSION IF NOT EXISTS vector' still present in {_CORE_BELIEFS}. "
            "Remove the raw-SQL whitelist site from invariant 3 per F21 contract."
        )


# ---------------------------------------------------------------------------
# /features/9/oracle/assertions/4
# core-beliefs.md: /notes/{id}/access example under invariant 4 removed.
# ---------------------------------------------------------------------------


class TestCoreBeliefsinvariant4AccessEndpointRemoved:
    """
    Oracle: /features/9/oracle/assertions/4
    Contract: /features/9/contract/core_beliefs_md/invariant_4_access_endpoint_example
              == "removed"

    The file must not reference '/notes/{id}/access' or 'notes/{id}/access'.
    """

    def test_access_endpoint_example_absent(self):
        assert _CORE_BELIEFS.exists(), f"Missing: {_CORE_BELIEFS}"
        text = _CORE_BELIEFS.read_text()
        # Match with or without leading slash
        assert re.search(r"/notes/\{id\}/access", text) is None, (
            f"'/notes/{{id}}/access' example still present in {_CORE_BELIEFS}. "
            "Remove from invariant 4's example list per F21 contract."
        )


# ---------------------------------------------------------------------------
# /features/9/oracle/assertions/5
# ARCHITECTURE.md: ### Embeddings & Similarity heading removed.
# ---------------------------------------------------------------------------


class TestArchitectureMdEmbeddingsSectionRemoved:
    """
    Oracle: /features/9/oracle/assertions/5
    Contract: /features/9/contract/architecture_md/embeddings_and_similarity_section
              == "deleted"

    ARCHITECTURE.md must not contain a heading '### Embeddings & Similarity'
    (or any heading depth).
    """

    def test_embeddings_and_similarity_heading_absent(self):
        assert _ARCHITECTURE_MD.exists(), f"Missing: {_ARCHITECTURE_MD}"
        text = _ARCHITECTURE_MD.read_text()
        pattern = re.compile(r"^#+\s*Embeddings\s*&\s*Similarity", re.MULTILINE)
        matches = pattern.findall(text)
        assert matches == [], (
            f"'### Embeddings & Similarity' heading still present in "
            f"{_ARCHITECTURE_MD}: {matches}. "
            "Delete the section per F21 contract."
        )


# ---------------------------------------------------------------------------
# /features/9/oracle/assertions/6
# docs/ai-embeddings-design.md is absent from docs/ root OR only present
# at docs/design-docs/archive/ai-embeddings-design.md.
# ---------------------------------------------------------------------------


class TestAiEmbeddingsDesignMdArchived:
    """
    Oracle: /features/9/oracle/assertions/6
    Contract: /features/9/contract/ai_embeddings_design_md ==
              "archived to docs/design-docs/archive/ or deleted"

    After F21:
    - docs/ai-embeddings-design.md must NOT exist at the docs/ root.
    - If archived, docs/design-docs/archive/ai-embeddings-design.md may exist.
    - Both absent == delete disposition (also valid).
    """

    def test_ai_embeddings_design_not_at_docs_root(self):
        assert not _AI_EMBEDDINGS_DESIGN_DOCS_ROOT.exists(), (
            f"docs/ai-embeddings-design.md still present at docs/ root "
            f"({_AI_EMBEDDINGS_DESIGN_DOCS_ROOT}). "
            "Archive to docs/design-docs/archive/ or delete per F21 contract."
        )
