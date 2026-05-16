# Per-worker LISTEN consumer plus per-user broker fanout

---
status: LANDED
pipeline: backend
spec_ref:
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F24
parent_sha:

intent: build
complexity: architecture-tier
designer_needed: YES
researcher_needed: YES
safety_auditor_needed: YES
arch_advisor_needed: YES
implementer_needed: YES

spec_review_verdict: CONFORMANT
spec_review_attempt: 1
safety_verdict: PASS
safety_attempt: 1
code_review_verdict: APPROVED
code_review_attempt: 1
arch_advisor_verdict: SOUND

arch_retry_spec_review_attempt: 0
arch_retry_safety_attempt: 0

remote_name: origin
roundtable_enabled: false
roundtable_precheck_skipped: true
roundtable_precheck_skip_reason: Roundtable MCP tools are unavailable in this Codex session.
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/95
doc_garden_verdict: CLEAN
doc_garden_drift_count: 0

roundtable_design_attempt: 0
roundtable_design_verdict:
roundtable_skipped: true
roundtable_skip_reason: Roundtable MCP tools are unavailable in this Codex session.

roundtable_landing_attempt: 0
roundtable_landing_verdict:

roundtable_retry_code_review_attempt: 0
roundtable_retry_spec_review_attempt: 0
roundtable_retry_safety_attempt: 0
---

## pre-check
## Execution Brief: Per-worker LISTEN consumer plus per-user broker fanout

**PRD:** /Users/tej/src/parchmark/docs/exec-plans/prds/realtime-notes-list-revalidation.json
**Feature ID:** F24
**Feature index:** 1
**Feature pointer base:** /features/1
**Layer:** service
**PRD-level invariants:** none
**Prototype mode:** none
**Dependencies:** MET - F23 is landed on `origin/main` via `docs/exec-plans/completed/handoffs/F23-postgres-trigger-notify.md`; backlog bookkeeping is now checked.
**Research needed:** YES - confirm the installed `asyncpg` notification listener API and callback behavior for `LISTEN`/`NOTIFY`.
**Designer needed:** YES (new backend service lifecycle and concurrency boundary)
**Implementer needed:** YES
**Safety auditor needed:** YES (touches app lifecycle and database notification flow)
**Arch-advisor needed:** YES (architecture-tier stateful per-worker background service)

**Intent:** build
**Complexity:** architecture-tier

**What to build:**
Add an in-process note event broker and one FastAPI-lifespan-managed Postgres LISTEN consumer per worker. The listener subscribes to `notes_events`, decodes F23 payloads, and fans them out only to subscribers registered for the matching `user_id`.

**New files:**
- `backend/app/services/note_events.py` - broker, subscriber queue model, listener lifecycle.
- `backend/tests/unit/services/test_note_events.py` - broker fanout and slow-consumer behavior.
- `backend/tests/integration/test_note_events_listener.py` - Postgres LISTEN/NOTIFY listener integration coverage.

**Modified files:**
- `backend/app/main.py` - start and stop the per-worker note-events listener in lifespan.
- `docs/exec-plans/active/feature-backlog.md` - mark landed F23 dependency as complete.

**Existing patterns to follow:**
- `backend/app/main.py:lifespan` - startup/shutdown wiring and fail-fast startup behavior.
- `backend/app/database/database.py` - existing async PostgreSQL URL construction and app-level engine lifecycle.
- `backend/tests/conftest.py` - testcontainers PostgreSQL fixture pattern.
- `backend/tests/integration/migrations/test_f23_notes_notify_trigger.py` - existing `notes_events` notification payload expectations.

**Assertion traceability:**
- `/features/1/oracle/assertions/0` -> instantiate lifespan with patched listener factory and assert exactly one listener start per app lifespan.
- `/features/1/oracle/assertions/1` -> broker subscribers for two users receive only matching payloads.
- `/features/1/oracle/assertions/2` -> saturated subscriber queue is disconnected while other subscribers still receive payloads.
- `/features/1/oracle/assertions/3` -> two listener/broker instances receive the same Postgres notification from `notes_events`.

