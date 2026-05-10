# F17 — Strip forYouNotes block from NotesExplorer.tsx

---
status: READY-TO-LAND
pipeline: frontend
prd_ref: docs/exec-plans/prds/remove-for-you.json#F17
spec_ref: docs/exec-plans/prds/remove-for-you.json#F17

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
pr_url:

# Roundtable pre-check review (Step 1.3)
roundtable_precheck_attempt: 2
roundtable_precheck_verdict: APPROVED

# Roundtable design review (Step 2.5)
roundtable_design_attempt: 0
roundtable_design_verdict:
roundtable_skipped:

# Roundtable landing review (Step 8.5)
roundtable_landing_attempt: 1
roundtable_landing_verdict: APPROVED

# Roundtable-triggered gate re-run counters (separate from initial passes)
roundtable_retry_code_review_attempt: 0
roundtable_retry_spec_review_attempt: 0
roundtable_retry_safety_attempt: 0

# Doc-gardener (Step 9 sub-step 1)
doc_garden_verdict: DRIFT_FOUND
doc_garden_drift_count: 3
---

## pre-check

## Execution Brief: Strip forYouNotes block from NotesExplorer.tsx

**PRD:** docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F17
**Feature index:** 5
**Feature pointer base:** /features/5
**Layer:** ui
**PRD-level invariants:** none
**Prototype mode:** none
**Dependencies:** MET — `needs[]` empty (intra-PRD); no cross-PRD `Needs:`. Sister F16 already landed (commit 3339b89) but is not a hard dependency of F17.
**Research needed:** NO
**Designer needed:** NO — see "Designer decision rationale" below.
**Implementer needed:** YES
**Safety auditor needed:** NO (pure UI change; touches `ui/src/**` only — none of `backend/app/{auth,routers,models,services/embeddings,database}/`; no auth/credentials/security surface; the `trackNoteAccess` call site removal is a UI telemetry write, not a security-sensitive control)
**Arch-advisor needed:** NO (F18 is sequenced behind F17 by the pipeline; no co-architecture needed)

**Intent:** mid-sized
**Complexity:** standard

