# End-to-end cross-user isolation safety test

---
status: LANDED
pipeline: cross-cutting
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F33
intent: build
complexity: standard
designer_needed: NO
researcher_needed: NO
safety_auditor_needed: YES
arch_advisor_needed: NO
implementer_needed: YES
spec_review_verdict: CONFORMANT
spec_review_attempt: 1
safety_verdict: PASS
safety_attempt: 1
code_review_verdict: APPROVED
code_review_attempt: 1
arch_advisor_verdict:
arch_retry_spec_review_attempt: 0
arch_retry_safety_attempt: 0
remote_name: origin
roundtable_enabled: true
roundtable_precheck_skipped: true
roundtable_precheck_skip_reason: roundtable MCP tools unavailable in this session
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/105
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

**Feature ID:** F33
**Title:** End-to-end cross-user isolation safety test
**Pipeline:** cross-cutting
**Intent:** build
**Complexity:** standard
**Designer needed:** NO
**Research needed:** NO
**Safety-auditor needed:** YES
**Arch-advisor needed:** NO
**Implementer needed:** YES

Add a CI-gated backend integration test that proves note-event SSE fanout does
not leak another user's note events. The test must register user B's stream
before assertions, perform ten real HTTP note mutations as user A, observe zero
user A events on user B's stream for five seconds, then prove the stream is
alive with one user B control mutation.

### Constraints for downstream

- MUST exercise the `/api/notes/events` transport, not only the stream
  generator helper.
- MUST use two authenticated users.
- MUST use real HTTP note mutation calls for user A and user B.
- MUST verify user B's broker subscription exists before isolation assertions.
- MUST keep the test in the backend pytest suite so CI gates it.

## researcher

Not needed. Existing F23-F26 tests provided the trigger, broker, listener, and
stream lifecycle patterns.

### Decisions (optional)

- Use a dedicated Postgres testcontainer because the standard backend `client`
  fixture creates tables directly and does not install the F23 NOTIFY trigger.

## arch-advisor-consultation

Not needed. This is a test-only integration slice.

### Constraints for downstream

None.

## backend-designer / frontend-designer

Not applicable. F33 is a cross-cutting test-gate feature.

### Decisions

None.

### Constraints for downstream

None.

## roundtable-design-review

Skipped: roundtable MCP tools are unavailable in this session.

## test-writer

Added `backend/tests/integration/notes/test_cross_user_event_stream_isolation.py`.

### Decisions (optional)

- Build a small FastAPI app around the real notes router and dependency-override
  it to a dedicated upgraded Postgres testcontainer.
- Install the F23 trigger by materializing the current schema, stamping at
  `7f1c343772e8`, and upgrading to head.
- Start a real `PostgresNoteEventListener` in app lifespan so HTTP mutations
  flow through Postgres NOTIFY, the per-worker listener, the broker, and the
  SSE route.
- Use `httpx.AsyncClient.stream()` against a local Uvicorn server so the test
  exercises the actual `/api/notes/events` transport.

## implementer

Implemented the F33 isolation test.

### Decisions

- Added a five-second leak window that checks user B receives zero data events
  after ten interleaved user A POST/PATCH/DELETE note mutations.
- Added a user B control POST and asserted user B's stream receives exactly the
  matching `{kind: "created", note_id}` payload.
- Added explicit stream-registration polling through `NoteEventBroker` before
  mutation assertions begin.
- Kept all helper state isolated to the test module and restored patched
  note-event services after the server exits.

## code-reviewer

**Verdict:** APPROVED

No code-quality blockers found. The test keeps the e2e harness isolated to the
F33 module, uses the existing router/listener/broker components, and avoids
weakening production code to make the test pass.

## spec-reviewer

**Verdict:** CONFORMANT

The implementation satisfies the F33 contract:

- `test_type`: backend integration/e2e pytest.
- `transport`: streams from `/api/notes/events`.
- `actors`: creates authenticated user A and user B.
- `user_b_stream_registration_required`: polls broker subscriber count before
  mutation assertions.
- `user_a_mutation_count`: performs ten user A HTTP mutations.
- `mutations`: covers POST, PATCH, and DELETE note calls.
- `leak_window_seconds`: observes user B's stream for five seconds.
- `negative_assertion`: asserts zero user A events reach user B.
- `control_assertion`: asserts one user B event reaches user B.
- `ci_gating`: the test is in the backend pytest suite.

## safety-auditor

**Verdict:** PASS

The test directly protects tenant isolation on the SSE transport by asserting
that authenticated user B never receives user A note events while also proving
the stream is live. No production authorization or routing code changed.

## arch-advisor-verification

Not needed.

## landing-verifier

**Verdict:** VERIFIED WITH LOCAL DOCKER CAVEAT

Local verification passed:

- `cd backend && uv run ruff format --check tests/integration/notes/test_cross_user_event_stream_isolation.py`
- `cd backend && uv run ruff check tests/integration/notes/test_cross_user_event_stream_isolation.py`
- `cd backend && uv run python -m py_compile tests/integration/notes/test_cross_user_event_stream_isolation.py`
- `cd backend && uv run ruff check app tests`
- `cd backend && uv run ruff format --check app tests`
- `cd backend && uv run pytest tests/integration/notes/test_note_events_stream.py -q`
- `python3 scripts/validate-prds.py --repo .`
- `uv run scripts/validate-prd-json.py docs/exec-plans/prds/realtime-notes-list-revalidation.json`
- `git diff --check`

The F33 e2e test could not run locally because Docker is unavailable:

- `docker version` reported `Cannot connect to the Docker daemon at
  unix:///Users/tej/.docker/run/docker.sock`.
- `cd backend && uv run pytest tests/integration/notes/test_cross_user_event_stream_isolation.py -q`
  failed at testcontainer setup while Docker SDK attempted `GET /version`.

Forgejo CI remains the required full-suite gate and is expected to run the
Postgres testcontainer path.

## roundtable-landing-review

Skipped: roundtable MCP tools are unavailable in this session.

## doc-gardener

doc_garden_verdict: CLEAN
drift_count: 0

No documentation drift requiring edits was found beyond the expected KEEL
handoff/backlog state updates for F33.
