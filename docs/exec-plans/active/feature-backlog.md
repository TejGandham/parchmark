# Feature Backlog

<!-- KEEL-INVARIANT-7: legacy-through=F00 -->

Smallest independently testable features. Execute top-to-bottom.
Each feature: read spec → write test → write code → verify.

**Specs:** `docs/product-specs/<spec>.md` (one per feature; authored before `/keel-pipeline`)
**PRDs:** `docs/exec-plans/prds/<slug>.md` (one per cohesive feature set; authored via `/keel-refine`)
**Principles:** `docs/design-docs/core-beliefs.md`
**Architecture:** `ARCHITECTURE.md`

<!-- KEEL-BOOTSTRAP: not-applicable -->

---

## Foundation (backend pipeline starts here)

## Service

- [ ] **F01 Postgres trigger emits NOTIFY on note title/content/delete**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F01-db-notify-trigger
  PRD: realtime-notes-list-revalidation
  Test: After alembic migration applied, a row trigger on the notes table fires NOTIFY on channel `notes_events` with JSON payload {user_id, kind, note_id} for INSERT, UPDATE-of-{title,content}, and DELETE. Embedding-only updates (UPDATE setting only the embedding column) MUST NOT fire the trigger. NOTIFY is transactional with row commit (rollback => no NOTIFY). Integration test: open a LISTEN connection, perform one of each qualifying mutation, assert exactly one payload received per qualifying mutation and zero for an embedding-only update.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

- [ ] **F02 Per-worker LISTEN consumer + per-user broker fanout**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F02-listen-and-broker | Needs: F01
  PRD: realtime-notes-list-revalidation
  Test: FastAPI lifespan starts exactly one Postgres LISTEN connection per uvicorn worker on channel `notes_events`. An in-process broker holds a per-user subscriber map. Test harness instantiates two subscribers (user A, user B) on the same broker, publishes mixed payloads via real NOTIFY, and asserts (a) A's queue receives only A's payloads, B's only B's, (b) a saturated subscriber (queue exceeds 50 events) is evicted via slow-consumer-disconnect while other subscribers continue receiving normally, (c) a separate test instantiates two broker instances (each with its own LISTEN connection) and verifies both receive every NOTIFY — proving cross-worker fanout via Postgres.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

- [ ] **F03 Authenticated SSE endpoint /notes/events**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F03-sse-endpoint | Needs: F02
  PRD: realtime-notes-list-revalidation
  Test: GET /notes/events with a valid Authorization: Bearer header returns 200 with Content-Type: text/event-stream and registers a subscriber on the broker keyed on current_user.id. Missing or invalid token returns 401. The wire payload of each event is exactly {kind, note_id} as JSON in the SSE `data:` field — the user_id used for routing never crosses the wire. Disconnect (TCP close from client) unregisters the subscriber from the broker (verified by asserting broker subscriber count decrements). Cross-user isolation is NOT this entry's concern — F11 covers it end-to-end.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

- [ ] **F04 SSE lifecycle: 30s heartbeat + disconnect cleanup**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F04-sse-lifecycle | Needs: F03
  PRD: realtime-notes-list-revalidation
  Test: The /notes/events stream emits a SSE comment-line heartbeat (`:heartbeat\n\n`) every 30 seconds while idle (verified by connecting an authenticated client, sending no mutations, and asserting at least one `:` comment frame is received within 32s). On client TCP close, the subscriber is removed from the broker within one heartbeat interval (asserted by broker subscriber count before/after). FastAPI lifespan shutdown closes all active streams and the LISTEN connection cleanly (no pending tasks warning in test logs).
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

## UI

- [ ] **F05 Frontend SSE client (fetch-event-source + Bearer auth)**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F05-sse-client | Needs: F03
  PRD: realtime-notes-list-revalidation
  Test: A new module under `ui/src/services/` (e.g. `notesEventStream.ts`) opens a stream to `/notes/events` using `@microsoft/fetch-event-source` with the same `Authorization: Bearer <token>` header that `services/api.ts` attaches to REST requests. The module exposes a typed subscribe(callback) API where callback receives `{kind, note_id}` parsed from each SSE event. Vitest test (mocked fetch-stream): opening a stream invokes fetch with the bearer header; injected SSE frames invoke the subscriber callback once per frame with the parsed payload; calling the returned dispose() function aborts the underlying fetch and stops invoking the callback. This entry covers the client connection lifecycle and event parsing only — wiring to router revalidation is F06.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

- [ ] **F06 Notes loader revalidation on each received event**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F06-revalidate | Needs: F05
  PRD: realtime-notes-list-revalidation
  Test: A subscriber attached at NotesLayout mount time calls `router.revalidate()` exactly once per received event. Because the React Router config exposes a single `id: 'notes-layout'` loader, blanket revalidation is the only available revalidation shape — selective per-loader revalidation is not architecturally available, and no decision is required. Vitest test: render the notes route with a mocked router; inject 3 SSE frames; assert `router.revalidate()` is called exactly 3 times. Browser smoke: with the notes list rendered and a separate authenticated client (curl) creating a note, the rendered list reflects the new note within 2s of the POST returning, and the network panel shows zero polling-style requests to `/api/notes` during a 30s idle window before the mutation.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

