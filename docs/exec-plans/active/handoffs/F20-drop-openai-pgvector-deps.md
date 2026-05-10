# F20 — Drop openai and pgvector dependencies from pyproject.toml

---
status: IN-PROGRESS
pipeline: backend
prd_ref: docs/exec-plans/prds/remove-for-you.json#F20
spec_ref: docs/exec-plans/prds/remove-for-you.json#F20

# Pre-check routing (set by pre-check, read by orchestrator)
intent: mid-sized
complexity: standard
designer_needed: NO
researcher_needed: NO
safety_auditor_needed: YES
arch_advisor_needed: YES
implementer_needed: YES

# Gate verdicts (set by orchestrator after each gate agent)
spec_review_verdict:
spec_review_attempt: 0
safety_verdict:
safety_attempt: 0
code_review_verdict:
code_review_attempt: 0
arch_advisor_verdict:

# Arch-advisor re-run counters (separate from initial gate passes)
arch_retry_spec_review_attempt: 0
arch_retry_safety_attempt: 0

# Pipeline configuration
remote_name: origin
roundtable_enabled: true
pr_url:

# Roundtable pre-check review (Step 1.3)
roundtable_precheck_attempt: 1
roundtable_precheck_verdict: CONCERNS

# Roundtable design review (Step 2.5)
roundtable_design_attempt: 0
roundtable_design_verdict:
roundtable_skipped:

# Roundtable landing review (Step 8.5)
roundtable_landing_attempt: 0
roundtable_landing_verdict:

# Roundtable-triggered gate re-run counters (separate from initial passes)
roundtable_retry_code_review_attempt: 0
roundtable_retry_spec_review_attempt: 0
roundtable_retry_safety_attempt: 0

# Doc-gardener (Step 9 sub-step 1)
doc_garden_verdict:
doc_garden_drift_count: 0
---

## pre-check

## Execution Brief: Drop openai and pgvector dependencies from pyproject.toml

**PRD:** docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F20
**Feature index:** 8
**Feature pointer base:** /features/8
**Layer:** foundation
**PRD-level invariants:** none
**Prototype mode:** none
**Dependencies:** MET — F15 [x] (OpenAI/embeddings deletion) and F19 [x] (Alembic drop migration + Note model update) both checked off in `docs/exec-plans/active/feature-backlog.md` (lines 19, 73).
**Research needed:** NO — `uv` and Alembic are already in routine use.
**Designer needed:** NO — pure dependency/config edit, no UI.
**Implementer needed:** YES — must edit `backend/pyproject.toml` and run `uv sync` to regenerate `backend/uv.lock`.
**Safety auditor needed:** YES — touches dependency surface; the migration-history hazard below interacts with database/migrations infrastructure (invariants 6–7's reliability/auth surfaces depend on alembic load succeeding at app startup).
**Arch-advisor needed:** NO — no structural change beyond the dependency removal.

**Intent:** mid-sized
**Complexity:** standard

> ### CRITICAL HALT RECOMMENDATION — Migration-history hazard (oracle inconsistency)
>
> The F19 roundtable landing review unanimously flagged this. Two Alembic
> revision files import `pgvector.sqlalchemy.Vector` at **module load time**:
>
> 1. `backend/migrations/versions/49f4bec52ca3_convert_embedding_to_pgvector.py:12`
> 2. `backend/migrations/versions/7f1c343772e8_drop_embedding_columns_and_pgvector.py:13`
>    (the F19 migration; its `downgrade()` body uses `Vector(1536)` to recreate
>    the column at line 52)
>
> Alembic loads every revision file in `migrations/versions/` into the Python
> interpreter to build its dependency graph **before** any command runs. Once
> F20 removes `pgvector` from `pyproject.toml` and `uv sync` uninstalls it,
> any invocation of `alembic` (including app startup with
> `APPLY_MIGRATIONS=true`, the dev compose stack, and the F19 round-trip
> upgrade/downgrade test) will raise `ModuleNotFoundError: No module named
> 'pgvector'` at file-load time, before reaching `upgrade()`/`downgrade()`.
>
> The F20 oracle is therefore **internally inconsistent**:
>
> - Assertion 4 excludes `migrations/versions/` from the ripgrep scope (the
>   drafter knew historical files retain the imports).
> - Assertion 3 requires `make test-backend-all` to pass — but `pytest` (under
>   `make test-backend-pytest-limited`) brings up app/services that exercise
>   alembic, and CI exercises the F19 round-trip downgrade.
>
> **Recommendation: HALT. Re-run `/keel-refine` to amend F20's contract** before
> proceeding, matching the F15/F19 precedent. Three resolution options
> surfaced by the F19 roundtable:
>
> | Option | Approach | Trade-off |
> |-|-|-|
> | (a) | Rewrite both migrations' `downgrade()` (and 49f4bec52ca3's `upgrade()`) to use raw `op.execute("ALTER TABLE notes ADD COLUMN embedding vector(1536)")` and drop the module-level `from pgvector.sqlalchemy import Vector` | Cleanest; preserves reversibility; eliminates the import from history entirely |
> | (b) | Move `from pgvector.sqlalchemy import Vector` inside each `downgrade()` (lazy import) | Smallest diff, but downgrade still requires `pgvector` installed at runtime — fails F19's CI round-trip test if run after F20 lands |
> | (c) | Replace both `downgrade()` bodies with `raise NotImplementedError("F19 is irreversible: pgvector removed in F20")` and document the irreversibility in F20's PRD | Acknowledges the product decision; loses round-trip testability |
>
> Recommended option for `/keel-refine`: **(a)** — preserves reversibility,
> removes the dangling import cleanly, and matches the spirit of "drop
> pgvector entirely" without sacrificing migration safety.

