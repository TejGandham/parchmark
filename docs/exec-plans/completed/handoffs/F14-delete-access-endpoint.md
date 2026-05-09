# F14 Delete POST /api/notes/{id}/access endpoint

---
status: LANDED
pipeline: backend
prd_ref: docs/exec-plans/prds/remove-for-you.json#F14
spec_ref:

# Pre-check routing (set by pre-check, read by orchestrator)
intent: mid-sized
complexity: standard
designer_needed: NO
researcher_needed: NO
safety_auditor_needed: NO
arch_advisor_needed: NO
implementer_needed: YES

# Gate verdicts (set by orchestrator after each gate agent)
spec_review_verdict: CONFORMANT
spec_review_attempt: 1
safety_verdict:
safety_attempt: 0
code_review_verdict: APPROVED
code_review_attempt: 1
arch_advisor_verdict:

# Arch-advisor re-run counters (separate from initial gate passes)
arch_retry_spec_review_attempt: 0
arch_retry_safety_attempt: 0

# Pipeline configuration
remote_name: origin
roundtable_enabled: true
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/81

# Roundtable design review (Step 2.5)
roundtable_design_attempt: 0
roundtable_design_verdict:
roundtable_skipped:

# Roundtable landing review (Step 8.5)
roundtable_landing_attempt: 2
roundtable_landing_verdict: APPROVED

# Roundtable-triggered gate re-run counters
roundtable_retry_code_review_attempt: 0
roundtable_retry_spec_review_attempt: 0
roundtable_retry_safety_attempt: 0

# Roundtable pre-check review (Step 1.3)
roundtable_precheck_attempt: 1
roundtable_precheck_verdict: APPROVED

# Doc-gardener (Step 9 sub-step 1)
doc_garden_verdict: DRIFT_FOUND
doc_garden_drift_count: 7
---

## pre-check

## Execution Brief: Delete POST /api/notes/{id}/access endpoint

**PRD:** /home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F14
**Feature index:** 2
**Feature pointer base:** /features/2
**Layer:** service
**PRD-level invariants:** none
**Prototype mode:** none
**Dependencies:** MET — `needs: []` (intra-PRD) and backlog `Needs:` empty (cross-PRD). F12 and F13 (commit b6e40da) are both checked off `[x]` in the backlog as informational context, but neither is a formal F14 dependency.
**Research needed:** NO — pure deletion of an existing FastAPI route + companion test file; no new APIs, libraries, or patterns.
**Designer needed:** NO — `layer: service`, not `ui`.
**Implementer needed:** YES — code-deletion is non-trivial: route removal + verifying no in-process callers break + symmetric handling with the F13 precedent.
**Safety auditor needed:** NO — pure deletion of a route handler removes attack surface; cannot introduce new tenant-leak vectors. The nine domain invariants gate adds/mutations, not removes. F12 and F13 both processed the identical surgical-deletion idiom on the same `routers/notes.py` and produced no actionable safety findings — empirical precedent. Note: this handler does write (`access_count`, `last_accessed_at`), so its deletion narrows write surface; still no invariant gain to verify since invariants 6/7 are slated for retirement in F21 and current invariant 4's example list still cites this very endpoint (per PRD design_facts).
**Arch-advisor needed:** NO — bounded scope, no structural pattern change.

**Intent:** mid-sized
**Complexity:** trivial

**What to build:**
Delete the `POST /api/notes/{note_id}/access` route handler from `backend/app/routers/notes.py` (function `track_note_access`, lines 255–278) and delete `backend/tests/integration/notes/test_access_tracking.py` in its entirety. After this feature, `POST /api/notes/{id}/access` must produce a FastAPI default 404 (no matching route). All surviving notes-router CRUD integration tests must continue to pass unchanged.

**New files:**
- (none — prefer extending the existing F13-created `backend/tests/integration/notes/test_endpoint_removal.py` with new test classes for F14 coverage)

**Modified files:**
- `backend/app/routers/notes.py` — remove the `track_note_access` handler (the `@router.post("/{note_id}/access", ...)` block at lines 255–278). Leave every other route, helper, and import untouched. Note: the `func` import on line 14 (`from sqlalchemy.sql import func`) is currently used only inside `track_note_access` (line 268). After deletion, `ruff check` will flag it as unused — remove it in the same diff. Do NOT pre-emptively guess; let lint be the arbiter.
- `backend/tests/integration/notes/test_endpoint_removal.py` — append three new classes mirroring F13's structure: `TestAccessEndpointGone` (HTTP 404 + trailing-slash 404), `TestRouterSourceContainsNoAccessRouteString` (grep), `TestAccessTrackingTestFileDeleted` (filesystem absence).

