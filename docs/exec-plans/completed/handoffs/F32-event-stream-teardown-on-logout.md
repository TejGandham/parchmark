# Event stream teardown on logout

---
status: LANDED
pipeline: frontend
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F32
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
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/104
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

**Feature ID:** F32
**Title:** Event stream teardown on logout
**Pipeline:** frontend
**Intent:** build
**Complexity:** standard
**Designer needed:** YES
**Research needed:** NO
**Safety-auditor needed:** NO
**Arch-advisor needed:** NO
**Implementer needed:** YES

Extend the frontend notes event stream so an active stream is torn down when
the auth store transitions from authenticated to unauthenticated. Teardown must
abort the active stream within 100ms and prevent any later event forwarding.

### Constraints for downstream

- MUST observe `useAuthStore` auth-state transitions.
- MUST only treat `isAuthenticated: true` to `false` as logout teardown.
- MUST abort the active stream within 100ms of that transition.
- MUST suppress all event forwarding after teardown.
- MUST preserve explicit dispose and F31 auth-refresh logout behavior.

## researcher

Not needed. The existing Zustand auth store exposes `subscribe`, and F25/F26
backend tests already verify broker unsubscribe on stream close.

### Decisions (optional)

- Use the auth store's existing subscription API instead of adding a new logout
  event bus.

## arch-advisor-consultation

Not needed. This is a narrow lifecycle change within the existing frontend
stream service.

### Constraints for downstream

None.

## backend-designer / frontend-designer

Use a shared stream teardown path for component disposal, auth-refresh logout,
and auth-store logout transitions.

### Decisions

- Add an auth-store listener inside `subscribe()` so each active stream owns its
  corresponding auth subscription.
- Call the same teardown helper for logout transitions and explicit disposal.
- Unsubscribe from auth-state changes during teardown to keep stream
  subscriptions idempotent and leak-free.
- Keep F31 `stopAndLogout()` on the same teardown path so failed refresh still
  aborts the stream and stops reconnects.

### Constraints for downstream

- Do not add another network transport or another event stream.
- Preserve retry backoff, stream-open recovery, and auth-refresh loop guard
  semantics from F29-F31.

## roundtable-design-review

Skipped: roundtable MCP tools are unavailable in this session.

## test-writer

Added F32 coverage in `ui/src/__tests__/services/notesEventStream.test.ts`.

### Decisions (optional)

- Assert a `true` to `false` auth transition aborts the active stream before the
  100ms deadline.
- Assert event messages received after logout-triggered teardown are not
  forwarded.
- Assert explicit disposal unregisters the auth-store listener.
- Reuse the existing F25/F26 backend stream tests as the broker cleanup smoke.

## implementer

Implemented logout-triggered teardown in
`ui/src/services/notesEventStream.ts`.

### Decisions

- Added `teardownStream()` to centralize timer cleanup, active fetch abort, and
  auth-listener cleanup.
- Replaced the returned inline disposer with the shared teardown helper.
- Subscribed each stream to `useAuthStore.subscribe()` and tear down only on
  `previousState.isAuthenticated && !state.isAuthenticated`.
- Updated `stopAndLogout()` to call the same teardown helper before invoking
  the auth-store logout action.

## code-reviewer

**Verdict:** APPROVED

No code-quality blockers found. The change is scoped to the existing stream
service, the teardown helper is idempotent, and the tests cover the F32 logout
transition contract plus auth-listener cleanup.

## spec-reviewer

**Verdict:** CONFORMANT

The implementation satisfies the F32 contract:

- `logout_signal`: observes `useAuthStore` auth-state changes.
- `auth_state_transition`: only tears down on authenticated to
  unauthenticated.
- `teardown_deadline_ms`: aborts synchronously, covered by a fake-timer test
  before 100ms.
- `teardown_behavior`: aborts the active stream.
- `event_forwarding_after_teardown`: `onmessage` returns without invoking
  subscribers after teardown.

Backend stream cleanup is covered by the existing smoke path in
`backend/tests/integration/notes/test_note_events_stream.py`, which verifies
the stream generator unregisters its broker subscriber when closed.

## safety-auditor

Not needed for this UI-only stream lifecycle slice.

## arch-advisor-verification

Not needed.

## landing-verifier

**Verdict:** VERIFIED WITH LOCAL DOCKER CAVEAT

Local verification passed:

- `cd ui && npm test -- --run src/__tests__/services/notesEventStream.test.ts`
- `cd ui && npm test -- --run src/__tests__/services/notesEventStream.test.ts src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npm run lint -- src/services/notesEventStream.ts src/__tests__/services/notesEventStream.test.ts src/features/notes/components/NotesLayout.tsx src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npx prettier --check src/services/notesEventStream.ts src/__tests__/services/notesEventStream.test.ts src/features/notes/components/NotesLayout.tsx src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd backend && uv run pytest tests/integration/notes/test_note_events_stream.py -q`
- `cd ui && npm run build`
- `cd ui && npm test`
- `cd ui && npm run lint`
- `python3 scripts/validate-prds.py --repo .`
- `uv run scripts/validate-prd-json.py docs/exec-plans/prds/realtime-notes-list-revalidation.json`
- `git diff --check`

`make test` ran UI lint and UI coverage successfully, then backend pytest
failed locally because Docker was not running:

- `docker version` reported `Cannot connect to the Docker daemon at
  unix:///Users/tej/.docker/run/docker.sock`.
- Backend pytest summary before exit: 405 passed, 231 errors, with the first
  error raised while testcontainers tried to call Docker `/version`.

Forgejo CI remains the required full-suite gate.

## roundtable-landing-review

Skipped: roundtable MCP tools are unavailable in this session.

## doc-gardener

doc_garden_verdict: CLEAN
drift_count: 0

No documentation drift requiring edits was found beyond the expected KEEL
handoff/backlog state updates for F32.