**What to build (post-amend):**
Remove `openai>=1.0.0` and `pgvector>=0.4.2` from `backend/pyproject.toml`'s
`[project].dependencies`, then run `uv sync` from `backend/` to regenerate
`backend/uv.lock`. After amend, also rewrite the two migrations' pgvector
references (option (a) above) so neither file imports `pgvector` at module
load time.

**New files:**
- (none)

**Modified files:**
- `backend/pyproject.toml` — drop the two lines from `[project].dependencies`.
- `backend/uv.lock` — regenerated by `uv sync` (do not hand-edit).
- (post-amend) `backend/migrations/versions/49f4bec52ca3_convert_embedding_to_pgvector.py` — replace `from pgvector.sqlalchemy import Vector` import + `Vector(1536)` usages with raw SQL `op.execute(...)` calls.
- (post-amend) `backend/migrations/versions/7f1c343772e8_drop_embedding_columns_and_pgvector.py` — same treatment for the `downgrade()` body.

**Existing patterns to follow:**
- `backend/pyproject.toml:[project].dependencies` — flat list of `package>=ver`; preserve TOML formatting.
- `backend/migrations/versions/33a4da6b0cac_add_embedding_to_notes.py` — predecessor migration; uses `sa.JSON()` and shows the no-pgvector style.
- `backend/Makefile`-driven `make test-backend-all` — gate; runs ruff + ty + pytest with testcontainers.

**Assertion traceability:**
- `/features/8/oracle/assertions/0` → grep `[project].dependencies` block of `backend/pyproject.toml` for `openai`/`pgvector` post-edit; expect zero.
- `/features/8/oracle/assertions/1` → run `cd backend && uv sync` post-edit; expect exit 0 and `uv.lock` updated.
- `/features/8/oracle/assertions/2` → run `make test-backend-all` from repo root; expect exit 0. **This is where the migration hazard manifests if not pre-amended.**
- `/features/8/oracle/assertions/3` → `cd backend && rg -n "^(from|import) (openai|pgvector)" --glob '!.venv' --glob '!migrations/versions/' .`; expect zero matches (already verified zero pre-edit).

**Edge cases:**
- `uv.lock` may show transitive removals beyond `openai`/`pgvector` (e.g., `httpx-sse`, `numpy` if only used by them). Inspect the diff but do not hand-prune.
- `pgvector` may still appear in `uv.lock` transitively if any other package depends on it (none expected).
- `make test-backend-all` runs alembic-touching code paths; the migration-history hazard is the dominant risk.

**Risks:**
- **Primary:** Migration-history hazard above — addressed only by `/keel-refine` amend.
- Hidden lockfile transitive churn could surprise reviewers; flag any unexpected removals in implementer's PR description.
- `OPENAI_API_KEY` references in `.env.example` / docs (out of scope here, but worth a sanity check) should already be cleaned by F15.

**Verify command:** `make test-backend-all` (from repo root)

**Path convention:** Backend lives under `backend/app/` (FastAPI). Migrations
under `backend/migrations/versions/`. Run all `uv` commands from `backend/`.

**Constraints for downstream:**
- MUST: regenerate `backend/uv.lock` via `cd backend && uv sync` (never hand-edit).
- MUST: keep `[project].dependencies` formatting consistent (one entry per line, alphabetical if neighbours are).
- MUST NOT: proceed with implementation until `/keel-refine` amends the F20 contract to cover the two migration files (option (a) recommended).
- MUST NOT: add new dependencies; this feature is strictly subtractive.
- MUST NOT: scope-creep into `.env.example` cleanup or doc edits — those belong to a separate feature if needed.