**Designer decision rationale (post-roundtable):**
Roundtable was split 2-reject / 1-apply. NO holds for these reasons, applied as first-principles re-derivation now that complexity is `standard`:
1. **F16 precedent (PR #88, commit 3339b89, just landed):** the identical surgical-deletion pattern was applied to `CommandPalette.tsx` — same For You block, same `trackNoteAccess` removal, same `getBlendedForYouNotes` import drop — and shipped clean without a designer. F17 is the structural twin in `NotesExplorer.tsx`.
2. **No new layout, no new state, no empty-state risk:** the surviving render path is `renderDateGroups` (NotesExplorer.tsx:122–150), which already handles the full notes list. Notes-explorer is non-empty by construction (authenticated user lands on it post-login with at least their own notes; the empty-state for zero notes is unrelated to For You). The For You section was a 3-item splice on top of a date-grouped list — removing it leaves the date-grouped list rendering as it always has.
3. **No tokens or styling decisions:** `section.forYou` is being deleted, not renamed or remapped. No new colors, spacing, or typography decisions.
4. **Codex's UI+standard→designer rubric is a heuristic, not a hard rule:** the rubric exists to catch interface design risk. Pure deletions with a precedent twin and no surviving state-machine branches are precisely the case where the heuristic over-fires. KEEL's pre-check spec ("Trivial UI features ... skip the designer") was the auto-rule for trivial; for standard the call is judgment, and the F16 twin makes the judgment cheap.

If the implementer encounters orphan-spacing visible in the running app (e.g. a stray gap where the For You section used to render), they MUST halt and request designer consultation before flailing on CSS — but the pre-deletion render path makes this outcome very unlikely.

**What to build:**
Remove the For You section from `NotesExplorer.tsx`: drop the `forYouNotes` memo, the `getBlendedForYouNotes` import, the `trackNoteAccess` import + call (replace with direct `navigate`), the `renderForYouSection` function and its render-site, and the `section.forYou` semantic token. Update the test file to drop For You assertions and the now-unused `trackNoteAccess` mock. Lines 70–73, 79–82, 88, 94–120, 235 in NotesExplorer.tsx are the surgical hot spots.

**New files:**
- (none)

**Modified files:**
- `ui/src/features/notes/components/NotesExplorer.tsx` — remove imports (lines 13, 14), `forYouNotes` memo (70–73), inline `forYou` splice in `visibleNotes` (79–82 — simplify to `[...allNotesGrouped.flatMap(g => g.notes)]` when not searching), `trackNoteAccess` call in `handleSelect` (88), `renderForYouSection` function (94–120), and `{renderForYouSection()}` render-site (235).
- `ui/src/__tests__/features/notes/components/NotesExplorer.test.tsx` — drop `trackNoteAccess` mock (line 23) and any For You assertions (`for-you-header` testid, `FOR YOU` text, blended-ranking expectations).
- `ui/src/styles/foundations/semanticTokens.ts` — remove `'section.forYou': 'secondary.600'` (line 31). Keep `section.recent`.

**Existing patterns to follow:**
- `ui/src/features/ui/components/CommandPalette.tsx` (post-F16) — same surgical-deletion pattern for For You section, applied successfully in PR #88 / commit 3339b89.
- `NotesExplorer.tsx:122–150` (`renderDateGroups`) — the surviving render path; ensure `visibleNotes` simplification still feeds virtualization correctly.

**Assertion traceability:**
- `/features/5/oracle/assertions/0` → ripgrep `forYouNotes|getBlendedForYouNotes|trackNoteAccess` against `NotesExplorer.tsx` after edit must be empty.
- `/features/5/oracle/assertions/1` → vitest `NotesExplorer.test.tsx` passes after dropping For You assertions and `trackNoteAccess` mock.
- `/features/5/oracle/assertions/2` → ripgrep `forYou` against `semanticTokens.ts` must be empty.

**Edge cases:**
- `handleSelect` no longer needs to fire-and-forget `trackNoteAccess` — collapse to direct `navigate`. Keep the `useCallback` (still used by virtualized + grouped rows).
- `visibleNotes` memo previously concatenated `[...forYou, ...grouped]`; after deletion, the `useVirtualScroll` threshold still applies to the unsearched grouped list, but note `useVirtualScroll` is currently only consumed in the search branch (renderSearchResults) — confirm `visibleNotes` is still referenced; if it becomes dead after the simplification, remove it too.
- `data-testid="for-you-header"` disappears — any test still asserting on it must be removed.
- `services/api.ts` `trackNoteAccess` export becomes orphan after F17 + F16; leave it for F18 to delete.
- Behavior change is user-visible (the "FOR YOU" section disappears) and a telemetry write (`POST /api/notes/{id}/access`) stops firing on note selection — this is the deliberate user-facing scope of F17 and is why intent is `mid-sized`, not `refactoring`.

**Risks:**
- Test file may rely on `trackNoteAccess` mock for unrelated assertions (low — mock is For You-specific). test-writer must verify before deletion.
- `visibleNotes` may become dead code after simplification — implementer must check and excise to keep the change minimal.
- `section.forYou` could theoretically be referenced elsewhere — grep already confirms NotesExplorer.tsx is the sole consumer.
- Orphan vertical spacing where the For You section used to render (low — the surviving date-grouped list renders directly; no wrapper container is being orphaned). If observed in dev, halt and consult the designer rather than ad-hoc CSS edits.

**Verify command:** `make test-ui-all`

**Path convention:** Frontend code under `ui/src/`; tests mirror paths under `ui/src/__tests__/`.

### Constraints for downstream

- MUST: Delete only the For You surface enumerated in the contract (`forYouNotes_block`, `getBlendedForYouNotes_import`, `trackNoteAccess_import`, `trackNoteAccess_call`, `semanticTokens_section_forYou`); leave `section.recent` and the date-grouped render path untouched.
- MUST: After deletion, ripgrep `forYouNotes|getBlendedForYouNotes|trackNoteAccess` over `NotesExplorer.tsx` and `forYou` over `semanticTokens.ts` must both return zero matches before declaring done.
- MUST: Keep `handleSelect` as a `useCallback` returning `navigate('/notes/${noteId}')` — no `trackNoteAccess` call, no behavioral change to navigation.
- MUST: If orphan vertical spacing appears in the running app where For You used to render, HALT and request a designer consultation rather than fixing it with ad-hoc CSS.
- MUST NOT: Touch `noteScoring.ts`, `services/api.ts` `trackNoteAccess` export, `SimilarNote` types, or any backend module — those deletions belong to F18.
- MUST NOT: Add docstrings, refactor unrelated memos, rename `section.recent`, or introduce feature flags / backwards-compat shims; this is a pure deletion.

## roundtable-precheck-review
<!-- Multi-model advisory review of pre-check routing (Step 1.3). Append-only across attempts. -->

### Attempt 1 — CONCERNS

Pre-check's initial classification:
`intent: refactoring | complexity: trivial | designer_needed: NO | researcher_needed: NO | safety_auditor_needed: NO | arch_advisor_needed: NO | implementer_needed: YES`

#### Critique

Three panelists (claude-opus-4-7, codex, gemini-3.1-pro) attacked the classification independently. Convergent findings:

- **HIGH (3/3) — `intent: refactoring` is wrong.** Refactoring preserves behavior; F17 deletes user-visible UI (the "FOR YOU" section) and a telemetry write (`trackNoteAccess` POST). Recommended `mid-sized` (closest schema-valid enum).
- **MEDIUM (1/3, Codex) — `complexity: trivial` underclassifies.** Pre-check's own rubric reserves trivial for single-file <10-line work; F17 spans 3 files and ~40 LOC of NotesExplorer.tsx alone.
- **MEDIUM (3/3, low–medium severity) — `designer_needed: NO` may miss layout risk.** Codex argues KEEL's UI+non-trivial rubric → designer. Claude/Gemini counter that the F16 precedent (CommandPalette, just landed) ran without a designer and the surviving date-grouped render path absorbs the deletion.
- **MEDIUM (2/3) — `safety_auditor_needed` may miss telemetry write removal.** Counter: parchmark CLAUDE.md scopes safety-auditor strictly to `backend/app/{auth,routers,models,services/embeddings,database}/`; F17 is `ui/src/**` only.
- **LOW (1/3, Claude) — `arch_advisor_needed` could review F17+F18 as one arc.** Counter: pipeline already gates F18 on F17 landing.

#### Canvass

Synthesis across the same three panelists, each producing a final routing block:

- **Apply (3/3 unanimous):** `intent: refactoring → mid-sized`. `complexity: trivial → standard`.
- **Reject (3/3 unanimous):** `safety_auditor_needed` flip; `arch_advisor_needed` flip; `researcher_needed` flip. Pre-check's NO holds.
- **Divergent — `designer_needed`:** Claude REJECT (F16 precedent, render path intact). Codex APPLY (rubric: layer==ui + complexity≥standard → designer YES; reinforced by orphan-spacing risk). Gemini REJECT (date-grouped fallback handles it). Vote: 2 reject, 1 apply.

#### Recommended action

Send these findings back to pre-check for revision. Convergent flips are unambiguous:
- `intent: mid-sized`
- `complexity: standard`

Pre-check decides `designer_needed` — the divergence hinges on whether KEEL's UI+standard→designer rubric is rule-based (Codex) or precedent-based (Claude/Gemini's F16 analogy). Pre-check is authoritative and resolves the call.

