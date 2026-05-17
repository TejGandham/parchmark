# Initial-connect and reconnect reconciliation

---
status: LANDED
pipeline: frontend
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F29
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
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/101
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

**Feature ID:** F29
**Title:** Initial-connect and reconnect reconciliation
**Pipeline:** frontend
**Intent:** build
**Complexity:** standard
**Designer needed:** YES
**Research needed:** NO
**Safety-auditor needed:** NO
**Arch-advisor needed:** NO
**Implementer needed:** YES

Add a stream-open recovery callback for the notes event stream and wire the
notes layout to force React Router loader revalidation on the initial SSE open
and every later reopen. This protects against missed events during connection
gaps without adding polling.

### Constraints for downstream

- MUST force `router.revalidate()` on initial stream open.
- MUST force `router.revalidate()` on every reconnect open.
- MUST keep received-event revalidation from F28 intact.
- MUST use the existing notes event stream transport.
- MUST NOT add polling, intervals, or optimistic cache patching.

## researcher

Not needed. The local `@microsoft/fetch-event-source` types expose an `onopen`
transport hook, and existing F27/F28 handoffs define the relevant boundaries.

### Decisions (optional)

- Preserve the existing `subscribe(callback)` shape by adding optional lifecycle
  options instead of replacing the callback API.

## arch-advisor-consultation

Not needed. This is a narrow frontend lifecycle extension.

### Constraints for downstream

None.

## backend-designer / frontend-designer

Extend the existing notes event stream service with an optional stream-open
lifecycle hook, then wire `NotesLayout` to use that hook for recovery
revalidation.

### Decisions

- Add optional `NoteEventStreamOptions` to `subscribe(callback, options)` so
  F27's public callback API remains backward-compatible.
- Use `fetch-event-source`'s `onopen` hook as the single source for initial
  connect and reconnect-open notification.
- Preserve the transport's event-stream content-type validation when providing
  a custom `onopen` callback.
- Reuse one `revalidateNotes` callback in `NotesLayout` for both received note
  events and stream-open reconciliation.

### Constraints for downstream

- Do not introduce a separate transport or polling recovery path.
- Do not change the `notes-layout` route id or loader contract.

## roundtable-design-review

Skipped: roundtable MCP tools are unavailable in this session.

## test-writer

Added focused F29 regression coverage in the stream service and layout tests.

### Decisions (optional)

- `notesEventStream.test.ts` now drives the transport `onopen` hook twice and
  asserts the lifecycle callback fires twice, covering initial open and reopen.
- `NotesLayout.test.tsx` captures the stream options passed by the layout and
  asserts initial open and repeated reconnect-open each call the router
  revalidator.
- Existing F28 received-event revalidation and disposer tests remain in place.

## implementer

Implemented initial-connect and reconnect reconciliation.

### Decisions

- `ui/src/services/notesEventStream.ts` now accepts optional
  `NoteEventStreamOptions` with `onOpen`, validates `text/event-stream`, and
  calls `onOpen` once for each transport open while the subscription is active.
- `ui/src/features/notes/components/NotesLayout.tsx` passes the router
  revalidator as both the received-event callback and the stream-open recovery
  callback.

## code-reviewer

**Verdict:** APPROVED

The change keeps the lifecycle concern at the stream boundary and reuses the
existing layout subscription. Backward compatibility is preserved for existing
`subscribe(callback)` callers, default event-stream validation is retained, and
no polling or cache-patching behavior was introduced.

## spec-reviewer

**Verdict:** CONFORMANT

The implementation satisfies the F29 contract:

- `revalidate_on_initial_open`: `NotesLayout` passes `revalidateNotes` through
  `onOpen`.
- `revalidate_on_reconnect_open`: every transport `onopen` invocation calls the
  same lifecycle callback.
- `missed_event_recovery`: stream reopen forces route loader revalidation.
- `applies_to_transport`: implemented in the notes event stream service used by
  the notes route layout.

Vitest covers initial open, repeated reopen, and the existing received-event
path. The browser smoke portion was not run locally because it requires the full
authenticated dev stack.

## safety-auditor

Not needed for this UI-only stream lifecycle slice.

## arch-advisor-verification

Not needed.

## landing-verifier

**Verdict:** VERIFIED

Local verification passed:

- `cd ui && npm test -- --run src/__tests__/services/notesEventStream.test.ts src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npm run lint -- src/services/notesEventStream.ts src/features/notes/components/NotesLayout.tsx src/__tests__/services/notesEventStream.test.ts src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npx prettier --check src/services/notesEventStream.ts src/features/notes/components/NotesLayout.tsx src/__tests__/services/notesEventStream.test.ts src/__tests__/features/notes/components/NotesLayout.test.tsx`
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
handoff/backlog state updates for F29.
