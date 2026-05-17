# SSE auth-failure refresh and logout handling

---
status: LANDED
pipeline: frontend
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F31
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
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/103
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

**Feature ID:** F31
**Title:** SSE auth-failure refresh and logout handling
**Pipeline:** frontend
**Intent:** build
**Complexity:** standard
**Designer needed:** YES
**Research needed:** NO
**Safety-auditor needed:** NO
**Arch-advisor needed:** NO
**Implementer needed:** YES

Extend the notes event stream client so 401 stream-open responses use the
existing auth-store token refresh path before reconnecting. Successful refresh
must reconnect with the new bearer token and reset retry backoff. Failed refresh
must log out once and stop reconnecting.

### Constraints for downstream

- MUST handle stream-open status 401 as auth failure, not generic retry.
- MUST call `useAuthStore.getState().actions.refreshTokens()` before the next
  stream attempt.
- MUST reconnect with the current bearer token after refresh succeeds.
- MUST call `logout()` exactly once and stop reconnecting after refresh fails.
- MUST guard against an infinite refresh loop if refreshed credentials still
  receive 401.

## researcher

Not needed. Existing `api.ts` already defines the auth-store refresh/logout
semantics this stream client should reuse.

### Decisions (optional)

- Treat auth failure as a distinct stream failure type so F30 backoff retries
  and F31 refresh/logout behavior remain separate.

## arch-advisor-consultation

Not needed. This is a narrow frontend service lifecycle extension.

### Constraints for downstream

None.

## backend-designer / frontend-designer

Handle stream authentication failures as a distinct lifecycle path in the notes
event stream service, separate from F30 generic retry backoff.

### Decisions

- Represent 401 stream-open responses with an internal auth-failure error.
- On first auth failure, call the existing auth-store `refreshTokens()` action
  before any reconnect attempt.
- If refresh succeeds, reset reconnect backoff and start a fresh stream attempt
  using the current auth-store bearer token.
- If refresh fails, call the existing auth-store `logout()` action once and
  stop all reconnect scheduling.
- If refreshed credentials still receive 401 before any successful stream open,
  log out instead of refreshing repeatedly.

### Constraints for downstream

- Preserve F30 retry behavior for server close, network errors, and 5xx
  responses.
- Dispose must still abort the active stream and clear pending timers.

## roundtable-design-review

Skipped: roundtable MCP tools are unavailable in this session.

## test-writer

Added F31 auth lifecycle coverage in
`ui/src/__tests__/services/notesEventStream.test.ts`.

### Decisions (optional)

- Assert a 401 response invokes `refreshTokens()` and does not reconnect until
  refresh resolves.
- Assert successful refresh reconnects with the refreshed bearer token and
  resets the next retry delay to 1 second.
- Assert failed refresh calls `logout()` exactly once and schedules no further
  reconnects.
- Assert repeated 401 after a successful refresh does not create an infinite
  refresh loop.

## implementer

Implemented auth-failure refresh and logout handling in
`ui/src/services/notesEventStream.ts`.

### Decisions

- Added an internal `AuthFailureError` for 401 stream-open responses.
- Added `handleAuthFailure()` to call `refreshTokens()` once, reconnect on
  success, and log out on failure.
- Added a loop guard that resets only after a successful stream open.
- Added `stopAndLogout()` so logout and shutdown happen once.

## code-reviewer

**Verdict:** APPROVED

The implementation reuses existing auth-store actions, keeps auth failure
separate from generic retry backoff, and preserves existing stream behavior.
Refresh success, refresh failure, repeated 401 loop guard, and dispose/timer
cleanup are covered by focused unit tests.

## spec-reviewer

**Verdict:** CONFORMANT

The implementation satisfies the F31 contract:

- `failure_status`: 401 stream-open responses are handled specially.
- `refresh_path`: uses `useAuthStore.getState().actions.refreshTokens()`.
- `refresh_before_reconnect`: no reconnect starts until refresh resolves.
- `success_behavior`: refresh success reconnects with the current bearer token.
- `failure_behavior`: refresh failure calls `logout()` once and stops.
- `loop_guard`: repeated 401 after refresh logs out instead of refreshing
  forever.

## safety-auditor

Not needed for this UI-only stream auth lifecycle slice.

## arch-advisor-verification

Not needed.

## landing-verifier

**Verdict:** VERIFIED

Local verification passed:

- `cd ui && npm test -- --run src/__tests__/services/notesEventStream.test.ts`
- `cd ui && npm test -- --run src/__tests__/services/notesEventStream.test.ts src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npm run lint -- src/services/notesEventStream.ts src/__tests__/services/notesEventStream.test.ts src/features/notes/components/NotesLayout.tsx src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npx prettier --check src/services/notesEventStream.ts src/__tests__/services/notesEventStream.test.ts`
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
handoff/backlog state updates for F31.
