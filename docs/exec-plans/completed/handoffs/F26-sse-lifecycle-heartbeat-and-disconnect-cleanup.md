# SSE lifecycle heartbeat and disconnect cleanup

---
status: LANDED
pipeline: backend
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F26
intent: build
complexity: standard
designer_needed: YES
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
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/97
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

**Feature ID:** F26
**Title:** SSE lifecycle heartbeat and disconnect cleanup
**Pipeline:** backend
**Intent:** build
**Complexity:** standard
**Designer needed:** YES
**Research needed:** NO
**Safety-auditor needed:** YES
**Arch-advisor needed:** NO
**Implementer needed:** YES

Extend the authenticated note-events SSE stream from F25 with lifecycle behavior: idle streams emit `:heartbeat\n\n` every 30 seconds, client disconnect removes the broker subscriber within one heartbeat interval, and FastAPI shutdown closes active streams before the F24 LISTEN connection is stopped.

### Constraints for downstream

- MUST preserve F25 auth and wire payload behavior.
- MUST emit exactly `:heartbeat\n\n` after 30 idle seconds.
- MUST unregister the subscriber when the request disconnects or the generator closes.
- MUST coordinate lifespan shutdown with active streams before stopping the note-event listener.
- MUST keep note event routing keyed only by authenticated user id.

## researcher

Not needed. Existing FastAPI `Request.is_disconnected`, `StreamingResponse`, and lifespan hooks cover the required behavior.

### Decisions (optional)

- Use bounded timers in tests rather than sleeping 30 seconds.

## arch-advisor-consultation

Not needed. F26 extends the existing F25 route lifecycle without changing service boundaries.

### Constraints for downstream

None.

## backend-designer / frontend-designer

Extend the F25 stream generator rather than adding another endpoint. The stream loop should wait for either a broker event, app shutdown, or a heartbeat timeout. On timeout it emits the exact comment frame from the contract. On shutdown or request disconnect it exits and runs the existing unsubscribe cleanup.

### Decisions

- Add a small `NoteEventStreamManager` service to track active subscribers and signal app shutdown to all loops.
- Call `note_event_stream_manager.open()` during FastAPI startup so repeated TestClient lifespans reset the closing flag.
- Call `await note_event_stream_manager.close_all()` during shutdown before stopping the F24 LISTEN listener.
- Keep `Request.is_disconnected()` in the router-level generator because disconnect detection is HTTP-specific.
- Cancel pending queue/shutdown wait tasks in a `finally` block to avoid pending-task warnings when a stream is closed.

### Constraints for downstream

- Preserve F25 auth and `{kind, note_id}` wire payload behavior.
- Heartbeat frame must be exactly `:heartbeat\n\n`.
- Tests must use bounded heartbeat intervals; no 30-second sleeps.

## roundtable-design-review

Skipped: roundtable MCP tools are unavailable in this session.

## test-writer

Added F26 coverage in `backend/tests/integration/notes/test_note_events_stream.py` and expanded lifespan coverage in `backend/tests/unit/app/test_note_events_lifespan.py`.

The tests verify:
- idle streams emit `:heartbeat\n\n` using a bounded heartbeat interval;
- disconnected streams unregister their broker subscriber;
- app shutdown wakes an idle stream immediately instead of waiting for the 30-second heartbeat interval;
- lifespan shutdown calls stream close before stopping the LISTEN listener.

### Decisions (optional)

- Direct generator tests are used for lifecycle timing to avoid slow or flaky network sleeps.

## implementer

Implemented F26:
- added `backend/app/services/note_event_streams.py` with heartbeat constants and `NoteEventStreamManager`;
- updated `_note_events_sse_stream` to race broker events against shutdown and heartbeat timeout;
- added request disconnect checks before and after each idle wait;
- wired FastAPI lifespan shutdown to close streams before stopping the note-event listener.

### Decisions

- Use `asyncio.wait(..., timeout=heartbeat_interval_seconds)` so tests can pass a short interval while production defaults to 30 seconds.
- Keep shutdown signaling separate from broker unsubscribe so future SSE features can still use the same broker semantics.

## code-reviewer

**Verdict:** APPROVED

No code-quality blockers found. The lifecycle manager is small, avoids router-global ad hoc sets, and the stream loop cancels pending tasks in all normal timeout/event paths.

## spec-reviewer

**Verdict:** CONFORMANT

F26 contract conformance:
- `heartbeat_interval_seconds: 30` and `heartbeat_frame: ":heartbeat\n\n"` are implemented via service constants.
- Idle streams emit the heartbeat frame after the bounded interval; tests verify with a shortened interval.
- Client disconnect cleanup unregisters the subscriber.
- FastAPI shutdown closes active streams before stopping the LISTEN listener.
- F25 authentication and wire payload behavior remain unchanged.

## safety-auditor

**Verdict:** PASS

Safety review:
- Auth remains required before subscription.
- Subscriber routing still uses only the authenticated user id.
- No server-only `user_id` data is exposed on the SSE wire.
- Shutdown now actively closes streams before listener disposal, reducing pending-task/resource-leak risk.

## arch-advisor-verification

Not needed.

## landing-verifier

**Verdict:** VERIFIED

Local verification:
- `python3 scripts/validate-prds.py --repo .` — passed.
- `uv run scripts/validate-prd-json.py docs/exec-plans/prds/realtime-notes-list-revalidation.json` — passed.
- `cd backend && uv run ruff check .` — passed.
- `cd backend && uv run ruff format --check .` — passed.
- `cd backend && uv run mypy app` — passed.
- `cd backend && uv run pytest tests/unit/services/test_note_events.py tests/unit/app/test_note_events_lifespan.py tests/integration/notes/test_note_events_stream.py -q` — passed, 21 tests.
- `cd backend && uv run pytest tests/integration/test_main.py::TestApplicationLifespan::test_lifespan_startup tests/integration/test_app_boot_no_openai.py::test_app_boots_without_openai_api_key -q` — passed, 2 tests.

Full Docker-backed backend coverage is deferred to Forgejo CI because this local session has no Docker socket.

## roundtable-landing-review

Skipped: roundtable MCP tools are unavailable in this session.

## doc-gardener

doc_garden_verdict: CLEAN
drift_count: 0

Backlog status updated for F26. No tech-debt entries were added; no resolved tech-debt items found in this feature's scope.
