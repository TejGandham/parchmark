# F12 Strip embedding generation from routers/notes.py

<!-- Handoff for F12 from PRD docs/exec-plans/prds/remove-for-you.json -->

---
status: READY-TO-LAND
pipeline: backend
prd_ref: docs/exec-plans/prds/remove-for-you.json#F12

# Pre-check routing (set by pre-check, read by orchestrator)
# Values are from attempt 2 after roundtable-precheck-review correction
intent: refactoring
complexity: standard
designer_needed: false
researcher_needed: false
safety_auditor_needed: true
arch_advisor_needed: false
implementer_needed: true

# Gate verdicts (set by orchestrator after each gate agent)
spec_review_verdict: CONFORMANT
spec_review_attempt: 1
safety_verdict: PASS
safety_attempt: 1
code_review_verdict: APPROVED
code_review_attempt: 1
arch_advisor_verdict:

# Arch-advisor re-run counters
arch_retry_spec_review_attempt: 0
arch_retry_safety_attempt: 0

# Pipeline configuration
remote_name: origin
roundtable_enabled: true
pr_url:

# Roundtable pre-check review (Step 1.3)
roundtable_precheck_attempt: 2
roundtable_precheck_verdict: CONCERNS

# Roundtable design review (Step 2.5)
roundtable_design_attempt: 0
roundtable_design_verdict:
roundtable_skipped:

# Roundtable landing review (Step 8.5)
roundtable_landing_attempt: 1
roundtable_landing_verdict: APPROVED

# Roundtable-triggered gate re-run counters
roundtable_retry_code_review_attempt: 0
roundtable_retry_spec_review_attempt: 0
roundtable_retry_safety_attempt: 0

# Doc-gardener (Step 9 sub-step 1)
doc_garden_verdict: DRIFT_FOUND
doc_garden_drift_count: 4
---

## pre-check
<!-- Execution brief appended here by pre-check agent -->

## Execution Brief: Strip embedding generation from routers/notes.py

**PRD:** /home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F12
**Feature index:** 0
**Feature pointer base:** /features/0
**Layer:** service
**PRD-level invariants:** none
**Prototype mode:** none
**Dependencies:** MET — F12 has no `needs[]` (intra-PRD) and no `Needs:` (cross-PRD/backlog).
**Research needed:** NO (no new third-party APIs; FastAPI / SQLAlchemy / pytest patterns already in use)
**Designer needed:** NO (layer is `service`, not `ui`; surgical deletion in a single file)
**Implementer needed:** YES
**Safety auditor needed:** YES (file is `backend/app/routers/notes.py`, in the safety-gate hook's watched paths and named in invariant 1's exempt-helpers list; the helper being deleted is `_generate_embedding_background` itself, which is the explicit subject of one of those exemptions. Auditor confirms the deletion does not regress tenant isolation, raw-SQL discipline, or background-task safety.)
**Arch-advisor needed:** NO (trivial structural change, single file, single module)

**Intent:** build
**Complexity:** trivial

**What to build:**
Delete the embedding background-task plumbing from `backend/app/routers/notes.py`. Remove the `_generate_embedding_background` helper, both `background_tasks.add_task(...)` call sites in `create_note`/`update_note`, the no-longer-used `BackgroundTasks` / `openai_client` / `session_factory` parameters on those handlers, and the imports that exist solely to feed the deleted helper. CRUD endpoints (GET list, GET one, POST create, PUT update, DELETE) keep their behavior; the `/similar` and `/access` endpoints are out-of-scope for F12 and stay intact.

**New files:**
- (none)

**Modified files:**
- `backend/app/routers/notes.py` — delete `_generate_embedding_background` helper (lines 51-63); drop `BackgroundTasks` from the fastapi import (line 10); drop `get_async_session_factory` from the database import (line 18); drop the entire `from app.services.embeddings import generate_embedding, get_openai_client` line (line 27); drop `from typing import Any` (line 8) since after the helper and parameter deletions there is no remaining `Any` usage in the file; remove `background_tasks: BackgroundTasks`, `openai_client: Any = Depends(get_openai_client)`, and `session_factory: Any = Depends(get_async_session_factory)` parameters from `create_note` (lines 93, 96, 97); remove the `background_tasks.add_task(...)` block in `create_note` (lines 144-146); remove the same three parameters from `update_note` (lines 155, 158, 159); remove the conditional `background_tasks.add_task(...)` block in `update_note` (lines 208-211). Note `_note_to_response` still references `note.access_count` and `note.last_accessed_at`; those columns stay on the model until F19 drops them — do NOT touch that helper here.