**Edge cases:**
- Invalid notification payloads must not crash the listener loop.
- A disconnected or saturated subscriber must be removed from future fanout.
- Shutdown must cancel the listener task and close the dedicated LISTEN connection.
- Multiple subscribers for the same user are independent subscribers.

**Risks:**
- Blocking fanout on one slow subscriber could starve unrelated users.
- Leaking listener tasks or LISTEN connections during shutdown would make tests and worker restarts flaky.
- Import-time global state could interfere with pytest app reuse; lifecycle state should be explicit and resettable.

**Verify command:** `make test-backend-all`

**Path convention:** Backend source under `backend/app/`; backend tests under `backend/tests/unit/` and `backend/tests/integration/`.

### Constraints for downstream
- MUST: keep the LISTEN connection dedicated and managed by FastAPI lifespan, not per request.
- MUST: enforce queue limit 50 by default and disconnect saturated subscribers without blocking other subscribers.
- MUST: preserve F23 payload shape: `user_id`, `kind`, `note_id`.
- MUST NOT: add the SSE endpoint in F24; F25 owns HTTP streaming.
- MUST NOT: add a cross-process broker dependency; Postgres NOTIFY is the cross-worker broadcast path.

**Ready:** YES
**Next hop:** researcher

### Resolved feature (verbatim from keel-feature-resolve.py)

```json
{
  "ok": true,
  "feature_id": "F24",
  "feature_index": 1,
  "feature_pointer_base": "/features/1",
  "prd_path": "/Users/tej/src/parchmark/docs/exec-plans/prds/realtime-notes-list-revalidation.json",
  "canonical_prd_path": "/Users/tej/src/parchmark/docs/exec-plans/prds/realtime-notes-list-revalidation.json",
  "title": "Per-worker LISTEN consumer plus per-user broker fanout",
  "layer": "service",
  "oracle": {
    "type": "integration",
    "setup": "FastAPI lifespan running with PostgreSQL NOTIFY available.",
    "assertions": [
      "Each worker starts exactly one LISTEN connection on the note events channel.",
      "A broker with subscribers for two users routes each payload only to subscribers for that payload's user.",
      "A saturated subscriber queue is disconnected without preventing other subscribers from receiving events.",
      "Two broker instances each receive every PostgreSQL notification, proving cross-worker fanout through Postgres."
    ],
    "tooling": "pytest async integration tests with broker instances and PostgreSQL NOTIFY."
  },
  "contract": {
    "listen_channel": "notes_events",
    "listener_scope": "one_per_uvicorn_worker",
    "startup_hook": "FastAPI lifespan",
    "broker_scope": "in_process_per_worker",
    "subscriber_key": "user_id",
    "subscriber_queue_limit": 50,
    "slow_consumer_policy": "disconnect_subscriber",
    "fanout_rule": "route payloads only to subscribers matching payload.user_id",
    "multi_tab_policy": "independent_subscribers",
    "cross_worker_delivery": "postgres_notify_broadcast",
    "payload_fields": [
      "user_id",
      "kind",
      "note_id"
    ]
  },
  "needs": [
    "F23"
  ],
  "prd_invariants_exercised": [],
  "backlog_fields": {
    "prd_slug": "realtime-notes-list-revalidation",
    "prd_exempt_reason": null,
    "spec_ref": null,
    "design_refs": [],
    "needs_ids": [
      "F23"
    ],
    "human_markers": [],
    "prototype_mode": null
  },
  "classification": "JSON_PRD_PATH"
}
```

## researcher
## Research Brief: asyncpg LISTEN notification callbacks

**Questions investigated:**
1. How should the worker subscribe to Postgres notifications? - Use a dedicated `asyncpg.Connection` and `await connection.add_listener(channel, callback)`.
2. What callback shape should the broker expect? - The callback receives `(connection, pid, channel, payload)`; asyncpg 0.31.0 accepts a callable or coroutine callback.
3. How should shutdown unregister the listener? - Call `remove_listener(channel, callback)` before closing the dedicated connection; closing the connection also ends LISTEN state.

**Open questions (if any):**
- None.

**Recommended pattern:**
Create a single dedicated connection per FastAPI worker lifespan, register one listener for `notes_events`, parse each payload, and dispatch into the in-process broker. Do not borrow request/session connections for LISTEN because LISTEN is connection-scoped and long-lived.