**Deleted files:**
- `backend/tests/integration/notes/test_access_tracking.py` — entire file (10 tests covering the removed endpoint).

**Existing patterns to follow:**
- F13 commit `b6e40da` (`feat(F13): Delete GET /api/notes/{id}/similar endpoint`, just-landed) — same router, same surgical-deletion idiom; mirror its style precisely.
- `backend/tests/integration/notes/test_endpoint_removal.py` (created by F13) — the canonical endpoint-removal test pattern. Class structure: `TestSimilarEndpointGone` (HTTP), `TestRouterSourceContainsNoSimilarPath` (grep), `TestSimilarityTestFileDeleted` (filesystem). Mirror it.
- `backend/app/routers/notes.py:get_note` (~line 225) — surviving GET-by-id pattern; keep its position relative to other routes intact when removing the sibling.

**Assertion traceability:**
- `/features/2/oracle/assertions/0` → integration test in `test_endpoint_removal.py::TestAccessEndpointGone` — `client.post(f"/api/notes/{id}/access", headers=auth_headers)` returns 404. Use a real `sample_note` fixture for path symmetry with surviving CRUD tests, even though absence-of-route 404s are independent of note existence. Add a sibling test asserting the trailing-slash variant `POST /api/notes/{id}/access/` also returns 404.
- `/features/2/oracle/assertions/1` → static test `TestRouterSourceContainsNoAccessRouteString` reading `app/routers/notes.py` and asserting zero matches for the literal `/access` (route-segment pattern). Beware: do NOT match on the bare word `access` — `_note_to_response` references `note.access_count` (line 42) which legitimately remains until F19. Match on `"/access"` (with leading slash) or on the decorator literal `@router.post("/{note_id}/access"`.
- `/features/2/oracle/assertions/2` → filesystem test `TestAccessTrackingTestFileDeleted::test_test_access_tracking_file_does_not_exist` asserting `Path("backend/tests/integration/notes/test_access_tracking.py").exists() is False`.
- `/features/2/oracle/assertions/3` → run existing notes CRUD integration suite (`backend/tests/integration/notes/test_*.py` minus the deleted file); all pass. No new test code; the existing `test_notes_router.py` is the vehicle.

**Edge cases:**
- 404 source: with the route deleted, FastAPI returns its default `{"detail": "Not Found"}` 404 — distinguish from the handler's old `"Note not found"` 404 (line 265). Test should assert status code only (mirror F13's status-only approach), NOT body shape.
- Trailing slash: confirm `POST /api/notes/{id}/access/` also 404s. FastAPI's `redirect_slashes=True` default would otherwise 307 to a still-deleted path. Mirror F13's explicit trailing-slash assertion.
- `_note_to_response` (lines 33–45) still references `note.access_count` and `note.last_accessed_at`. These columns remain on the `Note` model until F19 drops them. DO NOT touch `_note_to_response` in F14 — that's F19's column-drop scope.
- Frontend `trackNoteAccess` / `ACCESS` API config / `noteScoring` blending remain in scope of sibling features F16/F17/F18 — out of scope for F14.
- Surviving `routers/notes.py` decorators after F14 will be: `GET /`, `POST /`, `PUT /{note_id}`, `DELETE /{note_id}`, `GET /{note_id}`, `GET /health/check`. None match `/{note_id}/access` — no shadow risk. Verify before relying on FastAPI's default 404.
- The grep pattern in assertion-1 must be path-aware. A naive `grep access` would match `access_count`/`last_accessed_at` in `_note_to_response` and false-positive. Use `grep '/access'` or `grep '"/{note_id}/access"'` to target the route literal.