**AI-slop watchlist:**
- Do not "tidy" unrelated `pyproject.toml` sections (tool tables, ruff config) — strictly subtractive on `[project].dependencies`.
- Do not add a CHANGELOG entry, README note, or migration comment unless asked.
- Do not preemptively prune `OPENAI_API_KEY` from `.env.example` or docs.

**Ready:** NO — F20 contract is internally inconsistent with the existing migration history (see HALT block). Recommend `/keel-refine docs/exec-plans/prds/remove-for-you.json` to amend F20 (preferred: option (a)) before resuming `/keel-pipeline F20`.
**Next hop (after amend):** test-writer

### Resolved feature (verbatim from keel-feature-resolve.py)

```json
{
  "ok": true,
  "feature_id": "F20",
  "feature_index": 8,
  "feature_pointer_base": "/features/8",
  "prd_path": "/home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json",
  "canonical_prd_path": "/home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json",
  "title": "Drop openai and pgvector dependencies from pyproject.toml",
  "layer": "foundation",
  "oracle": {
    "type": "integration",
    "assertions": [
      "grep of `backend/pyproject.toml` `[project]` dependency list for `openai` and `pgvector` returns zero matches.",
      "`uv sync` against the updated `pyproject.toml` and `uv.lock` succeeds.",
      "Full backend test suite (`make test-backend-all`) runs to completion with all tests passing.",
      "ripgrep `^(from|import) (openai|pgvector)` across `backend/` (excluding `.venv` and `migrations/versions/` historical files) returns zero matches."
    ],
    "tooling": "uv; pytest; ripgrep."
  },
  "contract": {
    "pyproject_toml_dependencies_removed": [
      "openai>=1.0.0",
      "pgvector>=0.4.2"
    ],
    "uv_lock_updated": "regenerated"
  },
  "needs": [
    "F15",
    "F19"
  ],
  "prd_invariants_exercised": [],
  "backlog_fields": {
    "prd_slug": "remove-for-you",
    "prd_exempt_reason": null,
    "spec_ref": null,
    "design_refs": [],
    "needs_ids": [
      "F15",
      "F19"
    ],
    "human_markers": [],
    "prototype_mode": null
  },
  "classification": "JSON_PRD_PATH"
}
```

### Constraints for downstream
- MUST: halt on this brief and re-run `/keel-refine` to amend F20's contract before any test/impl work.
- MUST: post-amend, regenerate `backend/uv.lock` via `cd backend && uv sync` (never hand-edit).
- MUST NOT: proceed to test-writer until the migration-history hazard is resolved in the contract.
- MUST NOT: add or "tidy" unrelated entries in `pyproject.toml`; strictly subtractive on `[project].dependencies`.
- MUST NOT: scope-creep into `.env.example` / doc cleanup.

## roundtable-precheck-review

### Attempt 1 — CONCERNS

#### Critique
Multi-model crosscheck (Claude / Codex / Gemini) on F20's pre-check classification + amendment options.

**Routing flag consensus — flip `arch_advisor_needed: true`** (was NO):
- Claude: editing already-merged migrations perforates a structural convention; needs second opinion.
- Codex: change spans Alembic history graph, Docker startup, testcontainers migration tests, and fresh-environment boot semantics — above routine "standard" work.
- Gemini: modifying historical migration execution paths is a structural database change.

Other routing flags (intent: mid-sized, complexity: standard, designer/researcher: NO, safety: YES, implementer: YES) are correct.

**Option choice — Option (a) wins, hybrid (a+c) is the runner-up:**
- Claude: Option (a) — preserves reversibility for legitimate same-deploy ops rollbacks; (b) is dominated; (c) blocks emergency rollback for no real gain.
- Codex: Option (a) — only option that removes the Python dep AND keeps alembic loadable AND keeps full-history upgrades viable. Specifically rebuts (c): stubbing only `downgrade()` does NOT fix the module-load-time import in `49f4bec52ca3.upgrade()` — (c) alone is insufficient and must be expanded into effectively (a) for the upgrade path.
- Gemini: Hybrid (a + c) — raw SQL for `49f4bec52ca3.upgrade()` (allows fresh DB build) + `NotImplementedError` for F19's `downgrade()` (acknowledges semantic irreversibility — embedding data is gone forever).

**Option (b) is dominated** by all three: lazy-import inside `downgrade()` doesn't help `49f4bec52ca3.upgrade()`'s module-level need (still breaks fresh-DB upgrade), creates asymmetric eager-load-OK / runtime-fail behavior, breaks F19's CI round-trip test anyway, and trips ruff PLC0415.