### Attempt 2 — APPROVED (with advisory visual-QA conditions)

Pre-check applied 2 convergent flips (`intent → mid-sized`, `complexity → standard`) and held `designer_needed: NO` with documented first-principles reasoning. Re-running critique + canvass on the revised classification.

#### Critique

- **Claude (high):** F16 precedent reasoning is circular — F16 also skipped designer, citing it as validation just repeats the prior bet. Need an independent visual check, not a precedent appeal. NotesExplorer ≠ CommandPalette structurally (react-window virtualization). Orphan-spacing self-heal is reactive — make it an explicit gate or accept a designer pre-pass. Routing is plausible but needs explicit visual-QA in implementer brief.
- **Codex (medium):** F16 precedent is overstated; NotesExplorer pulls more (forYouNotes, visibleNotes, shared handleSelect/trackNoteAccess, test assertions) than CommandPalette did. Keep `designer_needed: NO` if you want, but justify it from the unchanged UX contract, not the F16 surgical-pattern analogy. Make visual QA an explicit DoD item.
- **Gemini (high):** Flip `designer_needed: YES`. Sidebars (NotesExplorer) leave structural holes; overlays (CommandPalette) shrink naturally. False equivalence.

**Note on Gemini's dissent:** Gemini's "removing a permanent sidebar" framing misreads scope. F17 strips one *block* (the For You section) *from* the sidebar — the sidebar itself, the date-grouped notes list, and the parent layout grid all remain. The grounded reading (Claude, Codex) holds.

#### Canvass