- [ ] **F07 Initial-connect / reconnect reconciliation**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F07-reconnect-revalidate | Needs: F05
  PRD: realtime-notes-list-revalidation
  Test: The client invokes `router.revalidate()` immediately on every stream open — both the initial connection AND every subsequent reconnect (handled by F08's backoff loop). This closes the lost-event window: NOTIFY is fire-and-forget, so any mutations that occur between the loader's initial fetch and `EventSource.onopen`, or during a network blip, are recovered by a forced revalidate once the stream is healthy. Vitest test: simulate stream open once, assert `router.revalidate()` called once; simulate close then re-open, assert a second `router.revalidate()` call. Browser smoke: kill the backend, perform a mutation via direct DB write, restart the backend; the rendered list reflects the mutation within 2s of stream re-open with no manual user action.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

- [ ] **F08 SSE auto-reconnect with exponential backoff**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F08-reconnect-backoff | Needs: F05
  PRD: realtime-notes-list-revalidation
  Test: When the underlying fetch-stream connection ends (server close, network error, non-401 5xx response), the client schedules a reconnect using exponential backoff: initial delay 1s, multiplier 2x, maximum cap 30s. Backoff resets to 1s after a successful stream open that lives longer than 30s (so a stable connection does not punish the next outage). Vitest test (fake timers): close the stream and assert reconnect attempts fire at t=1s, 3s, 7s, 15s, 31s (cap reached), 61s — verifying the schedule and the cap. Manual smoke: kill backend, observe reconnect attempts in dev tools network panel; restart backend, observe stream resumes and F07's revalidate fires.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

- [ ] **F09 SSE auth-failure handling: refresh, then retry / logout**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F09-sse-auth-failure | Needs: F05
  PRD: realtime-notes-list-revalidation
  Test: When the stream endpoint responds with 401 (token expired mid-stream or at connect time), the client invokes the existing `useAuthStore` token-refresh path BEFORE attempting another reconnect. On refresh success, the client opens a fresh stream with the new bearer token (and F08 backoff is reset). On refresh failure, the client invokes the existing logout path exactly once and stops reconnect attempts (no infinite refresh loop). Vitest test (mocked auth store + fake timers): inject a 401 response, assert refresh is called exactly once before the next reconnect attempt; second test injects a 401 and a refresh failure, assert logout is called exactly once and no further reconnect attempts are scheduled.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

- [ ] **F10 EventSource teardown on logout**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F10-logout-teardown | Needs: F05
  PRD: realtime-notes-list-revalidation
  Test: Calling `useAuthStore.logout()` (whether triggered by the user, by F09's terminal-failure cascade, or by the existing token expiration monitor) closes the active SSE stream within 100ms, preventing subscriber-queue leaks across logout/login cycles. Implementation: an effect or store-subscription in the SSE client module observes `isAuthenticated` transitions and disposes the stream on transition to false. Vitest test (fake timers + mocked auth store): subscribe to events; toggle `isAuthenticated` to false; advance timers 100ms; assert the underlying fetch is aborted and the broker would see a TCP close (verified by asserting the dispose callback was invoked and no further events are forwarded to subscribers). Backend smoke: log in, open a tab, log out, assert the broker subscriber count for the user decremented within 100ms.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->

## Cross-cutting

- [ ] **F11 End-to-end cross-user isolation safety test (CI-gated)**
  Spec: docs/product-specs/realtime-notes-list-revalidation.md#F11-cross-user-isolation-e2e | Needs: F01, F02, F03, F06
  PRD: realtime-notes-list-revalidation
  Test: Pytest async integration test (httpx streaming client) that (1) creates two users A and B via the existing seed/user fixtures, (2) opens an authenticated SSE stream as user B and asserts the broker registers exactly one subscriber for B (verifying the connection actually reached the broker — guards against vacuous-pass where B receives nothing because the stream silently failed to register), (3) performs 10 interleaved mutations (mix of POST /api/notes, PATCH /api/notes/{id}, DELETE /api/notes/{id}) as user A via real HTTP calls, (4) asserts B's stream receives EXACTLY ZERO events during a 5-second post-mutation window, (5) as control: performs one mutation as user B and asserts B's stream receives exactly one event with the correct {kind, note_id} payload (proves the stream is alive, not broken). Wired into Forgejo CI as a required gate; merge-blocking. This entry exists because cross-user event leakage would silently violate domain invariants 1 (tenant isolation) and 2 (auth on every non-public route) on a brand-new transport surface that the existing REST tenant-isolation tests do not exercise.
  <!-- DRAFTED: 2026-04-24 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:9f3c7b2a1e8d5f04 -->
