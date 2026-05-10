# F18 — Delete noteScoring util, API wrappers, endpoint constants, and SimilarNote types

---
status: IN-PROGRESS
pipeline: frontend
prd_ref: docs/exec-plans/prds/remove-for-you.json#F18

# Pre-check routing (set by pre-check, read by orchestrator)
intent: refactoring
complexity: standard
designer_needed: false
researcher_needed: false
safety_auditor_needed: false
arch_advisor_needed: false
implementer_needed: true

# Gate verdicts (set by orchestrator after each gate agent)
spec_review_verdict: CONFORMANT
spec_review_attempt: 1
safety_verdict:
safety_attempt: 0
code_review_verdict: APPROVED
code_review_attempt: 1
landing_verifier_verdict: VERIFIED
landing_verifier_attempt: 2
arch_advisor_verdict:

# Arch-advisor re-run counters (separate from initial gate passes)
arch_retry_spec_review_attempt: 0
arch_retry_safety_attempt: 0

# Pipeline configuration
remote_name: origin
roundtable_enabled: true
pr_url:

# Roundtable design review (Step 2.5)
roundtable_design_attempt: 0
roundtable_design_verdict:
roundtable_skipped:

# Roundtable pre-check review (Step 1.3)
roundtable_precheck_attempt: 1
roundtable_precheck_verdict: APPROVED

# Roundtable landing review (Step 8.5)
roundtable_landing_attempt: 2
roundtable_landing_verdict: APPROVED

# Roundtable-triggered gate re-run counters (separate from initial passes)
roundtable_retry_code_review_attempt: 1
roundtable_retry_spec_review_attempt: 1
roundtable_retry_safety_attempt: 0
roundtable_retry_landing_verifier_attempt: 1
status: READY-TO-LAND

# Doc-gardener (Step 9 sub-step 1)
doc_garden_verdict: DRIFT_FOUND
doc_garden_drift_count: 6
---

## pre-check

## Execution Brief: Delete noteScoring util, API wrappers, endpoint constants, and SimilarNote types

