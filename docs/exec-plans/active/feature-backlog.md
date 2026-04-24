# Feature Backlog



<!-- KEEL-INVARIANT-7: legacy-through=F07 -->

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
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- RESOLVED 2026-04-23: Confirmed. Handler ordering: (1) await db.commit() — persist first; events never fire on failed writes. (2) await pubsub.publish(channel=f"user_{current_user.id}_notes", event=NoteChangedEvent(...)) — on the request path, NOT background. Subscribers notified within one DB commit (~tens of ms), not after OpenAI embedding round-trip. (3) background_tasks.add_task(_generate_embedding_background, ...) — embedding stays background per invariant 6. Failure policy: publish() wrapped in try/except; NOTIFY failures logged but never propagated to user response. Matches parchmark's silent-degrade pattern for optional features (embeddings). Missed push = subscribers revalidate on next reconnect; no data loss. -->
  <!-- SPEC-NOTES: (a) test must assert all three ordering invariants: commit-first, publish-before-response, embedding-in-background; (b) publish failure must log per invariant 5 discipline — log the kind + note_id, NEVER the full event or any auth/user field; (c) each of POST, PUT, DELETE needs its own integration-test case for the user-isolation assertion. -->

## UI

- [ ] **F04 Frontend SSE client service (Bearer auth via fetch-event-source) with reconnect**
  Spec: docs/product-specs/notes-live-updates.md:event-source-client | Needs: F02
  Test: Unit test with a mocked fetch-event-source: client connects with Authorization: Bearer <jwt>, dispatches incoming note-change events to registered listeners, auto-reconnects with backoff on transient disconnect, refreshes token on 401 and reconnects, and tears down cleanly on close() with no dangling listeners.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- RESOLVED 2026-04-23 (auth): Determined by F02. Client uses @microsoft/fetch-event-source with Authorization: Bearer <jwt> header sourced from useAuthStore. No ticket endpoint. Token refresh on 401 via useAuthStore.refreshTokens() then reconnect. -->
  <!-- RESOLVED 2026-04-23 (backoff policy): Initial delay 1000 ms, exponential factor 2, max cap 30 s, jitter Uniform(0.8, 1.2), no attempt cap. Sequence: 1s, 2s, 4s, 8s, 16s, 30s, 30s... each × jitter. UI affordance: show "Live updates reconnecting..." toast after 3 consecutive failures (~7s), auto-dismiss on next successful connect. Reset backoff counter on successful connect. 401 is NOT a transient disconnect — call refreshTokens() first, then reconnect. Close on logout (useAuthStore.logout must call stream.close()). Do NOT close on tab hide; heartbeat keeps connection alive across visibility transitions. -->
  <!-- SPEC-NOTES: (a) test cases include: happy-path connect + event dispatch, transient 502 → backoff + retry, 401 → refresh + reconnect, refresh failure → bubble to auth store logout path, close() leaves no listeners; (b) service must expose an onEvent(callback) subscription API so F05's hook can register without importing fetch-event-source directly; (c) integrates with existing errorHandler.ts AppError for surfaced failures. -->