**Existing patterns to follow:**
- `backend/app/routers/notes.py:get_note` (lines 298-325) — minimal CRUD handler shape (no embedding plumbing). The pruned `create_note` and `update_note` should match this lean signature pattern: `current_user`, `db`, plus their own request body, nothing else.
- `backend/app/routers/notes.py:delete_note` (lines 216-256) — already shows the target shape after extra deps are removed.

**Assertion traceability:**
- `/features/0/oracle/assertions/0` → After implementer's edits, `rg "_generate_embedding_background" backend/app/routers/notes.py` returns no lines. Test-writer should encode this as a static-text assertion (read the file and assert the substring is absent) rather than a runtime test.
- `/features/0/oracle/assertions/1` → Locate the `create_note` and `update_note` function bodies (e.g. by AST or by source-slicing between `def create_note` / `def update_note` and the next `@router.` decorator) and assert `background_tasks.add_task` does not appear inside either span. A whole-file grep is too coarse — the assertion is scoped to those two handlers.
- `/features/0/oracle/assertions/2` → Run the existing notes-router CRUD integration tests (`backend/tests/integration/notes/test_notes_router.py`) and require pass with no edits to that file.

**Edge cases:**
- `update_note` only enqueued the background task when `note_data.content is not None and formatted_content is not None`. Removing the entire conditional block is correct; `formatted_content` is still set inside the `if note_data.content is not None:` branch above for the field assignment, so do not also delete that assignment.
- The `openai_client` parameter currently masks the imported `get_openai_client` symbol; removing the parameter and the import together avoids leaving an orphan reference.
- `_note_to_response` reads `note.access_count` and `note.last_accessed_at`. These columns still exist on the model for now (F19 owns their removal); leave that helper untouched.
- The `from typing import Any` line is *only* used to type the soon-to-be-deleted parameters and helper. If implementer leaves it in, ruff's `F401` will flag unused-import on next lint. Drop it.

**Risks:**
- **Test-collection ordering risk (FLAGGED for orchestrator/test-writer):** `backend/tests/integration/notes/test_similarity.py` patches `app.routers.notes.generate_embedding` (lines 107, 128, 149). After F12 lands, that attribute no longer exists on the module, and pytest collection of `test_similarity.py` will raise `AttributeError` *before any test runs*, which can take down the whole `backend/tests/integration/notes/` package collection. F13 owns the deletion of `test_similarity.py`. Options for the implementer/test-writer:
  1. (Preferred) During F12, delete `backend/tests/integration/notes/test_similarity.py` as a transitive consequence of removing the patched symbol, since the file becomes uncollectable. This is a defensible scope expansion because oracle assertion 2 says "Existing notes-router CRUD integration tests pass unchanged" — and the only way that holds is if the broken sibling collection doesn't poison the package. F13's contract already requires that file's absence.
  2. (Alternative) Mark `test_similarity.py` with a module-level `pytest.skip("F12 removes patched symbol; F13 deletes this file", allow_module_level=True)` until F13 lands.
  3. (Worst) Land F12 with the file untouched and accept that pytest collection of that subpackage will fail until F13 lands; this contradicts oracle assertion 2 and so is rejected.

  Recommendation to test-writer: pursue option (1). Document the deletion under "Decisions" in the test-writer section and call out the scope-expansion rationale. If test-writer chooses option (2), this is acceptable but must be explicitly logged and F13's pre-check must verify the marker and the file are removed together.
- Removing the `BackgroundTasks` import from fastapi is safe — `rg "BackgroundTasks|background_tasks" backend/app/routers backend/app/main.py` confirms no other handler uses it.
- The file's `_note_to_response` keeps reading `access_count` / `last_accessed_at`; those still exist as model attributes (F19 hasn't run yet). No KeyError risk.

**Verify command:** `make test-backend-all` (UI tests are unaffected; full pipeline gate is `make test`)

**Path convention:** Backend Python lives under `backend/app/`; tests under `backend/tests/{unit,integration}/`. F12 touches only `backend/app/routers/notes.py` (and, per the test-writer recommendation, possibly `backend/tests/integration/notes/test_similarity.py`).