**Risks:**
- Accidentally removing `track_note_access` AND brushing the `_note_to_response` helper or its `accessCount`/`lastAccessedAt` fields — those serve surviving routes (`get_note`, `get_notes`, `create_note`, `update_note`) and must remain until F19.
- Removing the wrong route (e.g., `/{note_id}` GET instead of `/{note_id}/access` POST). Fix: target by the literal decorator string `@router.post("/{note_id}/access"` to disambiguate.
- Breaking conftest fixtures referenced by the deleted test file (verify no shared `conftest.py` imports from `test_access_tracking.py`).
- `func` import handling: leaving it after deletion fails `ruff check`; removing it pre-emptively risks churn if the same diff brings it back. Defer to lint output as the source of truth — the standard make pipeline catches it.
- Collateral damage to surviving handler ordering — keep diff to pure subtraction, no reflow of `delete_note` / `get_note` / health-check siblings.
- Naive `/access` grep matching `access_count` substring in `_note_to_response` — write the assertion against `"/access"` (with quote+slash) or the full decorator literal to avoid false positives.

**Verify command:** `make test-backend-all` (lint + format + types + pytest from `/home/dev/projects/parchmark`). Spot-check: `cd /home/dev/projects/parchmark/backend && SECRET_KEY="dev-not-real-but-32-or-more-chars-here" uv run pytest tests/integration/notes/ -v`.

**Path convention:** Backend Python at `backend/app/` (FastAPI app root). Tests at `backend/tests/`. Integration tests at `backend/tests/integration/notes/`. Routers at `backend/app/routers/`.

