# V2 Application TODOs

Vetted against the current `parchmark-v2` worktree on June 21, 2026.

This file tracks remaining application work from the v2 redesign. It separates
real backend expansion from frontend wiring against endpoints that already
exist. The backend SSE note-events infrastructure is intentionally parked for
future UI upgrades and is not a deletion target.

## Backend Expansion

### 1. Persisted Note Tags

Status: implemented in this branch from `.karta/binders/persisted-note-tags.json`;
Docker-backed migration/API verification still needs CI or a local Docker socket.

Originally needed because the v2 UI already had tag chips, tag filters, and
active-note tag metadata, while backend `NoteResponse` did not expose tags.
This branch adds the backend contract, frontend list consumption, and
persisted tag-edit UI.

Backend work completed in this branch:
- Add tag storage for notes.
- Return `tags: string[]` on note list/detail/create/update responses.
- Accept optional tags on note create and update.
- Normalize, deduplicate, validate, and preserve tenant isolation for tags.
- Add migration and API tests.

Frontend work completed in this branch:
- Update `NoteDTO` and `useNotes()` to consume backend tags.
- Persist tag add/remove through the note update API.
- Re-enable tag filter tests that were deferred while backend tags were absent.

### 2. Profile Settings Contract

Status: not planned yet.

Needed because the settings entry exists in the shell, but the v2 UI does not
yet have a real profile screen.

Backend work:
- Decide the profile fields the UI can read and edit.
- Keep existing account metadata available: username, email, auth provider,
  account creation date, and note count.
- Add update endpoints only for fields the product actually allows users to
  change.
- Make local-account and SSO-account constraints explicit in response data.

Frontend work:
- Replace the settings placeholder with a profile settings view.
- Render provider-specific copy and disabled states based on backend metadata.

### 3. Workspace Settings Contract

Status: not planned yet.

Needed because workspace preferences are mentioned in the settings placeholder,
but no persisted backend preference contract exists.

Backend work:
- Define a per-user workspace/preferences model.
- Persist preferences that should survive across devices, such as theme,
  default note view, editor defaults, markdown/rendering preferences, or sort
  defaults once product scope is confirmed.
- Add read/update endpoints for those preferences.

Frontend work:
- Move durable preferences out of local-only state where appropriate.
- Keep ephemeral view state local unless product scope says otherwise.

### 4. SSO Settings Surface

Status: not planned yet.

Core OIDC/SSO auth exists, but the settings UI still needs an explicit account
metadata and provider-management contract.

Backend work:
- Expose whether the current account is local or SSO-backed.
- Expose whether password change is available.
- Expose SSO identity attributes needed by the UI, such as email/provider
  metadata.
- Decide whether connect, disconnect, provider switch, or IdP management links
  are in scope.

Frontend work:
- Show the right account-management affordances for local vs SSO users.
- Avoid offering password changes for SSO-only accounts.

## Frontend Wiring Against Existing Backend

### 5. Note Create, Update, Delete, And Tag Edits

Status: implemented for create, markdown update, delete, and tag add/remove.

Backend already has:
- `POST /api/notes/`
- `PUT /api/notes/{note_id}`
- `DELETE /api/notes/{note_id}`

Frontend now:
- Wires the new-note action to backend create.
- Persists markdown edits through backend update.
- Persists tag add/remove through backend update.
- Wires delete to backend delete and surfaces mutation errors.

Remaining product decision:
- Add delete confirmation if product scope requires it.

### 6. Existing Settings Routes

Status: backend exists; frontend not wired.

Backend already has:
- `GET /api/settings/user-info`
- `POST /api/settings/change-password`
- `GET /api/settings/export-notes`
- `DELETE /api/settings/delete-account`

Frontend work:
- Build the settings screen around these routes.
- Add account info, password change, export-all-notes, and delete-account UI.
- Handle OIDC/local-account constraints cleanly.

## Parked Infrastructure

### 7. SSE Note Events

Status: parked backend infrastructure.

Do not delete. The backend stream is available for future UI live-update work:
- `GET /api/notes/events`

Future frontend work:
- Add a Vue event-stream client when live note-list refresh is in scope.
- Reconcile missed events by refetching the notes list.
- Ensure logout/session refresh tears down or reconnects the stream correctly.

## Out Of Scope Unless Product Scope Changes

- Server-generated export for a single active note. The current single-note
  `.md` export can remain client-side.
- Server-side note search or tag query parameters. The current v2 UI filters
  client-side after fetching the notes list.
- Bulk tag management, tag colors, tag ordering, cross-note tag admin, or saved
  tag views.
- Mermaid runtime rendering. The current renderer only emits Mermaid markup.