**Gotchas:**
- LISTEN is per connection; using the SQLAlchemy request/session pool would tie listener state to pooled connection lifetime.
- Notification callbacks should not block. Schedule lightweight broker dispatch on the event loop and keep slow-consumer handling inside bounded queues.
- Invalid JSON payloads should be logged and ignored.

**Confidence:** HIGH
**Follow-up tests:** Assert two independent listener instances both receive one notification from Postgres, and assert saturated subscriber queues are disconnected.

**Sources:**
- Official asyncpg docs: https://magicstack.github.io/asyncpg/current/_modules/asyncpg/connection.html#Connection.add_listener
- Local installed asyncpg 0.31.0 signature: `Connection.add_listener(self, channel, callback)`

### Decisions (optional)
- Use a direct asyncpg connection for LISTEN because the API is connection-scoped.
- Use a nonblocking callback that schedules broker publish work on the running event loop.
- Keep retry/reconnect out of F24 unless needed by tests; the contract only requires one listener per worker and clean fanout.

**Next hop:** backend-designer

## arch-advisor-consultation
## Oracle Consultation: Per-worker LISTEN consumer plus per-user broker fanout

**Bottom line:** Build this as a small backend service module with an in-process broker and a dedicated asyncpg LISTEN connection owned by FastAPI lifespan. Keep the broker independent from HTTP/SSE so F24 only establishes delivery semantics and F25 can attach a route later.

**Action plan:**
1. Define a typed note-event payload and bounded subscriber abstraction in `backend/app/services/note_events.py`.
2. Implement `NoteEventBroker.subscribe()`, `unsubscribe()`, and `publish()` as synchronous in-memory operations over asyncio queues.
3. Implement `PostgresNoteEventListener.start()` with one `asyncpg.connect()` and one `add_listener("notes_events", callback)` call.
4. Decode notification JSON in the listener callback and hand valid payloads to the broker; log and ignore invalid payloads.
5. Wire one listener into `backend/app/main.py:lifespan`, start it after successful DB init, and stop it during shutdown before disposing the SQLAlchemy engine.
6. Keep app state resettable in tests by storing the listener on `app.state`.

**Effort estimate:** Medium

**Why this approach:**
- It honors the contract's `in_process_per_worker` broker scope without adding infrastructure.
- A dedicated asyncpg connection matches Postgres LISTEN semantics and avoids contaminating request/session pools.
- Keeping broker APIs independent of FastAPI lets F25 consume them without refactoring.

**Watch out for:**
- Do not let one full subscriber queue block fanout to other subscribers.
- Do not create the listener at import time; startup should own network I/O.
- Do not add reconnect loops in F24 unless the tests require them; this feature is scoped to initial listener and fanout.

### Constraints for downstream
- MUST: store listener lifecycle state on `app.state` or an explicit module-level singleton that tests can reset.
- MUST: use a dedicated asyncpg connection for LISTEN.
- MUST: keep F24 free of HTTP/SSE route work.
- MUST NOT: block publisher fanout on `await queue.put()`.

## backend-designer / frontend-designer
## Backend Design: Per-worker LISTEN consumer plus per-user broker fanout

**Module:** `app.services.note_events`
**Layer:** Services
**Depends on:** `asyncio`, `asyncpg`, `json`, `logging`, `app.database.database.SQLALCHEMY_DATABASE_URL`
**Called by:** `app.main.lifespan`, future F25 SSE router

**Public API:**
- `NoteEvent(kind: str, note_id: int, user_id: int)` - immutable event delivered to subscribers.
- `NoteEventBroker.subscribe(user_id: int, queue_limit: int = 50) -> NoteEventSubscriber` - registers one independent subscriber.
- `NoteEventBroker.unsubscribe(subscriber: NoteEventSubscriber) -> None` - removes and closes a subscriber.
- `NoteEventBroker.publish(event: NoteEvent) -> None` - fans out to matching user subscribers only.
- `NoteEventBroker.publish_payload(payload: Mapping[str, object]) -> None` - validates F23 payload fields and publishes.
- `PostgresNoteEventListener.start() -> None` - opens one LISTEN connection and registers callback.
- `PostgresNoteEventListener.stop() -> None` - unregisters callback and closes the connection.
- `create_note_event_listener(broker: NoteEventBroker | None = None) -> PostgresNoteEventListener` - factory used by lifespan.