#### Canvass — CRITICAL: scope expansion needed (consensus across all three models)

The pgvector surface lives in MANY places beyond the two migration files. The current F20 contract (only `pyproject.toml` + `uv.lock`) is incomplete. Must extend to:

| Surface | File | Action |
|-|-|-|
| Test image | `backend/tests/conftest.py:55` | Swap `PostgresContainer("pgvector/pgvector:pg17")` → `PostgresContainer("postgres:17")` |
| Test extension | `backend/tests/conftest.py:59` | Remove `conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))` |
| Dev compose | `docker-compose.dev.yml:7` | `image: pgvector/pgvector:pg17` → `image: postgres:17` |
| Stack compose | `docker-compose.yml:7` | Same swap |
| Prod compose | `docker-compose.prod.yml:3` | Same swap (production deploy surface) |
| OIDC-test compose | `docker-compose.oidc-test.yml` | Same swap |
| Migration test image | `backend/tests/integration/migrations/test_f19_drop_embedding.py` | **DO NOT swap** — F19's downgrade test needs pgvector to recreate `vector(1536)` via the rewritten raw DDL. Keep this image as-is and document the asymmetry. |
| Lockfile | `backend/uv.lock` | Already in contract — regen via `uv sync` |
| Docs | `backend/README.md` and others | Out of F20 scope; deferred to F21 doc sweep — flag for landing-verifier so it doesn't false-flag. |

Without this extension, F20 ships a half-removal. Compose files referencing pgvector retain unused image weight + security surface, and conftest's CREATE EXTENSION call against a vanilla postgres image would fail in CI.

#### Recommendation summary
**HALT-AND-AMEND** (unanimous). Run `/keel-refine` to amend F20:
1. Flip `arch_advisor_needed: YES` in handoff routing.
2. Add `migrations_rewritten: ["49f4bec52ca3_*.py", "7f1c343772e8_*.py"]` to contract — both upgrade + downgrade paths use raw `op.execute()` DDL; module-level pgvector imports removed.
3. Add `conftest_py: {testcontainer_image: "postgres:17", create_extension_vector_line: "removed"}` to contract.
4. Add `docker_compose_files_image_swap: [...4 files...]` to contract.
5. Add oracle assertions: alembic loads cleanly without pgvector installed, `make test-backend-all` passes, GET /api/notes/ + CRUD against vanilla postgres image succeeds, ripgrep `pgvector|^(from|import) (openai|pgvector)` across `backend/` (excluding `.venv`, `migrations/versions/` once rewritten, and `tests/integration/migrations/test_f19_*.py`) returns zero.
6. Note F21 deferral for doc surfaces (`backend/README.md`, `AGENTS.md`, `core-beliefs.md`, etc.).

**Product-decision question for the human:**
- Pure (a): F19's `downgrade()` recreates the `embedding vector(1536)` column via raw SQL. Empty data, but schema-rollback is mechanically possible.
- Hybrid (a + c): F19's `downgrade()` raises `NotImplementedError("F19+F20 is irreversible: pgvector removed and embedding data destroyed")`. Honest about the product decision; loses round-trip testability for F19.

**roundtable_precheck_verdict: CONCERNS** (routing flag flip + contract gap)

## researcher
<!-- Research brief (snapshot, if applicable) -->

### Decisions (optional)

## arch-advisor-consultation
<!-- Architecture guidance (snapshot, if applicable) -->

### Constraints for downstream

## backend-designer / frontend-designer
<!-- Design brief (snapshot, if applicable) -->

### Decisions
### Constraints for downstream

## roundtable-design-review
<!-- Multi-model advisory review of designer output (Step 2.5, append-only Attempt N blocks). -->

## test-writer
<!-- Test report (snapshot) -->

### Decisions (optional)

## implementer
<!-- Implementation report (snapshot) -->

### Decisions

## code-reviewer
<!-- Code quality review (snapshot). Verdict: APPROVED | CHANGES NEEDED. -->

## spec-reviewer
<!-- Conformance report (snapshot). Verdict: CONFORMANT | DEVIATION. -->

## safety-auditor
<!-- Audit report (snapshot, if applicable). Verdict: PASS | VIOLATION. -->

## arch-advisor-verification
<!-- Independent structural review (snapshot, if applicable). -->

## landing-verifier
<!-- Landing report (snapshot) -->

## roundtable-landing-review
<!-- Multi-model advisory review (Step 8.5, append-only Attempt N blocks). -->