Final 3-way vote on `designer_needed`:
- **Claude:** Option 1 — `NO` + explicit visual-QA gate (variant (a) of attempt-2 critique).
- **Codex:** Option 1 — `NO` + visual-QA as explicit DoD, justified by unchanged UX contract.
- **Gemini:** Option 2 — flip to `YES`; persistent-sidebar premise (factually weak — see note above).

**Verdict:** APPROVED with conditions. 2/3 grounded panelists converge on Option 1; Gemini's dissent rests on a misread of F17's scope.

#### Advisory conditions (orchestrator-logged for downstream agents)

Read by test-writer + implementer as additional acceptance criteria, in addition to the pre-check `### Constraints for downstream`:

- **Visual-QA DoD (test-writer + implementer):**
  - No orphan dividers, headers, or empty containers remain in the rendered NotesExplorer after F17 lands.
  - The sidebar's vertical rhythm below the removed section matches the pre-F17 baseline (no extra gap, no collapsed spacing).
  - The "no notes" empty-state path (when the user has zero notes) is exercised at least once; F17 must not change its behavior.
- **react-window invariants (implementer):** verify row-height stability, `itemKey` continuity, and overscan behavior on the surviving date-grouped path after `visibleNotes` simplification. The For You splice was at the head of the list — its removal shifts virtual indices.
- **trackNoteAccess scope check (implementer):** before deleting the call site in `handleSelect`, ripgrep the `ui/src/` tree to confirm CommandPalette.tsx (post-F16) is the only other call site, and that no other surviving feature relies on it. The export deletion itself stays in F18 scope.
- **Halt-and-consult escalation:** if the implementer encounters orphan-spacing or virtualization regressions in dev that aren't trivially fixed, halt and dispatch frontend-designer rather than guessing on CSS. The roundtable explicitly accepted `NO` on the basis that this escalation path remains live.

These conditions are **advisory** (per KEEL principle: roundtable never directly blocks). Authoritative gates remain spec-reviewer + code-reviewer. test-writer should encode the visual-QA DoD into Vitest assertions where feasible (orphan-element absence, render-tree shape after F17); residual visual checks fall to landing-verifier's manual smoke or a quick Chrome DevTools MCP pass per `CLAUDE.md` §"Visual QA".


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

## Test Report: Strip forYouNotes block from NotesExplorer.tsx

**PRD:** docs/exec-plans/prds/remove-for-you.json
**Feature ID:** F17
**Feature index:** 5
**Test files:**
- `ui/src/__tests__/features/notes/components/NotesExplorer.test.tsx` (modified)
- `ui/src/__tests__/features/notes/components/NotesExplorer.f17-deletion.test.tsx` (new)

**Tests written:** 20 total (14 behavioral + 6 deletion-fence)
**Status:** RED (assertions fail for the right reason — For You symbols still present in source; behavioral tests compile clean)

**Failure output (representative):**
```
FAIL NotesExplorer > for-you-header element is absent when notes exist (F17 orphan-element absence)
  Error: expected document not to contain element, found <p data-testid="for-you-header">FOR YOU</p>

FAIL F17 deletion: NotesExplorer.tsx contains no forYouNotes reference
FAIL F17 deletion: NotesExplorer.tsx contains no getBlendedForYouNotes reference
FAIL F17 deletion: NotesExplorer.tsx contains no trackNoteAccess reference
FAIL F17 deletion: semanticTokens.ts contains no forYou token

Tests: 5 failed | 15 passed
```

**Dropped from existing test file:**
- Line 22–24: `vi.mock('../../../../services/api', ...)` with `trackNoteAccess: vi.fn()` — removed entirely
- Lines 93–96: `'renders "FOR YOU" section header when notes exist'` — dropped (was `getByTestId('for-you-header')` presence assertion)
- Lines 160–166: `'hides FOR YOU section when searching'` — dropped (was a For You-specific behavior test; orphan-absence version retained)
- Lines 168–171: `'does not show FOR YOU when no notes'` — dropped (folded into new orphan-absence tests)

**Assertion traceability:**
- `/features/5/oracle/assertions/0` → `NotesExplorer.tsx contains no forYouNotes reference`, `...no getBlendedForYouNotes reference`, `...no trackNoteAccess reference` (deletion fence)
- `/features/5/oracle/assertions/1` → `for-you-header element is absent when notes exist`, `...when searching`, `...when notes array is empty`; `renders date group headers via renderDateGroups path`; `renders all notes as ExplorerNoteCard elements via date-grouped path`; `shows "No notes yet" empty state...`; `empty state does not reference For You...`; `clicking a note card calls navigate...`; all surviving search/filter tests
- `/features/5/oracle/assertions/2` → `semanticTokens.ts contains no forYou token` (deletion fence)

