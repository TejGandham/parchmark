# SSE auto-reconnect with exponential backoff

---
status: LANDED
pipeline: frontend
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F30
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
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/102
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

**Feature ID:** F30
**Title:** SSE auto-reconnect with exponential backoff
**Pipeline:** frontend
**Intent:** build
**Complexity:** standard
**Designer needed:** YES
**Research needed:** NO
**Safety-auditor needed:** NO
**Arch-advisor needed:** NO
**Implementer needed:** YES

Add explicit reconnect scheduling to the notes event stream client for server
close, network failure, and retryable 5xx stream-open responses. Retry delays
must follow 1s, 2s, 4s, 8s, 16s, then cap at 30s, and reset to 1s only after
an open stream remains stable for 30 seconds.

### Constraints for downstream

- MUST reconnect after server close.
- MUST reconnect after network error.
- MUST reconnect after non-401 5xx stream-open responses.
- MUST use 1s initial delay, x2 multiplier, and 30s cap.
- MUST reset backoff only after 30s of stable open stream time.

## researcher

Not needed. The local `fetch-event-source` implementation supports `onopen` and
`onerror`; F30 can own retries by rejecting transport failures and scheduling
the next `fetchEventSource` call directly.

### Decisions (optional)

- Prefer explicit service-owned timers over the library's default retry loop so
  server-close recovery and fake-timer tests share one deterministic path.

## arch-advisor-consultation

Not needed. This is a narrow frontend service lifecycle extension.

### Constraints for downstream

None.

## backend-designer / frontend-designer

Move retry ownership into the notes event stream service so all retryable
failures share one deterministic scheduler.

### Decisions

- Wrap each `fetchEventSource` attempt in service-owned reconnect scheduling
  instead of relying on the transport library's internal retry loop.
- Treat stream close, rejected transport attempts, and 5xx stream-open
  responses as retryable failures.
- Use a single backoff cursor with delays 1s, 2s, 4s, 8s, 16s, then 30s.
- Reset the cursor to 1s only after a stream remains open for 30 seconds.
- Preserve F27 token/header behavior and F29 `onOpen` recovery callbacks.

### Constraints for downstream

- Do not add route-level polling or loader timers.
- Dispose must abort the active stream and clear reconnect/stability timers.

## roundtable-design-review

Skipped: roundtable MCP tools are unavailable in this session.

## test-writer

Added fake-timer coverage to `ui/src/__tests__/services/notesEventStream.test.ts`.

### Decisions (optional)

- Assert server-close reconnect attempts occur at cumulative 1s, 3s, 7s, 15s,
  31s, and 61s.
- Assert repeated network failures cap the retry delay at 30s.
- Assert 503 stream-open responses schedule reconnect.
- Assert a stream open for 30 seconds resets the next reconnect delay to 1s.
- Keep F27/F29 service and layout tests green.

## implementer

Implemented service-owned SSE reconnect backoff in
`ui/src/services/notesEventStream.ts`.

### Decisions

- Each stream attempt gets a fresh `AbortController` and fresh auth headers.
- `onerror` rejects out of `fetch-event-source` so the service scheduler owns
  all retry timing.
- `scheduleReconnect` clears any pending stability reset before taking the next
  delay.
- `markStreamOpen` schedules the 30s stability reset and still invokes the F29
  `onOpen` callback.

## code-reviewer

**Verdict:** APPROVED

The change is contained to the stream service and its contract tests. The
backoff path is deterministic, dispose clears active timers and aborts the
current stream, and existing bearer header, message parsing, stream-open, and
layout revalidation behavior remains covered.

## spec-reviewer

**Verdict:** CONFORMANT

The implementation satisfies the F30 contract:

- `server_close`: resolved stream attempts schedule reconnect.
- `network_error`: rejected transport attempts schedule reconnect.
- `non_401_5xx_response`: 5xx responses during stream open are retryable.
- `initial_delay_seconds`: first retry delay is 1s.
- `multiplier`: delay doubles through 2s, 4s, 8s, and 16s.
- `max_delay_seconds`: delay caps at 30s.
- `reset_after_stable_seconds`: 30s of open stream time resets delay to 1s.

Vitest fake-timer coverage exercises the timing oracle directly.

## safety-auditor

Not needed for this UI-only stream lifecycle slice.

## arch-advisor-verification

Not needed.

## landing-verifier

**Verdict:** VERIFIED

Local verification passed:

- `cd ui && npm test -- --run src/__tests__/services/notesEventStream.test.ts`
- `cd ui && npm test -- --run src/__tests__/services/notesEventStream.test.ts src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npm run lint -- src/services/notesEventStream.ts src/__tests__/services/notesEventStream.test.ts src/features/notes/components/NotesLayout.tsx src/__tests__/features/notes/components/NotesLayout.test.tsx`
- `cd ui && npx prettier --check src/services/notesEventStream.ts src/__tests__/services/notesEventStream.test.ts src/features/notes/components/NotesLayout.tsx src/__tests__/features/notes/components/NotesLayout.test.tsx`
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
handoff/backlog state updates for F30.
