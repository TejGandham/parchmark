# Feature Backlog



Smallest independently testable features. Execute top-to-bottom.
Each feature: read spec → write test → write code → verify.

**Specs:** `docs/product-specs/<spec>.md` (one per feature; authored before `/keel-pipeline`)
**Principles:** `docs/design-docs/core-beliefs.md`
**Architecture:** `ARCHITECTURE.md`

<!-- KEEL-BOOTSTRAP: not-applicable -->

---

## Foundation (backend pipeline starts here)

## Service

- [ ] **F01 Per-user in-process pub/sub event bus for note change events**
  Spec: docs/product-specs/notes-live-updates.md:event-bus
  Test: Unit test: subscribing to user A's channel and publishing a NoteChangedEvent with user_id=A delivers the event to A's subscriber and not to user B's subscriber, and unsubscribe removes the listener with no residual references.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- RESOLVED 2026-04-23 (roundtable 5/5 A, conf 0.85-0.95): NoteChangedEvent is a pydantic BaseModel in app.schemas with fields {kind: Literal["created","updated","deleted"], note_id: str, user_id: str, updated_at: datetime}. Subscribers trigger useRevalidator().revalidate() — the /notes loader is the canonical fresh-state source. Rationale: invariant 6 makes full-record payloads carry stale/null embeddings (background task runs AFTER commit); minimal payload avoids ~6KB-per-event Vector(1536) bandwidth cost on SSE; loader already owns state freshness contract. -->
  <!-- RESOLVED 2026-04-23 (roundtable 5/5 Postgres LISTEN/NOTIFY, conf 0.85-0.92): Event bus is cross-replica from day one, not in-process per pod. Publish via func.pg_notify('user_{user_id}_notes', <json>) from the SQLAlchemy expression layer; subscribe via asyncpg.add_listener() in a new helper module backend/app/database/pubsub.py. Per-user channel naming enforces invariant 1 at the pg layer. Invariant 3 AMENDMENT REQUIRED: add backend/app/database/pubsub.py as the 4th whitelisted raw-SQL site (LISTEN cannot be wrapped in ORM idioms — asyncpg driver-level callback). Rationale: k3s rolling restart creates transient 2-pod windows even at replica=1, so in-process bus ships silently broken at every deploy; Redis is net-new infra unjustified at parchmark scale; Postgres NOTIFY 8KB cap accommodates minimal payload (~150 bytes) with headroom. -->
  <!-- SPEC-NOTES: (a) incompatible with PgBouncer transaction-pooling mode — breaks LISTEN silently; (b) one LISTEN connection per worker, watch max_connections; (c) consider coalescing on bulk-import storms (ties into F05's debounce marker). -->

- [ ] **F02 SSE endpoint GET /api/notes/stream with per-request subscription and heartbeat**
  Spec: docs/product-specs/notes-live-updates.md:sse-endpoint | Needs: F01
  Test: Integration test: authenticated user opens GET /api/notes/stream, receives Content-Type text/event-stream, receives a periodic heartbeat comment within the configured interval, and the handler declares Depends(get_current_user) so an unauthenticated request returns 401 before any stream bytes are written.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- RESOLVED 2026-04-23 (roundtable 5/5 B, conf 0.82-0.95): Frontend uses @microsoft/fetch-event-source polyfill so the request carries standard Authorization: Bearer <jwt>. Backend endpoint stays vanilla: GET /api/notes/stream with unchanged Depends(get_current_user). No new auth concepts, no ticket store, token never in URL (invariant 5 safe). Rationale: A (ticket) = new endpoint + Postgres store + safety-auditor amendment for narrow transport problem; C (query token) = invariant 5 landmine; D (cookie) = fragments pure-Bearer auth model. ~6-8 KB gzipped polyfill is noise against React+Chakra baseline. Future bundle optimization: native fetch + eventsource-parser (~2 KB) is a valid swap if needed. -->
  <!-- RESOLVED 2026-04-23 (heartbeat/timeout): 15s SSE heartbeat comment (": heartbeat\n\n"). No server-side idle-disconnect — connection lifetime bounded by JWT expiry (~30 min) and client reconnect loop. Proxy config required at landing: /api/notes/stream needs proxy_buffering off + proxy_cache off + proxy_read_timeout 1800s in both nginx.conf (dev) and k3s ingress manifest (operator applies outside-repo). -->
  <!-- SPEC-NOTES: (a) 5-min pre-landing audit of @microsoft/fetch-event-source — last release date, open-issue count, memory behavior on long-lived streams; (b) polyfill provides reconnect/backoff but F04's spec must still call out explicit backoff policy (ties into F04 marker 2); (c) useAuthStore's 401-retry-then-refresh flow composes with fetch-event-source's onopen/onerror hooks. -->

- [ ] **F03 Publish note-change events from POST/PUT/DELETE note handlers after commit**
  Spec: docs/product-specs/notes-live-updates.md:publish-on-mutation | Needs: F01, F02
  Test: Integration test: POST /api/notes (and PUT, DELETE) as user A triggers exactly one publish to user A's channel after the DB commit succeeds, publish is skipped if the commit raises, and the published event never leaks across users (filtered by current_user.id per invariant 1).
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 1 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- HUMAN: Embedding generation currently runs via background_tasks.add_task after commit (invariant 6). Confirm publish() runs on the request path immediately after commit, NOT inside the embedding task, so subscribers are notified promptly and an embedding failure never suppresses the notification. -->

## UI

- [ ] **F04 Frontend EventSource client service with reconnect and ticket-based auth**
  Spec: docs/product-specs/notes-live-updates.md:event-source-client | Needs: F02
  Test: Unit test with a mocked EventSource: client connects using the auth strategy chosen in F02, dispatches incoming note-change events to registered listeners, auto-reconnects with backoff on transient disconnect, and tears down cleanly on close() with no dangling listeners.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 2 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- HUMAN: Client auth approach depends on F02 resolution (ticket vs polyfilled fetch-event-source vs query-param). Spec must pick the matching client implementation. -->
  <!-- HUMAN: Reconnect/backoff policy (initial delay, max delay, jitter) is unspecified. -->

- [ ] **F05 NotesLayout mount hook that revalidates router loaders on note-change events**
  Spec: docs/product-specs/notes-live-updates.md:revalidate-on-event | Needs: F04
  Test: Component test: mounting NotesLayout subscribes via the F04 client; firing a synthetic note-change event calls useRevalidator().revalidate() exactly once per event, and unmounting closes the subscription so no revalidate fires afterwards.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 1 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- HUMAN: Should revalidation be debounced/coalesced when many events arrive in a burst (e.g. bulk import)? Default of one revalidate per event may be wasteful. -->

- [ ] **F06 BroadcastChannel complement for same-browser multi-tab note sync**
  Spec: docs/product-specs/notes-live-updates.md:broadcast-channel | Needs: F05
  Test: Integration test with two simulated tabs sharing an origin: a mutation in tab A posts to a 'parchmark-notes' BroadcastChannel, tab B receives the message and triggers revalidation without requiring an SSE round-trip.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 2 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- HUMAN: User listed this as optional. Confirm whether it ships with the initial feature or is deferred to a follow-up. -->
  <!-- HUMAN: Message schema on the channel — mirror the server NoteChangedEvent shape, or send a simpler 'notes-dirty' signal? -->

## Cross-cutting

- [ ] **F07 End-to-end two-tab live-update test for note list refresh**
  Spec: docs/product-specs/notes-live-updates.md:e2e-two-tab | Needs: F03, F05
  Test: E2E test: tab A and tab B both logged in as the same user view the notes list; tab A creates a note, and within a bounded time budget tab B's notes list shows the new note without a manual refresh. Repeat for update and delete.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 2 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- HUMAN: Time budget for 'within bounded time' is unspecified. Suggest e.g. 3 seconds, to be confirmed in spec. -->
  <!-- HUMAN: Which test harness — Playwright, Vitest + mocked EventSource, or a backend integration test with an HTTP SSE client? Repo does not currently have a browser E2E suite wired in. -->

