# Notes loader revalidation on received events

---
status: LANDED
pipeline: frontend
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F28
intent: build
complexity: standard
designer_needed: YES
researcher_needed: NO
safety_auditor_needed: NO
arch_advisor_needed: NO
implementer_needed: YES
spec_review_verdict: CONFORMANT
spec_review_attempt: 1
safety_verdict:
safety_attempt: 0
code_review_verdict: APPROVED
code_review_attempt: 1
arch_advisor_verdict:
arch_retry_spec_review_attempt: 0
arch_retry_safety_attempt: 0
remote_name: origin
roundtable_enabled: true
roundtable_precheck_skipped: true
roundtable_precheck_skip_reason: roundtable MCP tools unavailable in this session
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/100
roundtable_design_attempt: 0
roundtable_design_verdict:
roundtable_skipped: true
roundtable_skip_reason: roundtable MCP tools unavailable in this session
roundtable_landing_attempt: 0
roundtable_landing_verdict:
roundtable_retry_code_review_attempt: 0
roundtable_retry_spec_review_attempt: 0
roundtable_retry_safety_attempt: 0
doc_garden_verdict: CLEAN
doc_garden_drift_count: 0
---

## pre-check

**Feature ID:** F28
**Title:** Notes loader revalidation on received events
**Pipeline:** frontend
**Intent:** build
**Complexity:** standard
**Designer needed:** YES
**Research needed:** NO
**Safety-auditor needed:** NO
**Arch-advisor needed:** NO
**Implementer needed:** YES

Attach the F27 frontend notes event stream subscriber at the notes layout scope. Each received note event should call the React Router `router.revalidate()` method exactly once. The implementation must not add polling.

### Constraints for downstream

- MUST mount the subscription from the notes layout scope.
- MUST call `router.revalidate()` exactly once per received SSE event.
- MUST use the F27 `notesEventStream` public API instead of opening another stream implementation.
- MUST NOT add interval polling or repeated `/api/notes` fetches while idle.
- SHOULD preserve existing route loader id `notes-layout`.

## researcher

Not needed. Existing React Router, notes route, and F27 stream module patterns are sufficient.

### Decisions (optional)

- Use Vitest/mocks for the deterministic revalidation contract.

## arch-advisor-consultation

Not needed. This feature wires an existing client service into an existing route layout.

### Constraints for downstream

None.

## backend-designer / frontend-designer

Mount the event stream subscription in `NotesLayout`, which is the existing
route layout for loader id `notes-layout`.

### Decisions

- Use React Router's `useRevalidator()` hook from the layout component and
  invoke its `revalidate` callback once for each F27 stream callback.
- Use `services/notesEventStream.subscribe` directly so this feature depends on
  the public F27 API and does not create another SSE transport path.
- Return the subscription disposer from the layout effect so unmounting the
  route tears down this subscriber.

### Constraints for downstream

- Do not add timers, intervals, or polling fetches.
- Keep the existing `notes-layout` route id untouched.

## roundtable-design-review

Skipped: roundtable MCP tools are unavailable in this session.

## test-writer

Added route-scope unit coverage in
`ui/src/__tests__/features/notes/components/NotesLayout.test.tsx`.

### Decisions (optional)

- Mock `notesEventStream.subscribe` and capture its callback so the test can
  inject deterministic note events without a live SSE connection.
- Assert three injected received events call the mocked revalidator exactly
  three times.
- Assert unmount calls the returned stream disposer once.

## implementer

Implemented the F28 wiring in `NotesLayout`.

### Decisions

- `ui/src/features/notes/components/NotesLayout.tsx` now subscribes to the F27
  notes event stream at layout mount and calls `revalidate()` for each received
  event.
- The effect cleanup returns the F27 disposer, preserving route unmount cleanup.
- No polling or repeated idle `/api/notes` fetch path was introduced.

## code-reviewer

**Verdict:** APPROVED

The change is narrowly scoped to the notes layout and its component test. It
uses the F27 public API, preserves the existing route loader id, and cleans up
the subscription on unmount. No DRY, lifecycle, or architecture issues found.

## spec-reviewer

**Verdict:** CONFORMANT

The implementation satisfies the F28 contract:

- `mount_scope`: `NotesLayout`
- `event_handler`: React Router revalidator callback
- `revalidation_frequency`: one call per received stream callback
- `router_loader_id`: existing `notes-layout` route id remains unchanged
- `idle_polling`: no timers, intervals, or polling requests added

The deterministic Vitest route test covers the three-event revalidation oracle
and disposer cleanup. The browser smoke portion was not run locally because it
requires the full dev stack with authenticated clients.

## safety-auditor

Not needed for this UI-only wiring slice.

## arch-advisor-verification

Not needed.

## landing-verifier

**Verdict:** VERIFIED

Local verification passed:

- `cd ui && npm test -- --run src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npm test -- --run src/__tests__/features/notes/components/NotesLayout.test.tsx src/__tests__/services/notesEventStream.test.ts`
- `cd ui && npm run lint -- src/features/notes/components/NotesLayout.tsx src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npx prettier --check src/features/notes/components/NotesLayout.tsx src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npm run build`
- `cd ui && npm test`
- `cd ui && npm run lint`
- `python3 scripts/validate-prds.py --repo .`
- `uv run scripts/validate-prd-json.py docs/exec-plans/prds/realtime-notes-list-revalidation.json`
- `git diff --check`

## roundtable-landing-review

Skipped: roundtable MCP tools are unavailable in this session.

## doc-gardener

doc_garden_verdict: CLEAN
drift_count: 0

No documentation drift requiring edits was found beyond the expected KEEL
handoff/backlog state updates for F28.