**PRD:** docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F18
**Feature index:** 6
**Feature pointer base:** /features/6
**Layer:** ui
**PRD-level invariants:** none
**Prototype mode:** none
**Dependencies:** MET — intra-PRD `needs[]` = [F16, F17]; both checked off `[x]` in `docs/exec-plans/active/feature-backlog.md` (lines 122, 126). No cross-PRD `Needs:` from the backlog. Verified: production-code grep over `ui/src/**/*.{ts,tsx}` for the F18 deletion symbols (`trackNoteAccess`, `getSimilarNotes`, `SimilarNote`, `accessCount`, `lastAccessedAt`, `noteScoring`, `computeForYouScore`, `getForYouNotes`, `getBlendedForYouNotes`) returns zero matches outside the four deletion-target files (`utils/noteScoring.ts`, `services/api.ts`, `config/api.ts`, `types/index.ts`) and the existing test files (`__tests__/utils/noteScoring.test.ts` — being deleted by F18 — plus the F16/F17 deletion-fence tests, which only string-grep for these names against `CommandPalette.tsx`/`NotesExplorer.tsx` and don't import the symbols). The graph is genuinely orphaned.
**Research needed:** NO
**Designer needed:** NO — pure orphan-symbol deletion behind already-stripped UI; no rendered surface, no tokens, no state. Layer is `ui` but no component is touched.
**Implementer needed:** YES
**Safety auditor needed:** NO — all nine ParchMark domain invariants in `docs/design-docs/core-beliefs.md` are backend-scoped (Note ORM tenant filter, auth on routes, raw SQL whitelist, typed mutations, etc.); F18 touches `ui/src/**` only and zero files under `backend/app/{auth,routers,models,services/embeddings,database}/`. Contract/oracle do not reference auth, credentials, tokens, or any security-sensitive control. The endpoint constants (`ACCESS`, `SIMILAR`) being removed are URL string literals for routes already deleted in F13/F14 — no surviving backend surface to consider.
**Arch-advisor needed:** NO — single-PRD final cleanup feature; no cross-module structural decisions; the architecture decision (delete the For You feature end-to-end) was made at PRD scope and is being executed file by file across F16 → F17 → F18.

**Intent:** refactoring
**Complexity:** standard

**What to build:**
Delete the orphaned For You feature scaffolding from the frontend now that F16 (CommandPalette strip) and F17 (NotesExplorer strip) have removed all call sites. Specifically: delete `ui/src/utils/noteScoring.ts` and its test file `ui/src/__tests__/utils/noteScoring.test.ts`; remove `trackNoteAccess` and `getSimilarNotes` (functions + the `default` export entries on lines 233-234) from `ui/src/services/api.ts`; remove the `ACCESS:` and `SIMILAR:` entries from `API_ENDPOINTS.NOTES` in `ui/src/config/api.ts`; remove the `SimilarNote` interface from `ui/src/types/index.ts` and the optional `accessCount?` / `lastAccessedAt?` fields from the `Note` interface there. Pure deletion — no surviving call paths, no behavior change, no orphan-spacing risk (no UI is rendered).

**New files:**
- (none)

**Modified files:**
- `ui/src/utils/noteScoring.ts` — DELETE the file (whole file, all 73 lines: `computeForYouScore`, `getForYouNotes`, `getBlendedForYouNotes`).
- `ui/src/__tests__/utils/noteScoring.test.ts` — DELETE the file.
- `ui/src/services/api.ts` — remove `SimilarNote` from the import on line 1 (keep `Note`); delete `trackNoteAccess` (lines 151-159) and `getSimilarNotes` (lines 161-170); delete the two trailing entries `trackNoteAccess,` and `getSimilarNotes,` in the `default` export object (lines 233-234).
- `ui/src/config/api.ts` — delete the `ACCESS: (id: string) => `/notes/${id}/access`,` line (line 14) and the `SIMILAR: (id: string) => `/notes/${id}/similar`,` line (line 15) from the `NOTES` block. Keep `LIST`, `CREATE`, `GET`, `UPDATE`, `DELETE`.
- `ui/src/types/index.ts` — delete the `SimilarNote` interface (lines 11-16) and the two optional fields on `Note` (`accessCount?: number;` line 7, `lastAccessedAt?: string;` line 8).

**Existing patterns to follow:**
- `docs/exec-plans/completed/handoffs/F15-delete-embeddings-services.md` — the prior cross-module deletion in this PRD; same "delete the orphan, don't leave behind shims" discipline.
- `docs/exec-plans/completed/handoffs/F16-strip-for-you-from-command-palette.md` and `F17-strip-for-you-from-notes-explorer.md` — sister features whose call-site removals are what made F18's targets orphaned. Their deletion-fence tests (`CommandPalette.f16-deletion.test.tsx`, `NotesExplorer.f17-deletion.test.tsx`) are the model for any F18 deletion-fence tests test-writer adds (string-grep against the surviving files for absence of the removed symbols).

**Assertion traceability:**
- `/features/6/oracle/assertions/0` → after deletion, filesystem check that `ui/src/utils/noteScoring.ts` and `ui/src/__tests__/utils/noteScoring.test.ts` do not exist. (`fs.existsSync` in a vitest, or shell `[ ! -e ... ]`.)
- `/features/6/oracle/assertions/1` → ripgrep `trackNoteAccess|getSimilarNotes` over `ui/src/services/api.ts` returns zero matches.
- `/features/6/oracle/assertions/2` → ripgrep for `ACCESS\|SIMILAR` in endpoint-constant declarations over `ui/src/config/api.ts` returns zero matches. (The check is scoped to the `NOTES` block — it's fine if a comment elsewhere happens to contain those words; per the contract, the gate is "endpoint-constant declarations".)
- `/features/6/oracle/assertions/3` → ripgrep `SimilarNote|accessCount|lastAccessedAt` over `ui/src/types/index.ts` returns zero matches.
- `/features/6/oracle/assertions/4` → `npx tsc --noEmit` from `ui/` exits 0. (Verified clean at pre-check time as the pre-deletion baseline; must remain clean after deletion.)

**Edge cases:**
- The `default` export object in `services/api.ts` (lines 226-239) contains `trackNoteAccess,` and `getSimilarNotes,` entries — these MUST be removed alongside the function definitions, otherwise tsc fails with "cannot find name". Do not just delete the function bodies.
- The `import { Note, SimilarNote }` line at the top of `services/api.ts` references both types — keep the `Note` import (still used by `getNotes`, `createNote`, `updateNote`); drop only `SimilarNote`. Resulting line: `import { Note } from '../types';`.
- The `Note` interface fields `accessCount?` and `lastAccessedAt?` are optional and will not cascade type errors when removed (the only consumer was `noteScoring.ts`, which is also being deleted in this same change). tsc must pass on the combined diff, not on either file in isolation.
- Backend `POST /api/notes/{id}/access` and `GET /api/notes/{id}/similar` endpoints were already removed in F13/F14 (verified: no `access`/`similar` routes in `backend/app/routers/notes.py`; absence enforced by `backend/tests/integration/notes/test_endpoint_removal.py`). F18 is the matching frontend-only deletion of the orphaned client wrappers and types. Implementer MUST NOT touch any backend file.
- The endpoint constants are only referenced via the `API_ENDPOINTS.NOTES.ACCESS(id)` / `API_ENDPOINTS.NOTES.SIMILAR(id)` accessor inside the to-be-deleted `trackNoteAccess` / `getSimilarNotes` functions — production grep confirms no other consumer. Safe to drop.
- Pre-existing F16/F17 deletion-fence test files (`CommandPalette.f16-deletion.test.tsx`, `NotesExplorer.f17-deletion.test.tsx`) string-match these symbols inside their assertion strings (e.g., `'trackNoteAccess vi.mock override...'`) — they don't import the symbols, so they keep passing after F18. Implementer MUST NOT modify those files.

**Risks:**
- Forgetting to update `services/api.ts` `default` export object → tsc breaks. Spec-reviewer / oracle assertion 4 catches this; flag it as the most likely slip.
- Accidentally deleting `Note` from the `services/api.ts` import (currently `import { Note, SimilarNote } from '../types'`) → cascade tsc failure across `getNotes` / `createNote` / `updateNote` / `deleteNote`. The import edit is precise: remove only `, SimilarNote`.
- Accidentally removing `GET:` from `API_ENDPOINTS.NOTES` (it's adjacent to `ACCESS`/`SIMILAR`) → `notes/{id}` reads break. Edit by exact key name, not by line number.
- Pipeline alphabetic-sort risk: tsc and prettier may re-format the surviving import / export lines. That's fine; just don't fight the formatter.

**Verify commands:** `cd ui && npx tsc --noEmit` AND `make test-ui-all` (lint + vitest, per roundtable-precheck consensus — adds straggler-import detection beyond tsc).

**Path convention:** Frontend code under `ui/src/`; tests mirror paths under `ui/src/__tests__/`. F18 touches no backend file.

### Constraints for downstream

- MUST: Delete exactly the four files / four edits enumerated in "Modified files" — the two file deletions, the two `services/api.ts` function removals (plus the matching `default` export entries and the `SimilarNote` import drop), the two `config/api.ts` endpoint-constant removals, and the three `types/index.ts` removals (`SimilarNote` interface + `accessCount?` + `lastAccessedAt?`). Nothing more.
- MUST: After the edit, `cd ui && npx tsc --noEmit` exits 0 AND ripgrep `trackNoteAccess|getSimilarNotes|SimilarNote` over `ui/src/{services/api.ts,types/index.ts,config/api.ts}` returns zero matches before declaring done.
- MUST: Keep `Note` (and only `Note`) in the `services/api.ts` import from `../types`; keep `LIST`, `CREATE`, `GET`, `UPDATE`, `DELETE` (and only those) under `API_ENDPOINTS.NOTES`.
- MUST NOT: Touch any file under `backend/`. The backend `/notes/{id}/access` and `/notes/{id}/similar` endpoints intentionally remain — their removal is out of scope for F18.
- MUST NOT: Modify `CommandPalette.f16-deletion.test.tsx`, `NotesExplorer.f17-deletion.test.tsx`, or `NotesExplorer.test.tsx`; those F16/F17 fences string-match the symbols inside assertion-message strings and continue to pass unchanged. No new docstrings, no refactors of adjacent code, no feature flags, no backwards-compat shims — pure deletion only.

**Ready:** YES
**Next hop:** test-writer

### Resolved feature (verbatim from keel-feature-resolve.py)

```json
{
  "ok": true,
  "feature_id": "F18",
  "feature_index": 6,
  "feature_pointer_base": "/features/6",
  "prd_path": "/home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json",
  "canonical_prd_path": "/home/dev/projects/parchmark/docs/exec-plans/prds/remove-for-you.json",
  "title": "Delete noteScoring util, API wrappers, endpoint constants, and SimilarNote types",
  "layer": "ui",
  "oracle": {
    "type": "unit",
    "assertions": [
      "Files `ui/src/utils/noteScoring.ts` and `ui/src/__tests__/utils/noteScoring.test.ts` do not exist.",
      "grep of `ui/src/services/api.ts` for `trackNoteAccess` and `getSimilarNotes` returns zero matches.",
      "grep of `ui/src/config/api.ts` for `ACCESS` and `SIMILAR` returns zero matches in endpoint-constant declarations.",
      "grep of `ui/src/types/index.ts` for `SimilarNote`, `accessCount`, and `lastAccessedAt` returns zero matches.",
      "`tsc --noEmit` over `ui/` succeeds with zero errors."
    ],
    "tooling": "tsc; ripgrep; filesystem check."
  },
  "contract": {
    "deleted_files": [
      "ui/src/utils/noteScoring.ts",
      "ui/src/__tests__/utils/noteScoring.test.ts"
    ],
    "api_ts_symbols_removed": [
      "trackNoteAccess",
      "getSimilarNotes"
    ],
    "config_api_constants_removed": [
      "ACCESS",
      "SIMILAR"
    ],
    "types_index_changes": {
      "SimilarNote_interface": "removed",
      "Note_accessCount_field": "removed",
      "Note_lastAccessedAt_field": "removed"
    }
  },
  "needs": [
    "F16",
    "F17"
  ],
  "prd_invariants_exercised": [],
  "backlog_fields": {
    "prd_slug": "remove-for-you",
    "prd_exempt_reason": null,
    "spec_ref": null,
    "design_refs": [],
    "needs_ids": [
      "F16",
      "F17"
    ],
    "human_markers": [],
    "prototype_mode": null
  },
  "classification": "JSON_PRD_PATH"
}
```

## roundtable-precheck-review

### Attempt 1 — APPROVED

**Panelists:** claude-opus-4-7 (codereviewer), codex (codereviewer), gemini-3.1-pro-preview (codereviewer).

#### Critique

- **Claude — APPROVE.** All 7 routing flags correct as written. Two non-blocking spec tightenings recommended: (a) tighten safety rationale wording to explicitly note "all nine invariants are backend-scoped"; (b) add `make test-ui-all` (vitest + lint) to F18's verify command alongside `tsc --noEmit`. Specifically called out the `services/api.ts` default-export object (lines 233-234) as a second deletion site beyond the named exports — easy to miss in a "delete the function" framing.
- **Codex — CONCERNS** (downgraded by orchestrator to non-blocking). Identified that the pre-check brief contained stale prose claiming "Backend still exposes `POST /api/notes/{id}/access` and `GET /api/notes/{id}/similar`" — verified by codex against `backend/app/routers/notes.py` (no such routes) and `backend/tests/integration/notes/test_endpoint_removal.py` (absence enforced). Proposed flipping `researcher_needed: true` to force reconciliation. **Orchestrator notes:** the prose was inaccurate but the routing decision is unaffected — F18 is FE-only either way. Treated as a brief-prose fix, not a flag flip; brief was edited inline.
- **Gemini — OBJECT** (not adopted; premises falsified). Proposed `researcher_needed: true`, `arch_advisor_needed: true`, complexity → `complex`, intent → `build`, citing (a) test-file references to the soon-deleted symbols, (b) `noteScoring` cited in `core-beliefs.md`, (c) backend "intentionally continues to return" `accessCount`/`lastAccessedAt`. Orchestrator verified: (a) `grep -rn "trackNoteAccess|getSimilarNotes|SimilarNote|accessCount|lastAccessedAt" ui/src/__tests__/` → only matches in `noteScoring.test.ts` itself (being deleted by F18); (b) `grep "noteScoring" docs/design-docs/core-beliefs.md` → zero matches; (c) backend endpoints already removed in F13/F14 (matches Codex's verification). All three premises false.

#### Canvass

Unanimous consensus across all three panelists: **KEEP all 7 routing flags as written**.

Final routing decision (all panelists agreed):
- intent: KEEP (refactoring)
- complexity: KEEP (standard)
- designer_needed: KEEP (false)
- researcher_needed: KEEP (false)
- safety_auditor_needed: KEEP (false)
- arch_advisor_needed: KEEP (false)
- implementer_needed: KEEP (true)

**Non-blocking notes (all three panelists agreed; orchestrator applied 1 + 2 inline above and propagated 3 to verify-command):**
1. Reconcile pre-check brief prose: strike claim that backend still exposes `/access` and `/similar` endpoints (deleted in F13/F14). ✅ APPLIED to "Edge cases" bullet at handoff line 107.
2. Tighten safety-skip rationale to explicitly state "all nine invariants are backend-scoped". ✅ APPLIED to "Safety auditor needed" rationale.
3. Extend oracle/verify command to include `make test-ui-all` (vitest + lint) alongside `tsc --noEmit`, so straggler imports surface in the same gate. ✅ APPLIED to "Verify commands".

**Verdict:** APPROVED.

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

## Test Report: Delete noteScoring util, API wrappers, endpoint constants, and SimilarNote types

**PRD:** docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F18
**Feature index:** 6
**Test files:** `ui/src/__tests__/utils/noteScoring.f18-deletion.test.ts`
**Tests written:** 9
**Status:** RED (all 9 assertions fail at assertion level, compiles clean)
**Failure output:** All 9 tests fail because pre-deletion state still has the files and symbols present. `fs.existsSync` returns `true` for both deletion targets; `readFileSync` + `.not.toMatch()` fails for all 7 source-grep assertions.

**Assertion traceability:**
- `/features/6/oracle/assertions/0` → "noteScoring.ts does not exist" + "noteScoring.test.ts does not exist" (2 tests)
- `/features/6/oracle/assertions/1` → "api.ts contains no trackNoteAccess reference" + "api.ts contains no getSimilarNotes reference" (2 tests)
- `/features/6/oracle/assertions/2` → "config/api.ts contains no ACCESS endpoint-constant declaration" + "config/api.ts contains no SIMILAR endpoint-constant declaration" (2 tests)
- `/features/6/oracle/assertions/3` → "types/index.ts contains no SimilarNote reference" + "types/index.ts contains no accessCount reference" + "types/index.ts contains no lastAccessedAt reference" (3 tests)
- `/features/6/oracle/assertions/4` → delegated to `tsc --noEmit` build gate (see Decisions)

### Decisions (optional)

- `tsc --noEmit` (assertion 4) is not a vitest assertion. It cannot be expressed as a passing/failing test inside vitest itself — it is a process-exit check. The landing-verifier runs `make test-ui-all` which includes this check; encoding a redundant shell-exec vitest assertion would add noise without signal. Noted explicitly per handoff instructions.
- `repoRoot` path uses `../../../..` (4 levels up from `ui/src/__tests__/utils/`) to reach the parchmark repo root. F16/F17 fences sit 2 directories deeper and use `../../../../../..`; the depth difference is intentional and correct.
- `ACCESS:` and `SIMILAR:` are matched as object-key declarations via `/\bACCESS\s*:/` and `/\bSIMILAR\s*:/`, not bare word matches. This ensures a comment mentioning "ACCESS" elsewhere in the file would not produce a false failure.
- No behavioral tests added — F18 is pure deletion; there is no surviving behavior to exercise. Fence pattern from F16/F17 applied verbatim.
- Test file placed at `ui/src/__tests__/utils/noteScoring.f18-deletion.test.ts` to mirror the `utils/` path of the primary deletion target, consistent with how F16/F17 fences mirror the component path of their targets.

**Next hop:** implementer

## implementer

## Implementation Report: Delete noteScoring util, API wrappers, endpoint constants, and SimilarNote types

**Files created/modified:**
- `ui/src/utils/noteScoring.ts` — DELETED (orphan For You scoring util, no remaining call sites).
- `ui/src/__tests__/utils/noteScoring.test.ts` — DELETED (tests for the deleted module).
- `ui/src/services/api.ts` — dropped `SimilarNote` from the `../types` import (kept `Note`); removed `trackNoteAccess` and `getSimilarNotes` function definitions; removed both entries from the `default` export object.
- `ui/src/config/api.ts` — removed `ACCESS:` and `SIMILAR:` entries from `API_ENDPOINTS.NOTES` (kept `LIST`, `CREATE`, `GET`, `UPDATE`, `DELETE`).
- `ui/src/types/index.ts` — removed `SimilarNote` interface and the `accessCount?` / `lastAccessedAt?` optional fields from `Note`.

**Change scope:** initial
**Changed paths:**
- `ui/src/utils/noteScoring.ts` (deleted)
- `ui/src/__tests__/utils/noteScoring.test.ts` (deleted)
- `ui/src/services/api.ts`
- `ui/src/config/api.ts`
- `ui/src/types/index.ts`

**Test status:** PASS — 9/9 F18 deletion-fence tests green.
**Commands run:**
- `cd ui && npx vitest run src/__tests__/utils/noteScoring.f18-deletion.test.ts` → `Test Files 1 passed (1) | Tests 9 passed (9)`
- `cd ui && npx tsc --noEmit` → exit 0
- `grep -nE "trackNoteAccess|getSimilarNotes" ui/src/services/api.ts` → exit 1 (zero matches)
- `grep -nE "SimilarNote|accessCount|lastAccessedAt" ui/src/types/index.ts` → exit 1 (zero matches)
- `grep -nE "\bACCESS\s*:|\bSIMILAR\s*:" ui/src/config/api.ts` → exit 1 (zero matches)

**Blockers (if any):** none

### Decisions

- Deleted the entire `trackNoteAccess` + `getSimilarNotes` block in `services/api.ts` (the blank line separator between them and the `// Settings API` comment) as a single contiguous edit, replacing with `// Settings API` directly — preserves prettier-friendly single-blank-line separation between exports without leaving an orphan blank gap.
- Used a full-file rewrite for `types/index.ts` rather than three separate edits because the file is 22 lines and the combined diff is clearer; tsc and the F18 fence both pass.
- Did not touch any test file other than the mandated deletion of `ui/src/__tests__/utils/noteScoring.test.ts`. F16/F17 fences and `NotesExplorer.test.tsx` left untouched per pre-check constraints.
- No backend file modified. F18 is FE-only; backend `/access` and `/similar` endpoints were already removed in F13/F14.
- No comments, no feature flags, no shims added — pure deletion as specified.

**Next hop:** code-reviewer

### Pass 2 — roundtable doc-drift fix

**Changed paths (Pass 2):**
- `AGENTS.md`
- `ui/README.md`
- `ARCHITECTURE.md`
- `docs/design-docs/core-beliefs.md`

**Per-file diff summary:**
- `AGENTS.md` line 131 — removed `noteScoring,` from the `utils/` directory-map comment.
- `AGENTS.md` line 133 — removed `, SimilarNote` from the `types/` directory-map comment.
- `ui/README.md` line 108 — removed `, SimilarNote` from the `types/` description (now `(Note)`).
- `ARCHITECTURE.md` line 49 — removed `, SimilarNote` from the layer-map `Types` row (now `Note, User interfaces`); free-form right-side text, no box-padding to preserve.
- `ARCHITECTURE.md` line 74 — removed `, SimilarNote` from the `types/index.ts` directory-reference (now `Note, User`).
- `ARCHITECTURE.md` line 85 — deleted the entire `noteScoring.ts          # "For You" heuristic scoring` line; file no longer exists.
- `ARCHITECTURE.md` lines 269-281 — deleted the entire `### Embeddings & Similarity` section (intro + code block). Both items in the code block (`GET /api/notes/{id}/similar` deleted in F13, `Command Palette "For You"` deleted in F16/F17/F18) were the only contents; with both gone the section had no surviving content. Section header + intro removed as a coherent unit; surrounding `---` separator and `## Dependency Rules (Summary)` heading preserved.
- `docs/design-docs/core-beliefs.md` line 81 — replaced `e.g. \`/logout\`, \`/notes/{id}/access\`` with `e.g. \`/logout\`` (dropped the dead-endpoint example; surviving example kept).

**Verification:**
- `grep -nE "SimilarNote|noteScoring" AGENTS.md ui/README.md ARCHITECTURE.md` → exit 1 (zero matches).
- `grep -nE "/notes/\{id\}/similar|/notes/\{id\}/access" ARCHITECTURE.md docs/design-docs/core-beliefs.md` → exit 1 (zero matches).
- `grep -nE "Command Palette \"For You\"|Command Palette 'For You'" ARCHITECTURE.md` → exit 1 (zero matches).
- `cd ui && npx tsc --noEmit` → exit 0 (no-op as expected; docs only).
- `cd ui && npx vitest run src/__tests__/utils/noteScoring.f18-deletion.test.ts` → 9/9 PASS.

### Decisions (Pass 2)

- Deleted the entire `### Embeddings & Similarity` section in `ARCHITECTURE.md` rather than leaving an empty code block. Both line items in the block were on the F18 fix list; the surrounding intro ("Optional feature—silently degrades when `OPENAI_API_KEY` is absent.") had no surviving referent at the FE-architecture layer. Treated as a deletion (in scope) rather than a rewrite (out of scope).
- Backend-side embeddings residue (`backend/README.md`, `schemas.py SimilarNoteResponse`, `docs/ai-embeddings-design.md`) explicitly left untouched per scope guidance — those are F19 residual / doc-gardener territory.
- Did not retouch the `Utils ... scoring` description on ARCHITECTURE.md line 43 ("Error handling, date formatting, scoring") — the word "scoring" was not on the fix list; spec-reviewer / doc-gardener can flag separately if it counts as drift.

**Next hop:** code-reviewer

## code-reviewer
<!-- Code quality review appended here. Verdict: APPROVED | CHANGES NEEDED -->

### Pass 2 -- post-roundtable doc-drift fix re-review

**Files reviewed:** AGENTS.md, ui/README.md, ARCHITECTURE.md, docs/design-docs/core-beliefs.md

**Checks:**
1. Pass 1 source-code diff unchanged -- CONFIRMED. All source-change paths show empty diff against main; edits remain in working tree, consistent with pre-commit state.
2. Doc edits clean -- CONFIRMED. No orphan trailing whitespace; no broken markdown; surrounding lines unaffected in all 4 files.
3. Out-of-scope docs untouched -- CONFIRMED. backend/README.md, docs/ai-embeddings-design.md, backend/app/schemas/schemas.py all show empty diff.
4. No dangling cross-references to removed section -- CONFIRMED. No "Embeddings & Similarity" or "see" pointer to the deleted section survives in ARCHITECTURE.md. Remaining backend-layer embeddings references (lines 132, 157, 173, 176, 195, 197) are in the backend architecture section and remain accurate.

**Findings:**
- [MINOR] ARCHITECTURE.md:43 -- "scoring" survives in the Utils layer description ("Error handling, date formatting, scoring"). noteScoring.ts is deleted; this is a ghost reference. Implementer flagged explicitly in Pass 2 Decisions as deferred to doc-gardener. Not blocking.
- [MINOR] ui/README.md:109 -- same residual: "Utilities (errorHandler, markdown, scoring)". Same disposition.

**Summary:** Pass 2 doc edits are precise and contained. The two residual "scoring" words are minor and intentionally deferred by the implementer. No CRITICAL or MAJOR issues.

**Verdict:** APPROVED

## spec-reviewer

### Pass 1 — initial conformance review

**Spec Conformance: Delete noteScoring util, API wrappers, endpoint constants, and SimilarNote types**

**Verdict:** CONFORMANT
**Attempt:** 1

**PRD:** docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F18
**Feature index:** 6
**Feature pointer base:** /features/6
**Code:** `ui/src/services/api.ts`, `ui/src/config/api.ts`, `ui/src/types/index.ts` (+ deletions of `ui/src/utils/noteScoring.ts` and `ui/src/__tests__/utils/noteScoring.test.ts`)
**Tests:** `ui/src/__tests__/utils/noteScoring.f18-deletion.test.ts`

**Oracle assertion checks:**
- `/features/6/oracle/assertions/0` — verified: both files absent (Glob returns no results)
- `/features/6/oracle/assertions/1` — verified: `trackNoteAccess` and `getSimilarNotes` absent from `api.ts` (file is 217 lines with no trace of either symbol)
- `/features/6/oracle/assertions/2` — verified: `ACCESS` and `SIMILAR` keys absent from `config/api.ts` NOTES block
- `/features/6/oracle/assertions/3` — verified: `SimilarNote`, `accessCount`, `lastAccessedAt` absent from `types/index.ts`
- `/features/6/oracle/assertions/4` — delegated to `tsc --noEmit` build gate; implementer confirmed exit 0; test-writer decision logged in test file header

**Contract conformance:**
- `contract.deleted_files` — both files deleted. Conforms.
- `contract.api_ts_symbols_removed` — functions, default-export entries, and import reference all removed; `Note` import retained. Conforms.
- `contract.config_api_constants_removed` — `ACCESS` and `SIMILAR` gone; `LIST`, `CREATE`, `GET`, `UPDATE`, `DELETE` retained. Conforms.
- `contract.types_index_changes` — `SimilarNote` interface removed; `accessCount?` and `lastAccessedAt?` removed from `Note`. Conforms.

**Constraints honored:**
- MUST delete exactly the enumerated files/edits — verified.
- MUST keep `Note` in `api.ts` import and `LIST/CREATE/GET/UPDATE/DELETE` in NOTES block — verified.
- MUST NOT touch backend files — verified (no backend paths in changed files).
- MUST NOT modify F16/F17 fence tests or `NotesExplorer.test.tsx` — verified.

**Deviations:** None.

### Pass 2 — post-roundtable doc-drift re-review

**Verdict:** CONFORMANT
**Attempt:** 2

| Contract item | Check |
|-|-|
| `deleted_files` — `noteScoring.ts` + test deleted | PASS — files absent from `ui/src/` |
| `api_ts_symbols_removed` — `trackNoteAccess`, `getSimilarNotes` | PASS — zero matches in `ui/src/services/api.ts` |
| `config_api_constants_removed` — `ACCESS`, `SIMILAR` keys | PASS — zero matches in `ui/src/config/api.ts` |
| `types_index_changes` — `SimilarNote`, `accessCount?`, `lastAccessedAt?` | PASS — zero matches in `ui/src/types/index.ts` |
| MUST NOT touch `backend/` | PASS — Pass 2 edits are 4 doc files only; no backend path in diff |
| Doc edits vs. contract scope | PASS — contract scopes code symbols; doc edits don't violate any contract key, only reinforce current-state accuracy |

**Deviations:** None.

## safety-auditor
<!-- Audit report appended here (if applicable). Verdict: PASS | VIOLATION -->

## arch-advisor-verification
<!-- Independent structural review appended here by Arch-advisor at Step 7.5 (if applicable). -->

## landing-verifier

### Pass 1 — initial landing verification

**Landing Report: Delete noteScoring util, API wrappers, endpoint constants, and SimilarNote types**

**Pipeline:** frontend
**Verification:** All 5 gates passed. Full UI test suite: 43 test files, 570 tests, 0 failures, exit 0. Coverage: 95.3% statements (floor: 90%). F18 fence test (`noteScoring.f18-deletion.test.ts`) ran with 9/9 passing. F16/F17 fences also green. ESLint: 0 warnings. Backend diff: empty (0 files touched).

| Gate | Result |
|-|-|
| 1. Frontend test gate (`make test-ui-all`) | PASS — 43 files, 570 tests, exit 0; F18 fence (9 tests) present and green |
| 2. Backend untouched | PASS — `git diff origin/main..HEAD -- backend/` is empty |
| 3. Diff sanity | PASS — 5 files changed (2 deletions, 3 modifications) all under `ui/src/`; 1 new fence test untracked (expected) |
| 4. Tree clean | PASS — only expected uncommitted items: 4 implementer edits (2 deletions, 3 modifications staged) + handoff file + fence test (both untracked) |
| 5a. Oracle: noteScoring.ts + test absent | PASS |
| 5b. Oracle: api.ts trackNoteAccess/getSimilarNotes | PASS |
| 5c. Oracle: config/api.ts ACCESS/SIMILAR constants | PASS |
| 5d. Oracle: types/index.ts SimilarNote/accessCount/lastAccessedAt | PASS |
| 5e. Oracle: tsc --noEmit exits 0 | PASS (covered by make test-ui-all, lint step passed, no type errors) |

**Spec conformance:** CONFIRMED
**Safety audit:** NOT APPLICABLE (FE-only, safety-auditor correctly skipped per pre-check; all nine invariants are backend-scoped)
**Code review:** APPROVED
**Architecture review:** N/A (single-PRD final cleanup; no cross-module structural decisions)
**Doc drift:** NONE

**Status:** VERIFIED

**Next hop:** orchestrator (runs roundtable review if enabled, then Step 9 post-landing procedure)

## roundtable-landing-review

### Attempt 1 — CONCERNS (doc drift)

**Panelists:** claude-opus-4-7, codex, gemini-3.1-pro-preview (3 in crosscheck + 3 in critique = 6 total perspectives).

#### Crosscheck

- **Claude (generalist):** APPROVE. Verified backend `NoteResponse` schema (`backend/app/schemas/schemas.py:78-85`) emits only `id, title, content, createdAt, updatedAt` — no contract drift. Two MAJOR-severity items in `AGENTS.md:131,133`. Fence sufficiency adequate. F18/F19 sequencing safe either order.
- **Codex (codereviewer):** CONCERNS — 5 stale doc surfaces: `ARCHITECTURE.md:49,74,85,274` (`SimilarNote`, `noteScoring.ts`, `/notes/{id}/similar`); `ui/README.md:108`; `docs/design-docs/core-beliefs.md:81` uses dead `/notes/{id}/access` example. FE type-shrinkage safe (verified backend payload). Recommended fix in this PR.
- **Gemini (planner):** CONCERNS — convergent on doc drift across `ARCHITECTURE.md`, `AGENTS.md`, `README.md`, `backend/README.md`. Recommended bundling fix in this PR. Suggested follow-up to remove fence tests entirely once F19/F20 land.

#### Critique

- **Claude:** CONCERNS — flagged `ui/README.md:108`, `backend/README.md:263-265` (F19 residue), orphaned `SimilarNoteResponse` in `schemas.py:88` (F19 residue), fence regex bypassability (MINOR), `core-beliefs.md:81` dead-route example.
- **Codex:** CONCERNS — fence-test bypassability (MEDIUM): tests only check 3 specific files for specific symbols; could re-introduce under different names elsewhere. Doc drift across same surfaces.
- **Gemini:** CONCERNS — fence-test bypassability (HIGH); convergent doc drift in `docs/ai-embeddings-design.md` and core-beliefs example.

**Convergent finding (5/6 panelists):** Documentation drift in current-state living docs. Orchestrator triaged: in-scope for F18 = `AGENTS.md`, `ui/README.md`, `ARCHITECTURE.md`, `docs/design-docs/core-beliefs.md`. Out of scope (F19/follow-up) = `backend/README.md`, `SimilarNoteResponse` schema, full `docs/ai-embeddings-design.md` rewrite, fence-test rewrite.

**Action taken:** Dispatched implementer Pass 2 with scoped doc-drift fix. Gates re-ran with retry counters (code-reviewer Pass 2 → APPROVED; spec-reviewer Pass 2 → CONFORMANT; landing-verifier Pass 2 pending).

**Verdict:** CONCERNS (Attempt 1) — see Attempt 2 below for resolution.

### Attempt 2 — APPROVED

**Panelists:** claude-opus-4-7, codex, gemini-3.1-pro-preview (3 in crosscheck).

#### Crosscheck

- **Claude (generalist):** APPROVE. In-scope drift resolved. 8 findings — all RESOLVED or DEFER. Recommends opening F19-residual follow-up items: backend/README.md Note model fields + `SimilarNoteResponse` orphan. doc-gardener handles historical embeddings doc + ghost-words.
- **Codex (codereviewer):** APPROVE. One LOW finding: 2 surviving "scoring" ghost-words in layer-map descriptions (`ARCHITECTURE.md:43`, `ui/README.md:109`); not blocking. No correctness, security, error-handling, or contract blockers. Deferrals reasonable.
- **Gemini (planner):** APPROVE. Considered and rejected the "monolithic deletion" alternative (block F18 until F19 + doc-gardener bundle); concluded F18's bounded scope is correct architectural boundary. 95.3% coverage strong. Deferred items have named owners.

**Convergent verdict (3/3 APPROVE):** F18 is ready to commit. The two surviving "scoring" ghost-words and the historical embeddings design doc are deferred to doc-gardener (Step 9 sub-step 1, runs unconditionally). The F19-residual items (backend/README.md, `SimilarNoteResponse` schema) will be appended to `docs/exec-plans/tech-debt-tracker.md` in Step 9 sub-step 2.

**Verdict:** APPROVED.

## Landing Report: Delete noteScoring util, API wrappers, endpoint constants, and SimilarNote types

### Pass 2 — post-roundtable doc-drift re-verification

**Pipeline:** frontend
**Note:** Branch already merged to main at `4b765e4` before Pass 2 ran. All verification performed against current HEAD (= origin/main).

| Gate | Result |
|-|-|
| 1. `make test-ui-all` | PASS — 43 files, 570 tests (0 failures), exit 0; coverage 95.3% (floor 90%) |
| 2. Backend untouched | PASS — `git diff origin/main..HEAD -- backend/` empty |
| 3. Diff sanity | PASS — HEAD == origin/main; Pass 2 doc edits (`AGENTS.md`, `ui/README.md`, `ARCHITECTURE.md`, `docs/design-docs/core-beliefs.md`) are merged |
| 4. F18 fence (9 tests) | PASS — all 9 assertions green (`noteScoring.f18-deletion.test.ts`) |
| 5a–5e. Oracle assertions | PASS — all five confirmed passing (fence test run independently, exit 0) |

Vitest summary: `Test Files  43 passed (43) / Tests  570 passed (570)`

**Spec conformance:** CONFIRMED
**Safety audit:** NOT APPLICABLE
**Code review:** APPROVED (Pass 2)
**Architecture review:** SOUND — doc edits remove stale symbols only; no structural changes
**Doc drift:** NONE — roundtable-flagged drift addressed in Pass 2; no new drift detected

**Status:** VERIFIED

**Next hop:** orchestrator (Step 9 post-landing procedure)