**Internal state (if stateful process):**
```python
{
    "_subscribers_by_user": dict[int, set[NoteEventSubscriber]],
    "_connection": asyncpg.Connection | None,
    "_started": bool,
}
```

**Key decisions:**
- Subscriber queues use `put_nowait`; on `QueueFull`, that subscriber is removed and closed.
- `publish()` snapshots matching subscribers before fanout so unsubscribe during iteration is safe.
- Listener callback does minimal work: parse and publish, logging invalid payloads.
- DSN normalization strips SQLAlchemy driver prefixes before passing the URL to asyncpg.

**Patterns to follow:**
- `backend/app/main.py:lifespan` for startup/shutdown sequencing.
- `backend/tests/conftest.py` for Postgres testcontainer URL conversion.
- `backend/tests/integration/migrations/test_f23_notes_notify_trigger.py` for notification payload expectations.

**Files to create:**
- `backend/app/services/note_events.py` - event model, broker, subscriber, listener.
- `backend/tests/unit/services/test_note_events.py` - broker and listener unit coverage with fakes.
- `backend/tests/integration/test_note_events_listener.py` - real Postgres NOTIFY fanout to two listener instances.

**Files to modify:**
- `backend/app/main.py` - create/start/stop F24 listener in lifespan.
- `docs/exec-plans/active/feature-backlog.md` - check F23 dependency bookkeeping.

### Decisions
- Use direct asyncpg because LISTEN is connection-scoped.
- Store lifecycle listener on `app.state.note_event_listener` for test visibility and cleanup.
- Use immutable `NoteEvent` objects so downstream subscribers cannot mutate shared event data.
- Treat invalid payloads as dropped notifications rather than app-fatal runtime errors.
### Constraints for downstream
- MUST: queue capacity default must be exactly 50.
- MUST: two subscribers for the same user must both receive a matching event.
- MUST: two broker/listener instances must both receive a Postgres notification.
- MUST NOT: start the listener before database initialization succeeds.
- MUST NOT: add routing, authentication, or streaming response logic in F24.

**Next hop:** test-writer

## roundtable-design-review
<!-- Multi-model advisory review of designer output (Step 2.5, if roundtable enabled). -->

## test-writer
## Test Report: Per-worker LISTEN consumer plus per-user broker fanout

**PRD:** /Users/tej/src/parchmark/docs/exec-plans/prds/realtime-notes-list-revalidation.json
**Feature ID:** F24
**Feature index:** 1
**Test files:** `backend/tests/unit/services/test_note_events.py`, `backend/tests/unit/app/test_note_events_lifespan.py`, `backend/tests/integration/test_note_events_listener.py`
**Tests written:** 16
**Status:** RED-NEW (module under test did not exist before implementation)
**Failure output:** Initial red run failed with `ModuleNotFoundError: No module named 'app.services.note_events'`.

**Assertion traceability:**
- `/features/1/oracle/assertions/0` -> `test_lifespan_starts_one_note_event_listener_after_database_init`, `test_listener_start_registers_exactly_one_listen_connection`
- `/features/1/oracle/assertions/1` -> `test_broker_routes_payloads_only_to_matching_user`
- `/features/1/oracle/assertions/2` -> `test_saturated_subscriber_is_disconnected_without_blocking_others`
- `/features/1/oracle/assertions/3` -> `test_two_broker_instances_each_receive_every_postgres_notification`

### Decisions (optional)
- Added unit coverage for broker semantics so most F24 behavior is testable without Docker.
- Added one Postgres integration test for cross-worker broadcast semantics through NOTIFY.
- Added a lifespan test to keep startup ownership in `app.main` explicit.

**Next hop:** implementer

## implementer
## Implementation Report: Per-worker LISTEN consumer plus per-user broker fanout

**Files created:**
- `backend/app/services/note_events.py`
- `backend/tests/unit/services/test_note_events.py`
- `backend/tests/unit/app/test_note_events_lifespan.py`
- `backend/tests/integration/test_note_events_listener.py`

