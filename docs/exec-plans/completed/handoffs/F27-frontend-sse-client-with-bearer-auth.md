# Frontend SSE client with bearer auth

---
status: LANDED
pipeline: frontend
spec_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F27
prd_ref: docs/exec-plans/prds/realtime-notes-list-revalidation.json#F27

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
code_review_attempt: 2
arch_advisor_verdict:
arch_retry_spec_review_attempt: 0
arch_retry_safety_attempt: 0

remote_name: origin
roundtable_enabled: false
pr_url: https://brahma.myth-gecko.ts.net:3000/stackhouse/parchmark/pulls/98

roundtable_design_attempt: 0
roundtable_design_verdict:
roundtable_skipped: true
roundtable_skip_reason: roundtable MCP tools unavailable in this Codex session
roundtable_landing_attempt: 0
roundtable_landing_verdict:
roundtable_retry_code_review_attempt: 0
roundtable_retry_spec_review_attempt: 0
roundtable_retry_safety_attempt: 0
doc_garden_verdict: CLEAN
doc_garden_drift_count: 0

---

## pre-check

**Feature ID:** F27
**Title:** Frontend SSE client with bearer auth
**PRD:** docs/exec-plans/prds/realtime-notes-list-revalidation.json#F27
**Pipeline:** frontend
**Intent:** build
**Complexity:** standard

Build a frontend service module at `ui/src/services/notesEventStream.ts` that subscribes to `GET /notes/events` using `@microsoft/fetch-event-source`, sends the same bearer token source used by REST calls, parses SSE data payloads shaped as `{kind, note_id}`, and returns a dispose function that aborts the stream and prevents later callback delivery.

### Constraints for downstream

- MUST: use `@microsoft/fetch-event-source` as the stream transport.
- MUST: source `Authorization: Bearer <token>` from the same auth-store token path used by REST requests.
- MUST: expose a typed `subscribe(callback)` API returning a dispose function.
- MUST: parse and forward only `{kind, note_id}` event payloads.
- MUST: abort the fetch stream and stop forwarding events after dispose.

## researcher

### Decisions (optional)

- Not needed. The feature uses explicit PRD requirements and existing local frontend auth/API patterns.

## arch-advisor-consultation

### Constraints for downstream

## backend-designer / frontend-designer

Implement F27 as a narrow frontend service module, not a route component or store effect. The service should be reusable by later revalidation and reconnect features while owning only connection setup, auth headers, payload parsing, and disposal.

### Decisions

- Place the module under `ui/src/services/notesEventStream.ts`, matching the PRD contract and existing API service boundary.
- Keep the public API to `subscribe(callback) => dispose` so F28 can attach router revalidation without coupling this feature to React Router.
- Use the existing auth store token source directly, matching `ui/src/services/api.ts`.
- Re-read the current token in a custom fetch wrapper for each `fetch-event-source` network attempt, avoiding stale bearer headers after token refresh.

### Constraints for downstream

- Do not wire router revalidation, reconnect policy, auth-failure refresh, or logout teardown here; F28-F32 own those behaviors.

## roundtable-design-review

## test-writer

### Decisions (optional)

- Added focused Vitest contract coverage for future `ui/src/services/notesEventStream.ts`.
- Assertions cover `subscribe(callback)` opening `/api/notes/events` through `@microsoft/fetch-event-source` with the same auth-store bearer token path REST uses, forwarding parsed `{kind, note_id}` payloads once per SSE message, and aborting/suppressing later delivery after dispose.
- Added regression coverage that each transport fetch attempt uses the current auth-store token, preventing stale bearer headers on internal transport retries.
- Added negative coverage for malformed JSON and non-note payload shapes.
- Changed paths:
  - `ui/src/__tests__/services/notesEventStream.test.ts`
  - `docs/exec-plans/active/handoffs/F27-frontend-sse-client-with-bearer-auth.md`

### Verification

- Red as expected: `cd ui && npm test -- --run src/__tests__/services/notesEventStream.test.ts` fails because `../../services/notesEventStream` does not exist yet.

## implementer

Implemented F27 in `ui/src/services/notesEventStream.ts`:
- added typed `NoteEventPayload`, callback, and dispose exports;
- added `subscribe(callback)` using `@microsoft/fetch-event-source` against `${API_BASE_URL}/notes/events`;
- sourced bearer auth from `useAuthStore.getState().token`, the same source used by REST requests;
- injected a custom fetch wrapper that refreshes the Authorization header from the current auth-store token for each transport fetch attempt;
- parsed SSE `data` JSON and forwarded only payloads shaped as `{kind: string, note_id: string}`;
- returned a disposer that marks the subscription closed and aborts the underlying `AbortController`.

Added `@microsoft/fetch-event-source` to `ui/package.json` and `ui/package-lock.json`.

### Decisions
- Keep malformed frames as no-ops instead of surfacing errors to callers; the backend contract sends valid payloads, and later reconnect/error-policy features own recovery behavior.
- Preserve the initial `headers` option as a plain object for testability and use the custom fetch only to keep reconnect attempts current with the auth store.

## code-reviewer

**Verdict:** APPROVED

Initial review found a stale-token risk on `fetch-event-source` internal retries and missing malformed-payload coverage. Both were fixed. Re-review found no remaining code or package-manifest issues; only this handoff needed completion.

## spec-reviewer

**Verdict:** CONFORMANT

F27 contract conformance:
- `module_path`: implemented at `ui/src/services/notesEventStream.ts`.
- `transport_library`: uses `@microsoft/fetch-event-source`, declared in UI package manifests.
- `route`: opens `${API_BASE_URL}/notes/events`, resolving to the app's REST-prefixed `/api/notes/events` route.
- `auth_header_source`: reads bearer tokens from `useAuthStore.getState().token`, matching REST API requests.
- `public_api`: exports `subscribe(callback)` returning a dispose function.
- `event_payload_fields`: forwards only string `kind` and `note_id`.
- `dispose_behavior`: aborts the stream and suppresses later callback delivery.

## safety-auditor

Not needed. F27 is a frontend client service and does not change backend auth, tenant isolation, data models, migrations, or markdown rendering.

## arch-advisor-verification

Not needed.

## landing-verifier

**Verdict:** VERIFIED

Local verification:
- `cd ui && npm test -- --run src/__tests__/services/notesEventStream.test.ts` - passed, 5 tests.
- `cd ui && npm run lint` - passed.
- `cd ui && npm run build` - passed; existing large-chunk warning remains.
- `make test-ui-all` - passed; 44 files, 575 tests, 95.26% statements, 92.05% branches.

Full backend tests were not run because F27 only changes frontend service code and UI package manifests.

## roundtable-landing-review

Skipped: roundtable MCP tools are unavailable in this Codex session.

## doc-gardener

doc_garden_verdict: CLEAN
drift_count: 0

Backlog status updated for F27. No tech-debt entries were added; no resolved tech-debt items found in this feature's scope.
