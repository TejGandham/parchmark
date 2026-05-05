# Realtime Notes List Revalidation

The notes list in the ParchMark UI must reflect server-side changes to a user's
notes (creates, updates, deletes) without a manual refresh and without
client-side polling. The chosen approach is server-push: the backend emits
change events to authenticated clients over a one-way streaming channel
(Server-Sent Events), and the UI subscribes and revalidates the notes list when
relevant events arrive.

Scope covers (a) a backend mechanism to detect note mutations and fan them out
to subscribers per-user, (b) an authenticated streaming endpoint that delivers
those events to the active browser session, (c) a frontend subscription that
hooks into the existing router data layer to revalidate the notes list on each
event, and (d) the cross-cutting concerns of authentication on the stream,
strict per-user event isolation, graceful reconnection, and reconciliation of
events missed during connect/reconnect windows.

## Pinned design facts (post-roundtable)

- Emission: PostgreSQL trigger in alembic migration scoped to title/content
  inserts, updates, and deletes; embedding-only column updates do NOT emit (so
  background embedding writes never produce client noise).
- Fanout: every uvicorn worker maintains its own LISTEN connection; an
  in-process broker per worker fans payloads to per-user subscriber queues.
  Cross-worker delivery happens via Postgres NOTIFY itself.
- Subscriber queues are bounded (50 events) with a slow-consumer-disconnect
  policy. A user with multiple tabs holds independent subscribers — no
  server-side dedup.
- Stream auth uses the standard Authorization: Bearer header via a fetch-stream
  client (e.g., @microsoft/fetch-event-source); query-string tokens are
  forbidden (would leak credentials into proxy and access logs).
- Heartbeat: 30s comment-line keepalive.
- Wire payload to client carries `{kind, note_id}`; the user_id used for
  routing stays server-side only.
- On every stream open (initial and after reconnect), the client immediately
  revalidates the notes loader to heal any events missed during the connection
  gap. NOTIFY is fire-and-forget; this is the recovery contract.
- Reconnect uses exponential backoff (1s initial, x2 multiplier, 30s cap).
- 401 on the stream triggers the existing token-refresh path; refresh failure
  cascades into the existing logout path.
- Logout closes the active EventSource within 100ms.

## Out of scope

- Long polling.
- Bidirectional WebSocket transport.
- Optimistic in-place patching of the notes cache (the contract is "tell the
  client to refetch", not "push the new note payload").
- Cross-device collaborative editing of a single open note.

## Invariants exercised

- Domain invariant 1 (tenant isolation on every Note ORM operation): the
  end-to-end isolation safety test asserts cross-user event leakage is zero
  on the new transport.
- Domain invariant 2 (auth required on every non-public route): the SSE
  endpoint enforces Authorization: Bearer and returns 401 otherwise.
- Domain invariant 3 (no raw SQL outside the three whitelisted sites): the
  NOTIFY emission lives in an alembic migration (a sanctioned raw-SQL site),
  not in app code.
- Domain invariant 5 (no secrets in logs): the bearer token never appears in
  a URL query string, request path, or any log line on the stream path.