**Constraints for downstream:**
- MUST: keep CRUD endpoint behavior byte-identical from the client's perspective — same routes, methods, response shapes, status codes.
- MUST: drop the `from typing import Any` import after parameter deletions (no orphan unused imports; ruff F401 would block CI).
- MUST: leave `_note_to_response` and its references to `access_count` / `last_accessed_at` untouched. F19 removes those columns; F12 must not.
- MUST: leave the `/similar` (lines 259-295) and `/access` (lines 328-351) endpoints in place; F13 and F14 own their removal.
- MUST: leave `SimilarNoteResponse` in the schemas import block (lines 20-26). F13 cleans that import when `/similar` goes.
- MUST: address the `test_similarity.py` collection-time breakage per the test-writer recommendation in **Risks**.
- MUST NOT: modify `backend/app/services/embeddings.py`, `backend/app/services/backfill.py`, or any models/migrations — those are F15 / F19 scope.
- MUST NOT: drop pyproject.toml dependencies (`openai`, `pgvector`) — that is F20.
- MUST NOT: modify `docs/design-docs/core-beliefs.md` invariant 1 exempt-helpers list — F21 owns that doc sweep, even though `_generate_embedding_background` is named there.
- MUST NOT: introduce ai-slop:
  - No "premature abstraction" — do not refactor `create_note`/`update_note` beyond removing the deleted plumbing.
  - No "documentation bloat" — do not add docstring updates explaining what was removed.
  - No "gold-plating" — no feature flags, no shimmed `BackgroundTasks` parameter "for compatibility", no logger lines mourning the helper.
  - No "scope inflation" — F12 stops at `routers/notes.py`. The pyproject deps stay. The model columns stay. The other endpoints stay.
- MUST NOT: introduce new dependencies.

**Ready:** YES
**Next hop:** test-writer

### Resolved feature (verbatim from keel-feature-resolve.py)

```json
{
  "ok": true,
  "feature_id": "F12",
  "feature_index": 0,
  "feature_pointer_base": "/features/0",
  "prd_path": "/home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json",
  "canonical_prd_path": "/home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json",
  "title": "Strip embedding generation from routers/notes.py",
  "layer": "service",
  "oracle": {
    "type": "integration",
    "assertions": [
      "grep of `backend/app/routers/notes.py` for `_generate_embedding_background` returns zero matches.",
      "grep of `backend/app/routers/notes.py` for `background_tasks.add_task` returns zero matches inside `create_note` and `update_note`.",
      "Existing notes-router CRUD integration tests (create / read / update / delete) all pass unchanged."
    ],
    "tooling": "pytest backend/tests/integration/notes; ripgrep for static checks."
  },
  "contract": {
    "_generate_embedding_background": "deleted",
    "background_task_calls_in_create_note": "absent",
    "background_task_calls_in_update_note": "absent",
    "embedding_imports_in_routers_notes": "absent"
  },
  "needs": [],
  "prd_invariants_exercised": [],
  "backlog_fields": {
    "prd_slug": "remove-for-you",
    "prd_exempt_reason": null,
    "spec_ref": null,
    "design_refs": [],
    "needs_ids": [],
    "human_markers": [],
    "prototype_mode": null
  },
  "classification": "JSON_PRD_PATH"
}
```

### Constraints for downstream

## roundtable-precheck-review
<!-- Step 1.3 multi-model critique + canvass output -->

## pre-check (revised, attempt 2)

The roundtable (Claude Opus 4.7 + Codex CLI + Gemini 3.1 Pro) reviewed the prior brief and converged on five corrections. The brief below supersedes the original `## pre-check` section above. Where this section disagrees with the original, this section wins.

### Updated routing decisions