**Constraints for downstream:**
- MUST: delete only the `track_note_access` handler block in `routers/notes.py` (decorator + body, lines 255–278). Pure subtraction.
- MUST: delete `backend/tests/integration/notes/test_access_tracking.py` in full (no partial keep).
- MUST: leave `_note_to_response` (lines 33–45) and its `accessCount`/`lastAccessedAt` field mappings UNTOUCHED — F19 owns the column drop, not F14.
- MUST: leave `backend/app/models/models.py` UNTOUCHED — `Note.access_count` and `Note.last_accessed_at` columns are F19's scope.
- MUST: leave `backend/app/schemas/schemas.py` UNTOUCHED.
- MUST: leave the frontend (`ui/src/config/api.ts ACCESS`, `services/api.ts trackNoteAccess`, `noteScoring` blending, `CommandPalette`/`NotesExplorer` access-tracking calls) UNTOUCHED — those belong to sibling features F16/F17/F18.
- MUST: verify post-deletion that no shadow route in `routers/notes.py` matches `POST /notes/{id}/access` (e.g., `/{note_id}/{action}`-style catch-all). Inspect every `@router.{get,post,put,delete}` decorator in the file post-deletion and confirm none would match the path.
- MUST: test oracle MUST include an explicit `POST /api/notes/{note_id}/access` returning 404 integration assertion under authenticated request — mirror F13's load-bearing assertion. Use the `sample_note` fixture for path symmetry with surviving CRUD tests.
- MUST: include an explicit oracle assertion that `POST /api/notes/{note_id}/access/` (trailing slash) also returns 404 — mirror F13's amended constraint from roundtable Attempt 2.
- MUST: 404 oracle assertion asserts status code 404 only; do NOT assert body shape — body differs between "no route matches" (`{"detail": "Not Found"}`) and the handler's old `"Note not found"`. Status-only is the contract.
- MUST: grep assertion-1 targets the literal `"/access"` (quote+slash) or the full decorator literal `@router.post("/{note_id}/access"`, NOT the bare word `access` — surviving `note.access_count` references in `_note_to_response` would false-positive.
- MUST: handle the `func` import (line 14, `from sqlalchemy.sql import func`) by deferring to ruff. Run `make test-backend-all`; if `ruff check` flags it as unused, remove it in the same diff. Do NOT pre-emptively remove without lint signal, and do NOT leave it if lint flags it.
- MUST: surviving notes-CRUD integration tests pass unchanged after deletion (no test churn in `test_notes_router.py` or other surviving files).
- MUST: prefer extending the existing `backend/tests/integration/notes/test_endpoint_removal.py` (created by F13) with new test classes (`TestAccessEndpointGone`, `TestRouterSourceContainsNoAccessRouteString`, `TestAccessTrackingTestFileDeleted`) over creating a parallel file. One "endpoint-removal" file is the cleaner surface and aligns with the F13 precedent.
- MUST: PR body MUST note that the frontend strip (`trackNoteAccess` calls in `CommandPalette.tsx` and `NotesExplorer.tsx`, the `ACCESS` constant in `config/api.ts`, the `trackNoteAccess` symbol in `services/api.ts`) is sequenced in sibling features F16/F17/F18, and that the frontend's `trackNoteAccess()` is fire-and-forget (no UI rendering depends on its response), so a transient F14-merged / F18-unmerged window produces only browser-devtools 404 noise — no user-visible regression.
- MUST NOT: touch `backend/app/services/embeddings.py`, `backend/app/services/backfill.py`, or any service module — those belong to F15.
- MUST NOT: touch `backend/app/main.py` (OpenAI lifespan wiring is F15's scope).
- MUST NOT: touch `backend/app/models/models.py` — column drops are F19's scope.
- MUST NOT: rename, reorder, or restyle surviving handlers in `routers/notes.py` — diff should be a pure subtraction.
- MUST NOT: introduce new dependencies, helpers, or abstractions — this is a deletion, not a refactor.
- MUST NOT: add docstrings, comments, deprecation notes, or migration comments to the surrounding code — pure deletion.
- MUST NOT: gold-plate by adding a 410-Gone or deprecation shim. The contract is "404 from absence of route," not a custom response.
- MUST NOT: edit `docs/design-docs/core-beliefs.md` invariant 4's example list (which still cites `/notes/{id}/access`) — that doc-sweep is F21's scope.

### Constraints for downstream

(Mirror of the in-brief constraint block; the orchestrator may treat this section as canonical.)

- Pure subtraction diff in `backend/app/routers/notes.py` (handler block at lines 255–278 + the `func` import on line 14 if ruff flags it) + full delete of `backend/tests/integration/notes/test_access_tracking.py` + append-only additions to `backend/tests/integration/notes/test_endpoint_removal.py`.
- `_note_to_response`, the `Note` model's `access_count`/`last_accessed_at` columns, and the `accessCount`/`lastAccessedAt` schema fields all remain — F19 drops them.
- Frontend `trackNoteAccess` plumbing remains — F16/F17/F18 strip it.
- `docs/design-docs/core-beliefs.md` invariant 4 still cites this endpoint — F21 sweeps it.
- 404 from FastAPI's default route-not-found, not from a custom handler; tests assert status-only.
- Trailing-slash 404 must be explicitly asserted (parity with F13).
- Safety-auditor not routed (precedent: F13 declined and produced no findings on the same idiom; deletion-only changes cannot widen attack surface).

### Resolved feature (verbatim from keel-feature-resolve.py)

```json
{
  "ok": true,
  "feature_id": "F14",
  "feature_index": 2,
  "feature_pointer_base": "/features/2",
  "prd_path": "/home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json",
  "canonical_prd_path": "/home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json",
  "title": "Delete POST /api/notes/{id}/access endpoint",
  "layer": "service",
  "oracle": {
    "type": "integration",
    "assertions": [
      "POST on `/api/notes/{note_id}/access` for any authenticated user returns HTTP 404.",
      "grep of `backend/app/routers/notes.py` for `/access` returns zero matches.",
      "File `backend/tests/integration/notes/test_access_tracking.py` does not exist.",
      "Existing notes-router CRUD integration tests all pass unchanged."
    ],
    "tooling": "pytest with httpx test client; filesystem check."
  },
  "contract": {
    "route": "/api/notes/{note_id}/access",
    "method": "POST",
    "endpoint_status": "removed",
    "response_for_removed_route": 404,
    "deleted_test_file": "backend/tests/integration/notes/test_access_tracking.py"
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

**Ready:** YES
**Next hop:** test-writer

## roundtable-precheck-review

**Attempt:** 1
**Verdict:** APPROVED (with one ceremonial flip)

**Panel:** Claude Opus 4.7, Codex (gpt-5-codex), Gemini 3.1 Pro Preview — all under `codereviewer` role for the critique pass, then `default` synthesizer role for canvass.

**Per-flag consensus (canvass, unanimous):**

| Flag | Verdict | Reason |
|-|-|-|
| intent: mid-sized | KEEP | Scoped backend endpoint retirement matches the `mid-sized` intent. |
| complexity: trivial → standard | FLIP-TO-STANDARD | KEEL pre-check rubric (`.claude/agents/pre-check.md:42`) reserves `trivial` for single-file < 10-line changes. F14 spans 3 files: edit `routers/notes.py`, extend `tests/integration/notes/test_endpoint_removal.py`, delete `tests/integration/notes/test_access_tracking.py`. Strict definition forces `standard`. **Material:** NO — no downstream agent's run/skip decision is gated on the trivial/standard boundary for this feature. |
| designer_needed: NO | KEEP | Pure backend route subtraction; zero UI surface. |
| researcher_needed: NO | KEEP | No new patterns or unresolved discovery; mirrors F13's deletion playbook. |
| safety_auditor_needed: NO | KEEP | No code-side invariant breach. Doc-staleness (invariant-4 example list still cites this endpoint) is doc-gardener scope, not safety-auditor scope. |
| arch_advisor_needed: NO | KEEP | Architectural framing for the 9-feature retirement was a PRD/refine-time decision; per-feature arch-advisor adds no signal. |
| implementer_needed: YES | KEEP | Required to perform the deletion and test updates. |

**Re-dispatch pre-check:** NO — the sole flip (`complexity: trivial → standard`) is ceremonial and does not change which downstream agents run. YAML directly updated to reflect the consensus.

**Framework-level finding (advisory, out-of-scope for F14):**

All three panelists independently flagged a structural blind spot in the KEEL pre-check phase: there is no systematic pass for "inbound documentation references to the symbol being deleted." `core-beliefs.md` invariant-4 example list cites this exact endpoint; `doc-gardener` will catch it post-landing in Step 9 sub-step 1, applying the fix to the working tree before commit (so the PR diff is still stable). Resolution path for the framework gap is to edit `.claude/skills/keel-pipeline/SKILL.md` or `.claude/agents/pre-check.md` in a future feature — NOT folded into F14 mid-flight. Recording the observation here for downstream awareness.

**Implementer pickup hint (panel-derived):** When extending `_note_to_response`, `access_count` and `last_accessed_at` reads remain in the surviving helper until F19 drops the columns. Do not eagerly remove those reads in F14.

## researcher
<!-- Research brief appended here (if applicable) -->

### Decisions (optional)

## arch-advisor-consultation

### Constraints for downstream

## backend-designer / frontend-designer

### Decisions
### Constraints for downstream

## roundtable-design-review

## test-writer

## Test Report: Delete POST /api/notes/{id}/access endpoint

**PRD:** /home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F14
**Feature index:** 2
**Test files:** `backend/tests/integration/notes/test_endpoint_removal.py` (appended)
**Tests written:** 4 (3 new classes; assertion-3 uses the existing `test_notes_router.py` as vehicle — no new test code)
**Status:** RED (static assertions fail with clean output; HTTP assertions ERROR due to Docker/testcontainers unavailability in this environment — same infrastructure error as the existing F13 HTTP tests, which also require Docker to run)

**Failure output (static tests, no Docker required):**

```
FAILED TestRouterSourceContainsNoAccessRouteString::test_routers_notes_has_no_access_route_string
  AssertionError: Expected zero occurrences of the '/access' route literal in .../routers/notes.py,
  but found 1 match(es):
      line 255: @router.post("/{note_id}/access", response_model=NoteResponse)

FAILED TestAccessTrackingTestFileDeleted::test_test_access_tracking_file_does_not_exist
  AssertionError: Expected .../test_access_tracking.py to be deleted as part of F14, but it still exists.
```

HTTP tests (`TestAccessEndpointGone`) ERROR at fixture setup (no Docker) — identical to F13's HTTP tests in the same file; will FAIL → PASS once the implementer deletes the route and Docker is available in CI.

**Assertion traceability:**
- `/features/2/oracle/assertions/0` → `TestAccessEndpointGone::test_post_access_returns_404_for_authenticated_request` and `TestAccessEndpointGone::test_post_access_trailing_slash_returns_404`
- `/features/2/oracle/assertions/1` → `TestRouterSourceContainsNoAccessRouteString::test_routers_notes_has_no_access_route_string`
- `/features/2/oracle/assertions/2` → `TestAccessTrackingTestFileDeleted::test_test_access_tracking_file_does_not_exist`
- `/features/2/oracle/assertions/3` → existing `backend/tests/integration/notes/test_notes_router.py` (no new code; passing unchanged is the oracle)

### Decisions (optional)

- Grep pattern uses `'"/{note_id}/access"'` (the full decorator literal) rather than `'"/access"'` alone to avoid any risk of partial matches; the broader OR condition covers both possible literal forms.
- HTTP tests use `sample_note` fixture for path symmetry with surviving CRUD tests (per execution brief MUST constraint), even though the 404 is route-absence-based and not note-dependent.
- Trailing-slash tests mirror F13's approach: TestClient follows redirects by default, so the final resolved status (after any 307) is asserted as 404.
- No new test file created — appended to the existing F13-created `test_endpoint_removal.py` per the MUST constraint in the execution brief.

**Next hop:** implementer

## implementer

## Implementation Report: Delete POST /api/notes/{id}/access endpoint

**Files created/modified:**
- `/home/dev/projects/parchmark/backend/app/routers/notes.py` — removed `track_note_access` handler block (former lines 255–278) and the now-unused `from sqlalchemy.sql import func` import (former line 14). Pure subtraction; no other helpers, routes, imports, or formatting changed.
- `/home/dev/projects/parchmark/backend/tests/integration/notes/test_access_tracking.py` — DELETED in entirety (10 tests covering the removed endpoint). Verified no other test or conftest imports from this module before deletion.

**Change scope:** initial
**Changed paths:**
- `/home/dev/projects/parchmark/backend/app/routers/notes.py`
- `/home/dev/projects/parchmark/backend/tests/integration/notes/test_access_tracking.py` (deleted)

**Test status:** PASS (static + filesystem tier locally; HTTP tier deferred to CI per Docker-availability constraint stated in test report)

**Commands run:**

```
$ cd backend && uv run ruff check app/routers/notes.py
All checks passed!

$ cd backend && uv run ruff format app/routers/notes.py
1 file left unchanged

$ cd backend && uv run pytest tests/integration/notes/test_endpoint_removal.py::TestRouterSourceContainsNoAccessRouteString tests/integration/notes/test_endpoint_removal.py::TestAccessTrackingTestFileDeleted -v
collected 2 items
tests/integration/notes/test_endpoint_removal.py::TestRouterSourceContainsNoAccessRouteString::test_routers_notes_has_no_access_route_string PASSED [ 50%]
tests/integration/notes/test_endpoint_removal.py::TestAccessTrackingTestFileDeleted::test_test_access_tracking_file_does_not_exist PASSED [100%]
============================== 2 passed in 0.03s ===============================

$ cd backend && uv run pytest tests/integration/notes/test_endpoint_removal.py --collect-only
collected 8 items   # 4 F13 classes + 4 F14 classes — all collect cleanly

$ cd backend && uv run pytest tests/integration/notes/test_endpoint_removal.py::TestRouterSourceContainsNoSimilarPath tests/integration/notes/test_endpoint_removal.py::TestSimilarityTestFileDeleted -v   # F13 regression check
============================== 2 passed in 0.03s ===============================
```

**Blockers (if any):** none

### Decisions

- Removed `from sqlalchemy.sql import func` in the same diff as the handler — ruff would have flagged it as unused (per the execution brief's "defer to lint" guidance, confirmed by the no-import-in-handler-body check). No other imports were affected.
- Left `_note_to_response` and its `note.access_count` / `note.last_accessed_at` reads UNTOUCHED — those columns and helper reads belong to F19 per the precheck and roundtable implementer pickup hint.
- Confirmed via grep that no other test, fixture, or conftest imports anything from `test_access_tracking.py` before deleting it (only references are inside `test_endpoint_removal.py` as documentation strings, not imports).
- Pure subtraction: surviving handler ordering (`get_notes`, `create_note`, `update_note`, `delete_note`, `get_note`, `notes_health_check`) preserved verbatim; no reflow or reordering.
- HTTP-tier tests (`TestAccessEndpointGone`) were not run locally (no Docker available in this environment, same as F13's HTTP tests in the same file); they will be exercised by CI which has the testcontainers PostgreSQL stack.

**Next hop:** code-reviewer

### Decisions

## code-reviewer

## spec-reviewer

## safety-auditor

## arch-advisor-verification

## landing-verifier

## doc-gardener

**Mode:** pipeline
**Verdict:** DRIFT_FOUND
**Drift count:** 7

**F14 blast-radius drift (4 fixes applied to working tree before commit):**

| Path | Before | After |
|-|-|-|
| `AGENTS.md:155` | "Notable non-obvious endpoints: `POST /api/notes/{id}/access` (...), `GET /api/notes/{id}/similar` (...), `GET /api/health` (...)" | "Notable non-obvious endpoints: `GET /api/health` (DB + version info)." |
| `README.md:429-430` | API table rows for `POST /access` + `GET /similar` | rows removed |
| `backend/README.md:143-144` | API table rows for `POST /access` + `GET /similar` | rows removed |
| `ui/README.md:149-150` | API table rows for `/access` + `/similar` | rows removed |

Note: the `GET /api/notes/{id}/similar` rows were missed by F13's doc-gardener pass (F13 landed with these rows still present). F14's sweep removes them along with F14's own `/access` rows since both are part of the same `remove-for-you` retirement and appear on the same lines of each table — splitting them would leave the docs in a transient broken state.

**F14 feature-ID coverage (1 fix applied):**

- `docs/exec-plans/active/feature-backlog.md:71` — F14 entry flipped from `[ ]` to `[x]` per Step 9 norms.

**§P5 timeline-artifact drift (3 items deferred to tech-debt-tracker.md):**

Three drift items were flagged in `docs/deployment_upgrade/archive/`:
- `DEPLOYMENT.md:2429` — `## Changelog` section with version table
- `PHASE4_GITHUB_SECRETS.md:112` — "as of January 2025" annotation
- `DEPLOYMENT_VALIDATED.md:245` — "as of January 2025" annotation

These predate the §P5 invariant and are unrelated to F14's contract. Bundling them into F14's PR would muddy the diff. Recorded in `docs/exec-plans/tech-debt-tracker.md` for a future deployment-docs cleanup sweep.

**Known intentional deferral (not flagged as drift, recorded for transparency):**

- `docs/design-docs/core-beliefs.md` invariant 4 example list still cites the deleted `/access` endpoint. Cleanup is explicitly scoped to F21 in the `remove-for-you` PRD.

## roundtable-landing-review

**Attempt:** 2 (initial cross-check + synthesis canvass)
**Verdict:** APPROVED (LAND-WITH-CAVEAT)

**Panel:** Claude Opus 4.7 (generalist), Codex (codereviewer), Gemini 3.1 Pro Preview (planner) — mixed-role cross-check; then synthesis canvass with all three panelists in default role.

**Initial cross-check verdicts:** 2 LAND, 1 HOLD.

| Role | Vote | Summary |
|-|-|-|
| Claude (generalist) | LAND | Sequencing safe; pipeline gates clean; test scaffolding tolerable through F20. |
| Codex (codereviewer) | LAND | `func` import has no remaining references; FastAPI default 404 correct; frontend already fail-soft. |
| Gemini (planner) | HOLD | Sequencing hazard (frontend still calls /access); grep + filesystem-absence tests are "anti-patterns." |

**Resolution via synthesis canvass:** All three panelists converged on LAND.

- Gemini's HOLD was load-bearing on the assumption that `trackNoteAccess` does NOT swallow HTTP 404s. Both Claude and Codex independently verified the assumption is false: `ui/src/services/api.ts:151` is fire-and-forget; `NotesExplorer.tsx:88` chains `.catch(() => {})`; `CommandPalette.tsx:124` calls the same fail-soft helper. Once the factual misread was corrected, Gemini explicitly revised its vote to LAND.
- The retirement plan is intentionally backend-first (PRD `remove-for-you` orders F12-F15 before F16-F18, and F19 explicitly `Needs: F12, F13, F14, F15`). The sequencing was an architectural decision at PRD-refine time, not an oversight.
- On test-pattern asymmetry: Gemini's stylistic critique of grep + filesystem-absence tests is directionally fair, but reverting in F14 alone would create needless asymmetry with F13 (`b6e40da`) which merged through KEEL with the identical pattern under prior roundtable review. Right place to retire the pattern is a follow-up tech-debt sweep across F12-F15, not unilateral divergence inside F14.

**PR-description caveat (recommended by all three panelists):**
> Per the `remove-for-you` retirement plan, this is an intentionally backend-first deletion: frontend `trackNoteAccess` call sites (already fire-and-forget) remain until F16–F18 and will emit benign 404s in the interim.

**Tech-debt observation (non-blocking, recorded in tech-debt-tracker.md if a sweep is desired):**
- `test_endpoint_removal.py` is becoming an accumulator file for retirement features. After F15/F19/F20 it will hold 4+ feature class-pairs in one module. Consider parameterized fixtures or a dedicated subdirectory if the pattern continues past F20.