**Files modified:**
- `backend/app/main.py`
- `backend/tests/conftest.py`
- `backend/tests/integration/test_main.py`
- `backend/tests/integration/test_app_boot_no_openai.py`
- `docs/exec-plans/active/feature-backlog.md`
- `docs/exec-plans/active/handoffs/F24-per-worker-listen-broker-fanout.md`

**Changed paths:**
- `backend/app/services/note_events.py`
- `backend/app/main.py`
- `backend/tests/conftest.py`
- `backend/tests/unit/services/test_note_events.py`
- `backend/tests/unit/app/test_note_events_lifespan.py`
- `backend/tests/integration/test_note_events_listener.py`
- `backend/tests/integration/test_main.py`
- `backend/tests/integration/test_app_boot_no_openai.py`
- `docs/exec-plans/active/feature-backlog.md`
- `docs/exec-plans/active/handoffs/F24-per-worker-listen-broker-fanout.md`

**Implementation summary:**
Added `NoteEventBroker` with per-user subscriber sets, bounded independent queues, and slow-subscriber disconnect behavior. Added `PostgresNoteEventListener`, backed by one dedicated asyncpg LISTEN connection, and wired it into FastAPI lifespan after database init and before async engine disposal.

**Verification run locally:**
- `cd backend && uv run pytest tests/unit/services/test_note_events.py tests/unit/app/test_note_events_lifespan.py -q` -> 15 passed
- `cd backend && uv run pytest tests/unit/services/test_note_events.py --cov=app.services.note_events --cov-report=term-missing --cov-fail-under=90 -q` -> 14 passed, 100% service coverage
- `cd backend && uv run pytest tests/unit/services/test_note_events.py tests/unit/app/test_note_events_lifespan.py tests/integration/test_main.py::TestApplicationLifespan::test_lifespan_startup tests/integration/test_app_boot_no_openai.py::test_app_boots_without_openai_api_key -q` -> 16 passed
- `cd backend && uv run ruff check .` -> passed
- `cd backend && uv run ruff format --check .` -> passed
- `cd backend && uv run mypy app` -> passed
- `cd backend && uv run pytest tests/integration/test_note_events_listener.py -q` -> blocked locally because Docker socket is unavailable

### Decisions
- Used one dedicated asyncpg connection per listener because LISTEN state is connection-scoped.
- Kept broker publish synchronous and nonblocking by using `put_nowait`.
- Stored the lifespan listener on `app.state.note_event_listener` for clear ownership and test visibility.
- Patched existing TestClient fixtures to avoid opening a real LISTEN connection outside the F24 integration test.

## code-reviewer
## Code Review: Per-worker LISTEN consumer plus per-user broker fanout

**Verdict:** APPROVED

**Files reviewed:** `backend/app/services/note_events.py`, `backend/app/main.py`, `backend/tests/conftest.py`, `backend/tests/unit/services/test_note_events.py`, `backend/tests/unit/app/test_note_events_lifespan.py`, `backend/tests/integration/test_note_events_listener.py`, `backend/tests/integration/test_main.py`, `backend/tests/integration/test_app_boot_no_openai.py`
**Neighboring files compared:** `backend/app/services/health_service.py`, `backend/app/database/database.py`, `backend/tests/integration/migrations/test_f23_notes_notify_trigger.py`

**Findings:** None.

**Summary:** The implementation is small and aligned with the existing FastAPI lifespan and testcontainer patterns. Broker fanout is bounded and nonblocking, listener startup/shutdown is explicit, and the tests cover both pure service behavior and the Postgres broadcast path.

**Next hop:** spec-reviewer

## spec-reviewer
## Spec Conformance: Per-worker LISTEN consumer plus per-user broker fanout

**Verdict:** CONFORMANT
**Attempt:** 1

**PRD:** /Users/tej/src/parchmark/docs/exec-plans/prds/realtime-notes-list-revalidation.json
**Feature ID:** F24
**Feature index:** 1
**Feature pointer base:** /features/1
**Code:** `backend/app/services/note_events.py`, `backend/app/main.py`
**Tests:** `backend/tests/unit/services/test_note_events.py`, `backend/tests/unit/app/test_note_events_lifespan.py`, `backend/tests/integration/test_note_events_listener.py`

