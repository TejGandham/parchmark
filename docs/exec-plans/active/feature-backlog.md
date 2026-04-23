# Feature Backlog



Smallest independently testable features. Execute top-to-bottom.
Each feature: read spec → write test → write code → verify.

**Specs:** `docs/product-specs/[YOUR-SPEC].md`
**Principles:** `docs/design-docs/core-beliefs.md`
**Architecture:** `ARCHITECTURE.md`

<!-- KEEL-BOOTSTRAP: not-applicable -->

---

## Foundation (backend pipeline starts here)

## Service

- [ ] **F01 Per-user in-process pub/sub event bus for note change events**
  Spec: docs/product-specs/notes-live-updates.md:event-bus
  Test: Unit test: subscribing to user A's channel and publishing a NoteChangedEvent with user_id=A delivers the event to A's subscriber and not to user B's subscriber, and unsubscribe removes the listener with no residual references.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 2 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- HUMAN: Event payload schema not specified. Should NoteChangedEvent carry {kind: created|updated|deleted, note_id, updated_at} only, or the full Note record? Pydantic BaseModel required per invariant 4 if it ever becomes an HTTP body. -->
  <!-- HUMAN: Multi-worker deployment posture: is the backend guaranteed single-process for this feature, or does the spec need to acknowledge that in-process pub/sub only notifies subscribers on the same worker (and plan a cross-worker story later)? -->

- [ ] **F02 SSE endpoint GET /api/notes/stream with per-request subscription and heartbeat**
  Spec: docs/product-specs/notes-live-updates.md:sse-endpoint | Needs: F01
  Test: Integration test: authenticated user opens GET /api/notes/stream, receives Content-Type text/event-stream, receives a periodic heartbeat comment within the configured interval, and the handler declares Depends(get_current_user) so an unauthenticated request returns 401 before any stream bytes are written.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 2 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- HUMAN: EventSource cannot send Authorization headers. Pick an auth strategy: (a) short-lived single-use ticket endpoint POST /api/notes/stream/ticket returning a token consumed by GET /api/notes/stream?ticket=..., (b) a polyfilled EventSource such as @microsoft/fetch-event-source that supports headers, or (c) auth-via-query-param. Spec must pick one before implementation. -->
  <!-- HUMAN: Heartbeat interval and idle-disconnect timeout are unspecified. Propose values (e.g. 15s heartbeat, 60s idle cutoff) and confirm they play nicely with nginx/k3s proxy buffering defaults. -->

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