**Intent:** refactoring  *(was: build — schema's `build` connotes "new feature, greenfield"; F12 removes behavior while keeping the public CRUD contract byte-identical, so `refactoring` is the most defensible enum value)*
**Complexity:** standard  *(was: trivial — F12 spans two files (`backend/app/routers/notes.py` plus a class deletion in `backend/tests/integration/notes/test_similarity.py`), prunes two handler signatures, and threads a typing-import cleanup; that's beyond the agent contract's `trivial` definition of "single file, <10 lines, clear scope")*

Other routing flags from the original brief stand:
- **Designer needed:** NO
- **Researcher needed:** NO
- **Implementer needed:** YES
- **Arch-advisor needed:** NO
- **Safety-auditor needed:** YES — justified specifically under invariant 1's exempt-helpers transition. `_generate_embedding_background` is currently named in `docs/design-docs/core-beliefs.md` invariant 1's exempt-helpers list. Deleting it strictly narrows the exemption surface; the auditor's job here is to confirm the deletion does not displace the same violation pattern (cross-tenant raw-SQL access) into a new helper or call site, and to confirm no other site quietly relied on that exemption. (Not the generic "watched-paths heuristic" — the surface area is reducing, not changing.)

### Updated implementer guidance — surgical class-only deletion in `test_similarity.py`

F12 must also delete **only** the `TestEmbeddingGenerationOnMutations` class from `backend/tests/integration/notes/test_similarity.py` — lines 106-166 inclusive (class header at 106, last test body ends at 166). Do **not** delete the file. Do **not** touch:
- module-level imports (lines 1-7)
- the `DIMS` constant, `_pad` helper, `EMBEDDING_*` constants, and `create_note_with_embedding` factory (lines 8-31) — `TestSimilarNotesEndpoint` consumes them
- the `TestSimilarNotesEndpoint` class (lines 34-103) — it tests the still-extant `/similar` endpoint and the still-extant `Note.embedding` column; F13 owns its eventual deletion

Concretely, the post-F12 `test_similarity.py` ends after `TestSimilarNotesEndpoint`'s last test (line 103), with one trailing newline. F13's contract (`deleted_test_file: backend/tests/integration/notes/test_similarity.py`) remains satisfiable because the file and its 6 surviving tests still exist after F12.

This is a class-scoped surgical deletion, not whole-file deletion, and not a `pytest.skip` shim.

### Corrected Risks section (supersedes the original)

The original brief overstated the blast radius of leaving `TestEmbeddingGenerationOnMutations` in place. To set the record straight:

- `unittest.mock.patch` as a method decorator does **not** resolve its target string at class-load / collection time. Resolution happens inside `_patch.__enter__`, which runs only when the wrapped test method executes. So pytest **collection** of `test_similarity.py` would succeed even with the stale `@patch("app.routers.notes.generate_embedding")` decorators present.
- The 6 tests in `TestSimilarNotesEndpoint` (lines 34-103) do not patch anything; they exercise the still-present `/similar` route and `Note.embedding` column. They pass after F12 lands.
- Only the 3 tests in `TestEmbeddingGenerationOnMutations` (lines 107, 128, 149 — the three `@patch` sites) would fail, and only at **test execution time**, with `ModuleNotFoundError` / `AttributeError` from `_get_target` looking up `generate_embedding` on `app.routers.notes` (which F12 removes from the module's namespace).
- The CRUD tests in `backend/tests/integration/notes/test_notes_router.py` were never at risk from the mock issue. There is no package-level collection cascade.

Net blast radius without the surgical deletion: **3 stale tests fail at runtime**, not "the whole `backend/tests/integration/notes/` package collection takes down". Deleting the `TestEmbeddingGenerationOnMutations` class as part of F12 is therefore the smallest surgical fix that satisfies oracle assertion 2 without touching siblings F13 owns.

The original brief's Option 2 (`pytest.skip` shim) and Option 3 (land it broken) are both rejected by the roundtable: Option 2 leaves dead code; Option 3 leaves runtime failures that contradict oracle assertion 2.

Other risks from the original brief still apply:
- Removing the `BackgroundTasks` import is safe — no other handler in `backend/app/routers/` or `backend/app/main.py` uses it.
- `_note_to_response` keeps reading `access_count` / `last_accessed_at`; those columns still exist on the model until F19.

### Note on oracle assertion 2

`oracle.assertions[2]` ("Existing notes-router CRUD integration tests pass unchanged") is satisfied after the surgical class deletion:
- `backend/tests/integration/notes/test_notes_router.py` was never affected by the `@patch("app.routers.notes.generate_embedding")` decorators (those live exclusively in `test_similarity.py`'s `TestEmbeddingGenerationOnMutations` class), so its CRUD tests were never in danger of breakage from F12 — collection-time or otherwise.
- The surviving `TestSimilarNotesEndpoint` tests in `test_similarity.py` execute the `/similar` endpoint with no mocks of `routers.notes` symbols, so they remain green.
- Removing only the `TestEmbeddingGenerationOnMutations` class eliminates the only remaining failure surface (the 3 stale runtime patches) without disturbing F13's intended scope.

### Updated `Modified files` list (supersedes the original brief's single-file claim)

- `backend/app/routers/notes.py` — same edits as the original brief (helper removal, parameter pruning, import cleanup including `from typing import Any`).
- `backend/tests/integration/notes/test_similarity.py` — delete lines 106-166 (the `TestEmbeddingGenerationOnMutations` class). Leave lines 1-103 and the trailing newline intact.

### Updated `Constraints for downstream`

The constraint that previously read:
> MUST: address the `test_similarity.py` collection-time breakage per the test-writer recommendation in **Risks**.

is replaced by:
> MUST: delete only the `TestEmbeddingGenerationOnMutations` class (lines 106-166) from `backend/tests/integration/notes/test_similarity.py`. MUST NOT delete the file or any other class. MUST NOT introduce a `pytest.skip` shim. F13 retains ownership of the file's eventual full removal.

All other constraints from the original brief remain in force.

### Routing decisions (YAML for orchestrator frontmatter)

```yaml
intent: refactoring
complexity: standard
designer_needed: false
researcher_needed: false
safety_auditor_needed: true
arch_advisor_needed: false
implementer_needed: true
```

**Ready:** YES
**Next hop:** test-writer


## researcher
<!-- Research brief appended here (if applicable) -->

### Decisions (optional)

## arch-advisor-consultation
<!-- Architecture guidance appended here by Arch-advisor at Step 1.7 (if applicable) -->

### Constraints for downstream

## backend-designer / frontend-designer
<!-- Design brief appended here (if applicable) -->

### Decisions
### Constraints for downstream

## roundtable-design-review
<!-- Multi-model advisory review of designer output (Step 2.5, if roundtable enabled). -->

## test-writer

## Test Report: Strip embedding generation from routers/notes.py

**PRD:** docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F12
**Feature index:** 0
**Test files:** `backend/tests/unit/routers/test_notes_no_embedding_plumbing.py`
**Tests written:** 3
**Status:** RED (all 3 assertions fail, compiles clean — 3 failed in 0.08s)
**Failure output:**
- `test_generate_embedding_background_absent_from_file` — AssertionError: `_generate_embedding_background` still present in notes.py
- `test_background_tasks_add_task_absent_from_create_note` — AssertionError: `background_tasks.add_task` still present in create_note body
- `test_background_tasks_add_task_absent_from_update_note` — AssertionError: `background_tasks.add_task` still present in update_note body

**Assertion traceability:**
- `/features/0/oracle/assertions/0` → `test_generate_embedding_background_absent_from_file`
- `/features/0/oracle/assertions/1` → `test_background_tasks_add_task_absent_from_create_note`, `test_background_tasks_add_task_absent_from_update_note`
- `/features/0/oracle/assertions/2` → satisfied by existing `backend/tests/integration/notes/test_notes_router.py` (not authored here; no changes made to that file)

**Test commands:**
```bash
# New static-analysis tests (RED on unmodified main, GREEN after F12 lands):
cd backend && uv run pytest tests/unit/routers/test_notes_no_embedding_plumbing.py -v

# Oracle assertion 2 — existing CRUD integration tests (must pass unchanged):
cd backend && uv run pytest tests/integration/notes/test_notes_router.py -v
```

### Decisions (optional)

- **AST over text-slicing for function bodies.** `_function_body_source()` uses `ast.walk` to locate `create_note` and `update_note` by name, then slices the source by line number. This is resilient to whitespace and comment changes, and avoids brittle regex.
- **Whole-file text search for assertion 0.** `_generate_embedding_background` is asserted absent from the entire file source (not just function bodies); this catches both the `def` and any residual call sites.
- **Oracle assertion 2 not re-authored.** The existing `test_notes_router.py` already covers CRUD. No new tests were written for it. The file was not modified.
- **`test_similarity.py` not touched.** The test-writer's scope is strictly oracle assertions 0 and 1. The surgical deletion of `TestEmbeddingGenerationOnMutations` (lines 104-166) and the associated cleanup (`from unittest.mock import patch` at line 1, `EMBEDDING_C` constant at line 15) are owned by the implementer per the revised brief. No changes were made to `test_similarity.py` here.

**Next hop:** implementer

## implementer

## Implementation Report: Strip embedding generation from routers/notes.py

**Files created/modified:**
- `/home/dev/projects/parchmark/backend/app/routers/notes.py` — deleted `_generate_embedding_background` helper; dropped `BackgroundTasks` from fastapi import; dropped `get_async_session_factory` from database import; dropped `from app.services.embeddings import generate_embedding, get_openai_client`; dropped `from typing import Any`; pruned `background_tasks` / `openai_client` / `session_factory` parameters from `create_note` and `update_note`; removed both `background_tasks.add_task(...)` blocks; dropped the now-unused `formatted_content: str | None = None` predeclaration in `update_note` (the variable is now scoped to the `if note_data.content is not None:` branch where it is used).
- `/home/dev/projects/parchmark/backend/tests/integration/notes/test_similarity.py` — deleted `from unittest.mock import patch` import (orphan after class delete); deleted `EMBEDDING_C` constant (orphan after class delete); deleted entire `TestEmbeddingGenerationOnMutations` class plus its PEP 8 separator (lines 104-166 inclusive). The 6 `TestSimilarNotesEndpoint` tests + helpers / fixtures remain intact.
- `/home/dev/projects/parchmark/backend/tests/unit/routers/test_notes_transaction_errors.py` — transitive cleanup: dropped `BackgroundTasks` from fastapi import (orphan after call-site updates); updated 4 direct call-sites of `create_note` / `update_note` to use the new lean signature (removed `BackgroundTasks()`, `None`, `AsyncMock` positional args). Test contracts (commit/refresh failure → 500 + rollback) are unchanged. The 2 `delete_note` tests in this file were unaffected and not modified.

**Change scope:** initial

**Changed paths:**
- /home/dev/projects/parchmark/backend/app/routers/notes.py
- /home/dev/projects/parchmark/backend/tests/integration/notes/test_similarity.py
- /home/dev/projects/parchmark/backend/tests/unit/routers/test_notes_transaction_errors.py

**Test status:** PASS

**Commands run (condensed):**

- `uv run ruff check app/routers/notes.py tests/integration/notes/test_similarity.py tests/unit/routers/test_notes_no_embedding_plumbing.py tests/unit/routers/test_notes_transaction_errors.py` → All checks passed.
- `uv run ruff format --check app/routers/notes.py tests/integration/notes/test_similarity.py tests/unit/routers/test_notes_transaction_errors.py` → 3 files already formatted (idempotent).
- `uv run pytest tests/unit/routers/test_notes_no_embedding_plumbing.py -v` → 3 passed in 0.03s. All 3 RED → GREEN:
  - `test_generate_embedding_background_absent_from_file` PASSED
  - `test_background_tasks_add_task_absent_from_create_note` PASSED
  - `test_background_tasks_add_task_absent_from_update_note` PASSED
- `uv run pytest tests/unit/routers/ -v` → 11 passed (includes 4 transaction-error tests after signature realignment).
- `uv run pytest tests/unit/` → 359 passed, 0 failed; 69 errors are unrelated Docker-fixture errors (documented `TestGetCurrentUser` / `TestDependencyIntegration` / model fixtures that require Docker locally and pass in CI).
- `uv run pytest tests/integration/notes/test_notes_router.py tests/integration/notes/test_similarity.py --collect-only` → 52 tests collected cleanly. `test_similarity.py` shows only `TestSimilarNotesEndpoint` (6 tests); `TestEmbeddingGenerationOnMutations` is no longer collected. Integration test execution requires Docker (testcontainers); 46 errors at execute-time are all `docker.errors.DockerException: Connection aborted` — environmental, not a code failure. CI will run them.
- `SECRET_KEY=<32+ chars> python -c "from app.routers import notes; ..."` → module imports cleanly; `_generate_embedding_background` and `generate_embedding` confirmed absent from the module namespace.

**Blockers (if any):** none

### Decisions

- **Transitive cleanup of `tests/unit/routers/test_notes_transaction_errors.py` (not enumerated in the brief).** The pre-check / test-writer chain only enumerated `test_similarity.py` as a sibling test file affected by F12. After making the mandated signature changes I discovered 4 tests in `test_notes_transaction_errors.py` that call `create_note(...)` and `update_note(...)` directly with the old 7-positional-arg signature (`BackgroundTasks()`, `None`, `AsyncMock`) and so fail with `TypeError: takes from 2 to 4 positional arguments but 7 were given`. Per the same surgical-cleanup logic the brief applied to `test_similarity.py` (drop the orphan import, realign with the new contract), I trimmed the 4 call sites to `(note_data, mock_user, mock_db_session)` and `(note_id, note_data, mock_user, mock_db_session)` and dropped the now-orphan `BackgroundTasks` import. The tests' assertions (commit/refresh failure → 500 + rollback) are unchanged — only the call-site argument list was realigned with the new lean signature. Logging this here so spec-reviewer / safety-auditor can sanity-check the scope expansion is the smallest defensible fix.
- **Dropped `formatted_content: str | None = None` predeclaration in `update_note`.** The brief did not explicitly call this out, but the predeclaration only existed to support the post-commit `if ... and formatted_content is not None: background_tasks.add_task(...)` block. With that block gone, the predeclaration is dead and ruff F841 would have flagged the now-orphan variable scope. Removing it keeps the function lean and matches the "no orphan code" hygiene rule from the roundtable findings. `formatted_content` is now scoped strictly to the `if note_data.content is not None:` branch where it is used.
- **Did not touch `_note_to_response`, `/similar`, `/access`, `services/embeddings.py`, or any model / schema / migration code.** Per the explicit MUST-NOT constraints in the brief, those are F13 / F14 / F15 / F19 scope.

**Next hop:** code-reviewer



## code-reviewer
<!-- Code quality review appended here. -->

## spec-reviewer
<!-- Conformance report appended here. -->

## safety-auditor
<!-- Audit report appended here (if applicable). -->

## arch-advisor-verification
<!-- Independent structural review appended here by Arch-advisor at Step 7.5 (if applicable). -->

## landing-verifier
<!-- Landing report appended here -->

## roundtable-landing-review
<!-- Multi-model advisory review of implementation (Step 8.5, if roundtable enabled). -->

## doc-gardener
<!-- Doc drift report appended here at Step 9 sub-step 1. -->

## roundtable-precheck-review (attempt 2 findings)

Three-model critique on the revised brief returned **CONCERNS** (5 prior corrections all landed; new hygiene findings surfaced).

**Implementation hygiene items for test-writer + implementer to absorb:**

1. **HIGH (CI-blocking):** When deleting `TestEmbeddingGenerationOnMutations` from `backend/tests/integration/notes/test_similarity.py`, also delete `from unittest.mock import patch` at line 1 — `patch` is unused after the class is removed; ruff F401 blocks CI. Brief's "leave lines 1-103 intact" guidance is wrong on this point.
2. **MEDIUM:** Effective deletion range is **lines 104-166**, not 106-166. Lines 104-105 are PEP 8 two-blank-line class separators between `TestSimilarNotesEndpoint` and `TestEmbeddingGenerationOnMutations`. Deleting only 106-166 leaves trailing blank lines.
3. **LOW:** `EMBEDDING_C` constant at line 15 of `test_similarity.py` is only referenced by `test_update_note_regenerates_embedding_on_content_update` (in the deleted class). Becomes orphan dead code — delete it as part of the cleanup.
4. **LOW:** Original (attempt-1) brief at lines 60-185 retains stale claims (collection-time poison framing, single-file scope, Option-1-delete-file recommendation, "trivial structural change" arch-advisor rationale). Supersede notice in attempt-2 brief covers it; downstream agents reading top-to-bottom may anchor on stale guidance — visually quarantine if it becomes a recurring source of confusion.

Verdict per skill rule: proceed with attempt-2 routing (advisory, not blocking). Test-writer must absorb items 1-3 above when authoring the test changes.

## safety-auditor

## Safety Audit: Strip embedding generation from routers/notes.py

**Verdict:** PASS

**PRD:** docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F12
**Files scanned:**
- backend/app/routers/notes.py (post-F12 working tree)
- backend/app/services/backfill.py (invariant-1 exempt module — sanity-checked, untouched by F12)
- backend/app/services/embeddings.py (invariant 6/7 — untouched by F12)
- backend/app/models/models.py (invariant 7 — untouched by F12)
- backend/tests/integration/notes/test_similarity.py (class deletion — non-prod code)
- backend/tests/unit/routers/test_notes_transaction_errors.py (signature realignment — non-prod code)

### Invariant-by-invariant evidence

| # | Rule | Verdict | Evidence |
|-|-|-|-|
| 1 | Tenant isolation on every Note ORM op | PASS | `rg "select\(Note\)\|update\(Note\)\|delete\(Note\)\|db\.query\(Note\)" backend/app/routers/notes.py backend/app/services/` returns 7 lines: 6 in `routers/notes.py` (lines 66, 155, 208, 234, 286, 301) — every one carries `Note.user_id == current_user.id`; 1 in `services/backfill.py:43` which is in the invariant-1 exempt list. The deleted `_generate_embedding_background` (which previously did a *non*-tenant-filtered `select(Note).filter(Note.id == note_id)` under exemption) is gone — exemption surface strictly NARROWS. No new helper inherits its exemption. The exempt-list entry in core-beliefs.md is stale per F21's scope — that is doc-debt, not a code violation. |
| 2 | Auth on every non-public route | PASS | `create_note` (line 76), `update_note` (line 131), `get_notes` (line 50), `get_note` (line 268), `delete_note` (line 186), `get_similar_notes` (line 230), `track_note_access` (line 298) all declare `current_user: User = Depends(get_current_user)`. The signature pruning kept `current_user` intact. `/notes/health/check` (line 322) is on the public allowlist. |
| 3 | No raw SQL outside three whitelisted sites | PASS | `rg "text\(" backend/app/` returns exactly the three whitelisted sites (`models/models.py:64`, `database/init_db.py:19`, `services/health_service.py:28`) plus an unrelated `CryptContext` substring match in `auth/auth.py:26`. F12 added zero `text(...)` calls. |
| 4 | Typed-or-bodyless mutations | PASS | `create_note` (POST) takes `note_data: NoteCreate`; `update_note` (PUT) takes `note_data: NoteUpdate`; both are `pydantic.BaseModel` subclasses from `app.schemas.schemas`. The deleted `from typing import Any` confirms no `Any`-typed body params. `track_note_access` (POST) is bodyless — allowed by 4(b). |
| 5 | No secrets in logs | PASS | The 4 `logger.error(...)` calls in `routers/notes.py` (lines 121, 177, 220, 315) interpolate only the `note_id` and the SQLAlchemyError exception `e`; none reference passwords, tokens, secrets, or auth/credentials schemas. F12 introduced no new log statements. |
| 6 | Embedding failure must never break note CRUD | PASS (vacuously) | After F12, `routers/notes.py` contains zero embedding work in `create_note` and `update_note` — neither `await generate_embedding(...)` nor `background_tasks.add_task(...)`. The invariant's second clause ("invoke embedding work *exclusively through* `background_tasks.add_task(...)`") is vacuously satisfied because there is no embedding work to invoke. The first clause (`generate_embedding` top-level try/except returning `None`) is unchanged in `services/embeddings.py` — F12 did not touch that file. F21 will retire this invariant. |
| 7 | Embedding dimension parity | PASS | `services/embeddings.py:13` → `EMBEDDING_DIMENSIONS = 1536`; `models/models.py:66` → `Vector(1536)`. F12 touched neither. |
| 8 | Passwords never stored raw | N/A | F12 touches no auth/settings code; no `.password_hash` assignments added/changed. |
| 9 | OIDC identity binding by `sub` | N/A | F12 touches no auth/dependencies code. |

### Special focus — invariant 1 transition

The deleted helper `_generate_embedding_background` was named in the invariant's exempt-helpers list precisely because it intentionally fetched a Note by `id` only (no `user_id` filter), trusting the caller to have already authorized the user. Removing that helper:

1. Does not displace the unfiltered-fetch pattern into another file. Confirmed via `rg "select\(Note\)\.filter\(Note\.id" backend/app/` → 5 hits, all in `routers/notes.py` (lines 155, 208, 234, 286, 301) — every one immediately follows with `Note.user_id == current_user.id` in the same `.filter(...)` call.
2. Does not leave any caller of the helper stranded — `rg "_generate_embedding_background" backend/` returns zero matches.
3. Strictly narrows the exemption surface. The exempt-list entry in `docs/design-docs/core-beliefs.md` is now stale (refers to a deleted symbol) but is intentionally left for F21 to sweep — explicit MUST-NOT in the F12 brief.

### Notes on test-file changes

- `backend/tests/integration/notes/test_similarity.py` — class-scoped deletion of `TestEmbeddingGenerationOnMutations` plus orphan `from unittest.mock import patch` import and `EMBEDDING_C` constant. Test code; not subject to invariants 1-9 directly. The surviving `TestSimilarNotesEndpoint` exercises the still-present `/similar` endpoint (out-of-scope for F12).
- `backend/tests/unit/routers/test_notes_transaction_errors.py` — call-site argument-list realignment after the production signatures pruned. No invariant impact.

**Next hop:** landing-verifier