### Decisions (optional)
- Dropped the `trackNoteAccess` vi.mock entirely (was the only consumer); the mock was importing `../../../../services/api` which chain-imports `auth/oidcUtils.ts` → `window.sessionStorage`, causing `window is not defined` in the happy-dom environment. Removing it unblocked all other tests.
- The "no trackNoteAccess call fires" behavioral assertion is encoded structurally via the deletion fence (`NotesExplorer.test.tsx does not mock trackNoteAccess`) rather than by asserting on the API module at runtime — avoids re-introducing the problematic import chain.
- `for-you-header` absence tests are written with `queryByTestId` (not `getByTestId`) per the deletion semantics — one test per render scenario (notes exist, searching, zero notes).
- The deletion-fence test for `NotesExplorer.test.tsx` already passes (2/6 green) because the test-file changes were made first; the 4 source-file fence tests fail for the correct reason (symbols still in NotesExplorer.tsx / semanticTokens.ts).
- Mirrored `CommandPalette.f16-deletion.test.tsx` pattern exactly: `// @vitest-environment node`, `node:fs readFileSync`, one `it` per symbol, message cites the required action.

**Next hop:** implementer

## implementer

## Implementation Report: Strip forYouNotes block from NotesExplorer.tsx

**Files created/modified:**
- `ui/src/features/notes/components/NotesExplorer.tsx` (-58, +1 net; 243 → 186 lines) — removed `getBlendedForYouNotes` import, `trackNoteAccess` import, `forYouNotes` memo, `visibleNotes` memo (became dead code), `renderForYouSection` function and its render-site, and the `trackNoteAccess(noteId).catch(...)` line in `handleSelect`. Switched `useVirtualScroll` threshold to read `filteredNotes.length` (its only consumer is `renderSearchResults`, which uses `filteredNotes` for both rowCount and rowProps; the prior `visibleNotes.length` value was a code smell — the head-spliced For You items inflated the threshold count even though they were never virtualized).
- `ui/src/styles/foundations/semanticTokens.ts` (-1) — removed `'section.forYou': 'secondary.600'` line; kept `section.recent`.

**Change scope:** initial
**Changed paths:**
- `/home/dev/projects/parchmark/ui/src/features/notes/components/NotesExplorer.tsx`
- `/home/dev/projects/parchmark/ui/src/styles/foundations/semanticTokens.ts`

