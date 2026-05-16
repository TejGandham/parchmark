# Authenticated SSE endpoint /notes/events

---
status: LANDED
pipeline: backend
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F25
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
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/96
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

**Feature ID:** F25
**Title:** Authenticated SSE endpoint /notes/events
**Pipeline:** backend
**Intent:** build
**Complexity:** standard
**Designer needed:** YES
**Research needed:** NO
**Safety-auditor needed:** YES
**Arch-advisor needed:** NO
**Implementer needed:** YES

Add an authenticated backend SSE route at `GET /api/notes/events` by registering an APIRouter route whose effective app path is `/notes/events` under the existing `/api` prefix. The route subscribes the authenticated user's id to the F24 note event broker and streams note events as SSE data frames.

### Constraints for downstream

- MUST use the existing bearer-token auth dependency; unauthenticated requests return 401 before broker subscription.
- MUST subscribe with `current_user.id` and unregister the subscriber when the stream generator closes.
- MUST serialize only `{kind, note_id}` to SSE `data:` frames; `user_id` remains server-only.
- MUST return `text/event-stream` and status 200 for authenticated streams.
- MUST keep heartbeat timing and lifecycle guarantees scoped to F26; F25 may only clean up on generator close.

## researcher

Not needed. Existing FastAPI `StreamingResponse` and auth dependency patterns are sufficient.

### Decisions (optional)

- Use existing project route/auth conventions rather than introducing a new streaming framework.

## arch-advisor-consultation

Not needed. This feature attaches a narrow HTTP route to the F24 broker service without changing architecture boundaries.

### Constraints for downstream

None.

## backend-designer / frontend-designer

Implement F25 inside the existing `app.routers.notes` APIRouter so the effective route is `GET /api/notes/events`. The endpoint returns a `StreamingResponse` with `text/event-stream` media type and delegates all fanout state to the F24 `note_event_broker`.

### Decisions

- Keep the endpoint in `backend/app/routers/notes.py` because it is note-domain HTTP surface and already mounted under `/api`.
- Register `/events` before `/{note_id}` so the static SSE route is not captured as a note id.
- Add a route-local bearer dependency that still calls the existing `get_current_user` logic but returns 401 for missing credentials, matching F25's explicit unauthorized contract.
- Put broker subscription inside the stream generator so a client that disconnects before body iteration does not leak a subscriber.
- Stream SSE `data:` frames containing only `kind` and `note_id`.

### Constraints for downstream

- Do not expose `user_id` in the wire payload.
- Do not add heartbeat behavior; F26 owns idle heartbeat timing.
- Do not create a second broker or listener; use F24's process-local broker.

## roundtable-design-review

Skipped: roundtable MCP tools are unavailable in this session.

## test-writer

Added route-level integration coverage in `backend/tests/integration/notes/test_note_events_stream.py`.

The tests mount the real notes router in a small FastAPI app, patch the auth/broker boundaries, and verify:
- authenticated requests return `text/event-stream`;
- the broker subscribes with the authenticated user id;
- the SSE data frame contains only `kind` and `note_id`;
- the stream generator unregisters the subscriber on close;
- missing and invalid credentials return 401 without subscribing.

Also updated the F24 service test to exercise string note IDs from the actual F23 trigger payload shape.

### Decisions (optional)

- Use a finite fake broker queue in tests so Starlette's synchronous TestClient can consume the streaming response without hanging on an infinite stream.

## implementer

Implemented F25 in `backend/app/routers/notes.py`:
- added `GET /api/notes/events`;
- added a note-event auth dependency that maps missing bearer credentials to 401 and delegates token validation to existing auth;
- added an SSE generator that subscribes by `current_user.id`, emits `data: {"kind": ..., "note_id": ...}\n\n`, and unregisters in `finally`.

Adjusted `backend/app/services/note_events.py` so `NoteEvent.note_id` accepts `int | str`; F23 emits string note ids from the `notes.id` column, so F24's previous int-only normalization would have dropped real trigger payloads.

### Decisions

- Kept SSE serialization as plain JSON in the `data:` field with no event name because F25's wire contract only names payload fields.
- Added `Cache-Control: no-cache` and `X-Accel-Buffering: no` headers for streaming friendliness without changing the contract.

## code-reviewer

**Verdict:** APPROVED

No code-quality blockers found. The route is scoped to the existing notes router, static route ordering is correct, subscription cleanup is in a `finally` block, and the broker remains the single F24 fanout mechanism.

## spec-reviewer

**Verdict:** CONFORMANT

F25 contract conformance:
- `route`, `method`, `success_status`, and `content_type`: implemented by `GET /api/notes/events` returning `StreamingResponse` with `text/event-stream`.
- `auth_scheme` and `unauthorized_status`: bearer auth is required; missing or invalid credentials return 401 in F25 tests.
- `subscriber_key`: broker subscription uses `current_user.id`.
- `wire_payload_fields` and `server_only_fields`: SSE frames include only `kind` and `note_id`; `user_id` is used only for broker routing.
- `disconnect_cleanup`: generator `finally` unregisters the subscriber.

The implementation also preserves F26 scope by not adding heartbeat behavior.

## safety-auditor

**Verdict:** PASS

Safety review:
- Auth required on route: PASS. The endpoint does not subscribe until bearer auth resolves a user.
- User isolation: PASS. Subscription key is the authenticated user's id; clients cannot choose the routing key.
- Data exposure: PASS. `user_id` is not serialized into SSE frames.
- Resource cleanup: PASS for F25 scope. The stream generator unregisters the subscriber when it closes.

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
- `cd backend && uv run pytest tests/unit/services/test_note_events.py tests/unit/app/test_note_events_lifespan.py tests/integration/notes/test_note_events_stream.py -q` — passed, 18 tests.
- `cd backend && uv run pytest tests/integration/test_main.py::TestApplicationLifespan::test_lifespan_startup tests/integration/test_app_boot_no_openai.py::test_app_boots_without_openai_api_key -q` — passed, 2 tests.

Full Docker-backed backend coverage is deferred to Forgejo CI because this local session has no Docker socket.

## roundtable-landing-review

Skipped: roundtable MCP tools are unavailable in this session.

## doc-gardener

doc_garden_verdict: CLEAN
drift_count: 0

Backlog status updated for F25. No tech-debt entries were added; no resolved tech-debt items found in this feature's scope.
