# V2 Application TODOs

Vetted against the current `parchmark-v2` worktree on June 21, 2026.

This file tracks remaining application work from the v2 redesign. It separates
real backend expansion from frontend wiring against endpoints that already
exist. The backend SSE note-events infrastructure is now consumed by the frontend
for live note-list refresh.

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

Status: implemented for read-only account details, password availability, and
provider-specific copy; editable profile fields are not planned.

The settings screen is real now. It reads username, email, auth provider,
account creation date, and note count from `/api/settings/user-info`, then
shows local-vs-OIDC password copy.

Remaining product decision:
- Decide whether users may edit profile fields.

### 3. Workspace Settings Contract

Status: not planned yet.

Needed if workspace preferences become product scope. The current settings view
does not expose persisted workspace preferences, and no backend preference
contract exists.

Backend work:
- Define a per-user workspace/preferences model.
- Persist preferences that should survive across devices, such as theme,
  default note view, editor defaults, markdown/rendering preferences, or sort
  defaults once product scope is confirmed.
- Add read/update endpoints for those preferences.

Frontend work:
- Move durable preferences out of local-only state where appropriate.
- Keep ephemeral view state local unless product scope says otherwise.

### 4. SSO Provider Management Surface

Status: not planned yet.

Core OIDC/SSO auth exists, and the settings UI now shows provider-aware account
metadata and disables local password changes for OIDC accounts. Provider
management is still not planned.

Backend work:
- Decide whether connect, disconnect, provider switch, or IdP management links
  are in scope.

Frontend work:
- Add provider-management affordances only if product scope includes them.

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

Status: backend exists; frontend is wired for account info, password change, and
full-notes export. Delete-account UI is not wired.

Backend already has:
- `GET /api/settings/user-info`
- `POST /api/settings/change-password`
- `GET /api/settings/export-notes`
- `DELETE /api/settings/delete-account`

Frontend now:
- Shows account info.
- Supports local-account password changes and OIDC disabled-state copy.
- Downloads all notes through `/api/settings/export-notes`.

Remaining product decision:
- Add delete-account UI if product scope requires it.

## Live Note Events

### 7. SSE Note Events

Status: implemented — the frontend consumes the backend stream for live
note-list refresh.

Backend already had:
- `GET /api/notes/events`

Frontend now:
- Opens an authenticated event-stream client (`ui/src/services/noteEvents.ts`,
  `ui/src/features/notes/useNoteEvents.ts`) over the shared refresh-and-retry
  policy in `services/http.ts` (`requestStream`).
- Reconciles changes by refetching the notes list — `AppShell.vue` debounces a
  `useNotes().scheduleRefetch()` on each created/updated/deleted event.
- Tears the stream down on sign-out and on unmount, and reopens it on
  re-authentication.

## Out Of Scope Unless Product Scope Changes

- Server-generated export for a single active note. The current single-note
  `.md` export can remain client-side.
- Server-side note search or tag query parameters. The current v2 UI filters
  client-side after fetching the notes list.
- Bulk tag management, tag colors, tag ordering, cross-note tag admin, or saved
  tag views.
- Mermaid runtime rendering. The current renderer only emits Mermaid markup.