**`visibleNotes` removed as dead code:** YES. After the `[...forYou, ...grouped]` splice was dropped, `visibleNotes` had only one consumer: the `useVirtualScroll` threshold. That threshold is only read inside `renderSearchResults`, which itself runs only when `isSearching`. In the searching branch `visibleNotes` would have equaled `filteredNotes`, so the threshold computation is identical when read from `filteredNotes.length` directly. Result: dropping `visibleNotes` is behavior-preserving and removes a 6-line dead memo. (Pre-check Risk #2 explicitly authorized this excision.)

**trackNoteAccess scope check:** `rg 'trackNoteAccess' ui/src/` returned hits only in (a) `services/api.ts` (export + named-import re-export — F18's territory), (b) `NotesExplorer.tsx` (now removed), (c) `CommandPalette.f16-deletion.test.tsx` and `NotesExplorer.f17-deletion.test.tsx` (deletion-fence test files, which are the contract). No surviving production consumer. Confirmed safe to remove the import and call.

**Test status:** PASS — 20/20 in the two F17 test files (14 behavioral + 6 deletion-fence); full UI suite green; coverage 95.01% / 92.36% / 91.87% / 95.01% (above 90% floor); no other tests regressed.

**Commands run:**
- `rg 'forYouNotes|getBlendedForYouNotes|trackNoteAccess' ui/src/features/notes/components/NotesExplorer.tsx` → zero matches
- `rg 'forYou' ui/src/styles/foundations/semanticTokens.ts` → zero matches
- `rg 'trackNoteAccess' ui/src/` → only api.ts export + deletion-fence tests (scope check)
- `make test-ui-all` → exit 0; "All UI tests passed"
- `npx vitest run NotesExplorer.test.tsx NotesExplorer.f17-deletion.test.tsx` → 20 passed (2 files)

**Blockers:** none.

**react-window invariants (advisory check):** the surviving non-search render path in `renderDateGroups` does NOT use `react-window` virtualization (only the search path does). The For You splice was at the head of a non-virtualized list, so virtual-index shifts are a non-issue; row-height stability and `itemKey` continuity are unaffected. The search-path virtualization continues to use `filteredNotes` keyed by `note.id`, unchanged.

**Visual-QA / orphan-spacing:** the surviving render now feeds `<VStack spacing={6} align="stretch">{renderDateGroups()}</VStack>` directly. With only one child path remaining, there is no orphan wrapper, no leftover `mb`, and no surviving conditional-null branch that could collapse vertical rhythm. Halt-and-consult escalation not triggered.

### Decisions
- Removed `visibleNotes` memo as dead code (pre-check Risk #2 authorized) — its sole consumer (`useVirtualScroll`) now reads `filteredNotes.length` directly, behavior-identical because `useVirtualScroll` is only consulted on the search path.
- Kept `useCallback` on `handleSelect` per Constraint MUST; body is now a single-line `navigate(\`/notes/${noteId}\`)` — no telemetry write, no fire-and-forget.
- Did not touch `services/api.ts` `trackNoteAccess` export, `noteScoring.ts`, or `SimilarNote` types — those belong to F18 per pre-check Constraint MUST NOT.
- Did not touch test files — test-writer's authored Red state was the contract; just turned it Green.
- No CSS / spacing patches: only one render branch survives in the unsearched layout, so no orphan-spacing risk emerged; halt-and-consult escalation path was not needed.

**Next hop:** code-reviewer

## code-reviewer

### Code Review: F17 — Strip forYouNotes block from NotesExplorer.tsx

**Files reviewed:**
- `ui/src/features/notes/components/NotesExplorer.tsx`
- `ui/src/styles/foundations/semanticTokens.ts`
- `ui/src/__tests__/features/notes/components/NotesExplorer.test.tsx`
- `ui/src/__tests__/features/notes/components/NotesExplorer.f17-deletion.test.tsx`

**Neighboring files compared:**
- `ui/src/features/ui/components/CommandPalette.tsx` (post-F16, pattern twin)
- `ui/src/services/api.ts` (F18 scope, `trackNoteAccess` export confirmed intact)
- `ui/src/utils/noteScoring.ts` (untouched, confirmed)

**Findings:**

None. All eight review focus points check out:

1. **Surgical-deletion correctness:** Diff is strictly subtractive. The two removed imports, four removed memos/functions, one removed render site, and one removed token match the enumerated contract exactly. Surviving paths (date-grouped render, search render, virtualization, `handleSelect`, store wiring) are untouched.
2. **`visibleNotes` removal:** In the search branch, `visibleNotes` returned `filteredNotes` verbatim. In the non-search branch it was never read by `useVirtualScroll` (only `renderSearchResults` consults the threshold, and that runs only when `isSearching`). Switching the threshold to `filteredNotes.length` directly is behavior-identical. Removal is correct.
3. **`handleSelect` simplification:** Body is `navigate(\`/notes/${noteId}\`)` inside `useCallback([navigate])`. No telemetry, no error handling, matches the spec MUST constraint exactly.
4. **Token deletion side effects:** `section.forYou` grep returns zero hits in `ui/src/` outside deletion-fence tests and the now-cleaned `semanticTokens.ts`. `section.recent` is untouched.
5. **react-window invariants:** Non-search path is non-virtualized (`renderDateGroups` returns plain `VStack`). Search path continues to key on `note.id` and reads `filteredNotes` directly. For You splice was at head of a non-virtualized list — no virtual-index shift impact.
6. **DRY / patterns:** Post-F17 NotesExplorer mirrors post-F16 CommandPalette — `useCallback` on `handleSelect` with `navigate` only, no telemetry import, same import grouping shape.
7. **Test scope / api mock removal:** The `vi.mock('../../../../services/api')` block is cleanly removed. No surviving test asserts on any api-service call surface, so nothing is left unmocked that would have needed the mock.
8. **Pure deletion discipline:** No docstrings added, no unrelated refactoring, `section.recent` untouched, no feature flags or shims.

**Summary:** A precise surgical deletion matching the enumerated contract. All surviving paths are intact, the `visibleNotes` dead-code removal is provably behavior-equivalent, and the deletion-fence tests guard all three oracle assertions.

**Verdict:** APPROVED

## spec-reviewer

### Spec Conformance: F17 — Strip forYouNotes block from NotesExplorer.tsx

**PRD:** `docs/exec-plans/prds/remove-for-you.json`
**Feature ID:** F17 (feature index 5)
**Code:** `ui/src/features/notes/components/NotesExplorer.tsx`, `ui/src/styles/foundations/semanticTokens.ts`
**Tests:** `ui/src/__tests__/features/notes/components/NotesExplorer.test.tsx`, `ui/src/__tests__/features/notes/components/NotesExplorer.f17-deletion.test.tsx`

**Contract items:**

| Key | Status |
|-|-|
| `forYouNotes_block` removed | PASS — zero matches for `forYouNotes` in NotesExplorer.tsx |
| `getBlendedForYouNotes_import` removed | PASS — zero matches |
| `trackNoteAccess_import` removed | PASS — zero matches |
| `trackNoteAccess_call` removed | PASS — zero matches |
| `semanticTokens_section_forYou` removed | PASS — zero matches for `forYou` in `semanticTokens.ts` |

**Oracle assertions:**

| Assertion | Status |
|-|-|
| `/features/5/oracle/assertions/0` — ripgrep of NotesExplorer.tsx for all three symbols → zero | PASS — confirmed directly |
| `/features/5/oracle/assertions/1` — Vitest passes after For You assertions dropped | PASS — deletion-fence tests cover symbols; behavioral tests cover surviving render path; 20/20 passing |
| `/features/5/oracle/assertions/2` — ripgrep of `semanticTokens.ts` for `forYou` → zero | PASS — confirmed directly; `section.recent` untouched |

**MUST/MUST NOT constraints:**

- MUST delete only enumerated For You surface — PASS; `section.recent` intact, `renderDateGroups` path intact.
- MUST ripgreps return zero — PASS; verified independently above.
- MUST `handleSelect` is `useCallback` returning `navigate('/notes/${noteId}')` — PASS; confirmed at NotesExplorer.tsx (post-edit).
- MUST NOT touch `noteScoring.ts`, `services/api.ts` `trackNoteAccess` export, `SimilarNote` types, backend — PASS.
- MUST NOT add docstrings, rename `section.recent`, introduce feature flags — PASS.

**Deviations:** none.
**Coverage gaps:** none. All three oracle assertions have covering tests.

**Advisory observations (not blocking):**
- Roundtable visual-QA DoD (orphan-element absence, vertical rhythm, empty-state) and react-window invariants were noted as advisory; implementer addressed these in prose. Not independently verifiable from static analysis — landing-verifier's smoke pass closes them.

**Verdict:** CONFORMANT

## safety-auditor
<!-- Skipped per pre-check (`safety_auditor_needed: NO`). F17 is pure UI; no backend/auth/embeddings/database surface touched. -->

## arch-advisor-verification
<!-- Skipped per pre-check (`arch_advisor_needed: NO`). -->

## landing-verifier

## Landing Report: Strip forYouNotes block from NotesExplorer.tsx

**Pipeline:** frontend
**Verification:** make test-ui-all exit 0; all four coverage metrics above 90% floor (Stmts 95.01%, Branch 92.36%, Funcs 91.87%, Lines 95.01%); oracle ripgreps both returned zero matches (confirmed directly, not from upstream claims).

**Spec conformance:** CONFIRMED
**Safety audit:** NOT APPLICABLE (pre-check: safety_auditor_needed: NO — pure UI change, no backend/auth/embeddings/database surface)
**Code review:** APPROVED (## code-reviewer section contains full APPROVED report; all 8 focus points checked out)
**Architecture review:** N/A (pre-check: arch_advisor_needed: NO; arch-advisor-verification skipped per pre-check)
**Doc drift:** NONE (touched files: NotesExplorer.tsx, semanticTokens.ts, NotesExplorer.test.tsx, NotesExplorer.f17-deletion.test.tsx — none are ARCHITECTURE.md-governing surface; surgical deletion only)

**Checks run:**

| Check | Result |
|-|-|
| make test-ui-all exit code | 0 |
| Coverage Stmts | 95.01% (floor 90%) |
| Coverage Branch | 92.36% (floor 90%) |
| Coverage Funcs | 91.87% (floor 90%) |
| Coverage Lines | 95.01% (floor 90%) |
| rg forYouNotes\|getBlendedForYouNotes\|trackNoteAccess in NotesExplorer.tsx | 0 matches |
| rg forYou in semanticTokens.ts | 0 matches |
| ## code-reviewer verdict | APPROVED |
| ## spec-reviewer verdict | CONFORMANT |
| ## safety-auditor | Skipped per pre-check (correct) |
| ## arch-advisor-verification | Skipped per pre-check (correct) |
| Branch is feature branch (not main) | YES — keel/F17-strip-for-you-from-notes-explorer |
| Working tree files | 3 modified + 1 untracked (handoff) + 1 untracked (f17-deletion test) — exactly the expected 4 impl/test files |
| F17 in feature-backlog.md | PRESENT |

**Status:** VERIFIED

**Verdict:** VERIFIED

**Next hop:** orchestrator (runs roundtable review if enabled, then Step 9 post-landing procedure)

## roundtable-landing-review

### Attempt 1 — APPROVED

Three-panelist crosscheck (planner / codereviewer / generalist roles) + adversarial critique on the landed F17 diff. No CHANGES NEEDED.

#### Crosscheck

- **Planner (gemini, codex concurring):** F17 advances the remove-for-you arc cleanly. Strictly UI-tier; no scope leakage into F18 (service/types deletion), F20 (backend deps), or F21 (doc sweep). F18 is fully unblocked.
- **Codereviewer (codex):** Virtualization claim verified — `useVirtualScroll` is consumed only inside `renderSearchResults` (NotesExplorer.tsx:109); `filteredNotes.length` substitution is behavior-preserving in the only branch that consults it. One LOW: deletion-fence tests use raw substring assertions on file content; brittle to safe refactors. Recommend explicit retirement of these fence tests when F18/F21 land.
- **Generalist (claude):** Gates correct. Advisory items for downstream work: (1) F21 doc-sweep should explicitly retire access-tracking telemetry docs, not just "section removed"; (2) quick a11y grep for surviving `aria-labelledby="for-you-header"` references; (3) verify F19's migration retired `access_count` / `last_accessed_at` columns or schedule that for F18 / F20; (4) deletion-fence tests should be removed in F18 once the symbols are gone repo-wide.

#### Critique

- **Claude — APPROVE landing.** No CHANGES NEEDED. Two flagged tech-debt items: (a) `renderDateGroups` path is non-virtualized — pre-existing, not F17-introduced (search-only virtualization predates this PRD); (b) deletion-fence regex is substring-bounded (`/forYou/` would match a future `notForYou` identifier) — tighten to `\bforYou\b`. Also verified safe: `trackNoteAccess` has zero production callers in `ui/src/` (services/api.ts export + re-export only); `section.recent` still consumed by NotesExplorer + CommandPalette; empty-state path tested.
- **Codex — APPROVE.** No CHANGES NEEDED. One LOW: search-virtualization branch (`filteredNotes.length > 50`) is never exercised by the test suite (`sampleNotes` contains 5 items, threshold is 50). A future refactor could break virtualized search without CI catching. Optional: add a >50-notes search test asserting `virtual-notes-list` renders.
- **Gemini — APPROVE with caveats.** Pre-existing virtualization gap in `renderDateGroups` is now the user-visible default path (no For You splice on top); 5000 notes would render synchronously. Pre-existing, not introduced by F17, but increasingly load-bearing as the only render path. Telemetry-drop concern: zero production callers remain — verify with PM that the endpoint was For-You-exclusive vs. general analytics.

#### Verdict

APPROVED. All three panelists agree: no F17-introduced regressions. Three advisory items will be logged to `docs/exec-plans/tech-debt-tracker.md` at Step 9 sub-step 2:

- **TD-F17-1 (low):** `renderDateGroups` path lacks virtualization; pre-existing but increasingly load-bearing post-F17. Threshold: re-evaluate when avg user note count exceeds 200.
- **TD-F17-2 (low):** Deletion-fence regex in `NotesExplorer.f17-deletion.test.tsx` (and the F16 sibling) uses substring matching. Tighten to `\b...\b` and retire when F18 lands and the symbols are repo-wide gone.
- **TD-F17-3 (low):** Search-virtualization branch (`filteredNotes.length > 50`) is uncovered by tests; future refactor risk.

Status → READY-TO-LAND.