- [ ] **F05 NotesLayout mount hook that revalidates router loaders on note-change events**
  Spec: docs/product-specs/notes-live-updates.md:revalidate-on-event | Needs: F04
  Test: Component test: mounting NotesLayout subscribes via the F04 client; firing a synthetic note-change event calls useRevalidator().revalidate() within the coalescing window; bursts of N events within 500 ms fire at most 2 revalidates (leading + trailing); unmounting closes the subscription so no revalidate fires afterwards.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- RESOLVED 2026-04-23 (coalescing): Throttle with trailing flush, 500 ms window. On first event after idle: revalidate immediately + start 500ms timer (leading-edge, snappy for single events). Subsequent events during the window set a pending flag. On timer expiry: if pending, revalidate + restart timer + reset pending; else timer = null. Rationale: React Router's useRevalidator().revalidate() does not dedup — N calls = N fetches. Single event costs 1 revalidate with ~0ms latency; bulk import of 50 events over 5s costs ~10 revalidates (vs 50 without coalescing); worst-case 2nd-wave event latency is 500ms (acceptable for this feature). -->
  <!-- SPEC-NOTES: (a) implement as a custom hook useNoteChangeRevalidation mounted once in NotesLayout, not per-route; (b) cleanup on unmount must clear any pending timer to prevent leaks; (c) F06 (BroadcastChannel) is deferred for MVP — if un-deferred later, its events feed into the same coalescing layer (no double-revalidation when one tab's mutation reaches another via both SSE + BroadcastChannel). -->

- [ ] **F06 [DEFERRED] BroadcastChannel complement for same-browser multi-tab note sync**
  Spec: docs/product-specs/notes-live-updates.md:broadcast-channel | Needs: F05
  Test: Integration test with two simulated tabs sharing an origin: a mutation in tab A posts to a 'parchmark-notes' BroadcastChannel, tab B receives the message and triggers revalidation without requiring an SSE round-trip.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- DEFERRED 2026-04-23 (product decision: MVP scope, no bells and whistles): F06 is redundant with F02's SSE path for the stated use case. Tab A mutates → its own useFetcher() revalidates locally (React Router default). Tab B sees it via SSE → F03's pg NOTIFY → F04's subscriber → F05's revalidate. BroadcastChannel adds ~10ms-vs-50ms latency improvement (imperceptible), SSE-reconnect fallback (rare), and minor backend-NOTIFY savings. All marginal. Revisit after F01-F05 ship if multi-tab UX lag is observable. Do NOT pipeline F06 without product sign-off. -->
  <!-- SPEC-NOTES: If un-deferred later: mirror server NoteChangedEvent shape on the channel (keeps F05's coalescing layer transport-agnostic and preserves kind discriminator for per-event-type optimizations). Feed into same 500ms coalesce window as SSE events — no double-revalidation when one tab's mutation reaches another via both transports. -->

## Cross-cutting

- [ ] **F07 Two-tab live-update acceptance gate (hybrid: backend integration + frontend unit + manual DevTools MCP)**
  Spec: docs/product-specs/notes-live-updates.md:e2e-two-tab | Needs: F03, F05
  Test: Three-part acceptance gate. (a) Backend integration (pytest + httpx SSE client): NOTIFY from publish → SSE delivery → correct payload → no cross-user leakage, for each of POST/PUT/DELETE. (b) Frontend unit (Vitest + mocked fetch-event-source): synthetic event → F05 coalescing → useRevalidator().revalidate() fires within the 500ms window. (c) Manual acceptance (Chrome DevTools MCP): two tabs same user; mutation in tab A shows in tab B within 2 seconds without manual refresh, for create/update/delete; browser console clean.
  <!-- DRAFTED: 2026-04-23 by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: prose:0f4b2c1d7a9e3b6f -->
  <!-- RESOLVED 2026-04-23 (time budget): 2 seconds. Latency budget: pg NOTIFY <1ms + SSE delivery ~50-200ms + F05 leading-edge revalidate 0ms + loader fetch ~100-500ms = ~200ms-1s total on healthy network. 2s gives 2-5x margin. <2s flakes on slow CI; >3s enters "why hasn't it updated yet" territory. -->
  <!-- RESOLVED 2026-04-23 (test harness): Split the e2e goal into three verifiable pieces; skip Playwright for MVP. Rationale: parchmark's current testing posture is pytest (backend, testcontainers Postgres) + Vitest (frontend) + Chrome DevTools MCP (manual visual QA per AGENTS.md). Standing up Playwright for one test is MVP-scope violation. F07a + F07b are automated in CI; F07c is manual acceptance before merge, documented in PR description. -->
  <!-- SPEC-NOTES: (a) F07a must assert publish-after-commit-only (publish skipped on rollback) — ties into F03's failure-policy; (b) F07c is the merge gate — PR description documents the manual run, operator attests; (c) tech debt: when parchmark grows an automated browser E2E suite (likely triggered by F07c becoming recurring pain), add a Playwright-based F07d as a follow-up and keep F07c as a fallback; (d) log an entry in docs/exec-plans/tech-debt-tracker.md: "No automated browser E2E; manual Chrome DevTools MCP gates live-update acceptance. Graduate to Playwright when F07c pain exceeds manual-run cost." -->