**Deviations (if any):** None.

**Notes:**
- `/features/1/contract/listen_channel` is implemented by `NOTE_EVENTS_CHANNEL = "notes_events"` and used by the listener and integration publisher.
- `/features/1/contract/listener_scope` and `/features/1/contract/startup_hook` are covered by lifespan wiring and one listener start per lifespan.
- `/features/1/contract/broker_scope`, `/subscriber_key`, `/subscriber_queue_limit`, `/slow_consumer_policy`, `/fanout_rule`, and `/multi_tab_policy` are implemented in `NoteEventBroker` and covered by unit tests.
- `/features/1/contract/cross_worker_delivery` is covered by two independent listener/broker instances receiving one Postgres notification.
- `/features/1/contract/payload_fields` is enforced by `publish_payload()`.

**Coverage gaps (if any):** None.

**Next hop:** safety-auditor

## safety-auditor
## Safety Audit: Per-worker LISTEN consumer plus per-user broker fanout

**Verdict:** PASS

**PRD:** /Users/tej/src/parchmark/docs/exec-plans/prds/realtime-notes-list-revalidation.json
**Feature ID:** F24
**Files scanned:** `backend/app/services/note_events.py`, `backend/app/main.py`, `backend/app/routers/**`

**Violations (if any):** None.

**Checks:**
- Tenant isolation: no `Note` ORM statements added in `backend/app/services/note_events.py` or `backend/app/main.py`.
- Auth required on routes: no routes added in F24.
- Raw SQL: no `text(...)` or raw SQL added in backend app code.
- Typed/bodyless mutations: no mutations or request bodies added.
- No secrets in logs: new log statements include channel/user id or exception summaries, not tokens/passwords/request bodies.
- Password hashing and OIDC binding invariants: not touched.

**Next hop:** arch-advisor

## arch-advisor-verification
## Oracle Verification: Per-worker LISTEN consumer plus per-user broker fanout

**Verdict:** SOUND

**Bottom line:** The implementation follows the consultation: the broker is isolated in a service module, FastAPI lifespan owns exactly one listener per worker process, and Postgres remains the cross-worker broadcast mechanism. The design does not add routes or infrastructure ahead of F25.

**Findings:** None.

**Optional future considerations:**
- F25 should consume `note_event_broker.subscribe()` directly and guarantee `unsubscribe()` on SSE disconnect.
- A reconnect loop may be useful later, but it is outside F24's stated contract.

## landing-verifier
## Doc Garden Report

**Mode:** pipeline (feature F24)
**Date:** 2026-05-15
**Code state:** F24 implemented on `keel/F24-per-worker-listen-broker-fanout`

### Findings

#### Pipeline-scoped
(clean)

#### P5 timeline-artifact sweep
(clean for F24-scoped/current-state docs; pre-existing archived-doc examples remain outside this feature's blast radius)

### Verdict

**doc_garden_verdict:** CLEAN
**drift_count:** 0
**Next hop:** orchestrator

## Landing Verification: Per-worker LISTEN consumer plus per-user broker fanout

**Verdict:** VERIFIED with Docker-backed integration deferred to Forgejo CI

**Local checks passed:**
- `python3 scripts/validate-prds.py --repo .`
- `uv run scripts/validate-prd-json.py docs/exec-plans/prds/realtime-notes-list-revalidation.json`
- `cd backend && uv run ruff check .`
- `cd backend && uv run ruff format --check .`
- `cd backend && uv run mypy app`
- `cd backend && uv run pytest tests/unit/services/test_note_events.py tests/unit/app/test_note_events_lifespan.py tests/integration/test_main.py::TestApplicationLifespan::test_lifespan_startup tests/integration/test_app_boot_no_openai.py::test_app_boots_without_openai_api_key -q`

**Local environment gap:**
- `cd backend && uv run pytest tests/integration/test_note_events_listener.py -q` could not start `PostgresContainer("postgres:17")` because Docker is unavailable at the local socket. This test is expected to run in Forgejo CI.

## roundtable-landing-review
<!-- Multi-model advisory review of implementation (Step 8.5, if roundtable enabled). -->
