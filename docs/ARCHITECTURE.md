# Architecture

> Domain map, layer dependencies, and cross-cutting concerns for ParchMark.

ParchMark is a full-stack markdown note-taking app with two domains: a Vue 3 frontend (`ui/`) and a FastAPI backend (`backend/`). They communicate over `/api/*`; most calls are JSON REST endpoints, and the settings notes export returns a ZIP download. Auth, note CRUD, tag edits, full-notes export, and live note-events refresh are wired to the backend. Copy and single-note export stay browser-only. For API endpoints, environment variables, commands, and coding patterns, see [AGENTS.md](../AGENTS.md).

```
+----------------------+         +-----------------------+
|       Frontend       |  HTTP   |       Backend         |
|    Vue 3 / Vite / TS  | ------> |  FastAPI / SQLAlchemy |
|    localhost:5173     | <------ |  localhost:8000       |
+----------------------+ JSON/ZIP +-----------------------+
                                           |
                                           v
                                  +-----------------+
                                  |   PostgreSQL    |
                                  +-----------------+
```

---

## Frontend (`ui/src/`)

The frontend is a ground-up **Vue 3** rewrite (`<script setup lang="ts">` SFCs, Vite, TypeScript). There is **no Pinia/Vuex and no Vue Router** — state lives in composables and plain `ref`/`computed`, and view switching is done by an auth gate plus `v-if` toggles. A DTCG design-token system generates the CSS variables the UI is built on.

### Layer Map

Layers are listed bottom-up. Code may only import from layers **below** it—never above.

```
 +-------------------------------------+
 |  App shell / gate                   |  App.vue auth gate -> LoginView | AppShell
 |  src/App.vue, src/main.ts           |
 +-------------------------------------+
 |  Features                           |  Feature modules (SFCs + composables)
 |  features/{auth,shell,notes,settings}/ |
 +-------------------------------------+
 |  Design system                      |  Ds* components, icons, generated tokens
 |  design-system/                     |
 +-------------------------------------+
 |  Services                           |  HTTP client + auth/notes/settings API wrappers
 |  services/{http.ts,auth.ts,notes.ts,noteEvents.ts,settings.ts} |
 +-------------------------------------+
```

There is **no `types/`, `config/`, `utils/`, `store/`, or `router/` directory** in this tree. Pure helpers live inside their feature (e.g. `features/notes/noteMockHelpers.ts`); types are declared alongside the code that uses them (e.g. `features/shell/headerTypes.ts`).

### Dependency Rules

| Layer | May Import From |
|-|-|
| Services | Nothing from app (external libs only) |
| Design system | Services-free; self-contained tokens/components/icons |
| Features | Design system, Services |
| App shell / gate | Features, Services |

**No service↔store cycle.** `services/http.ts` never imports the auth composable. Instead, the auth composable injects token/refresh callbacks via `setAuthHooks({ getToken, onRefresh })`, so `http.ts` stays dependency-free and the 401 refresh-and-retry policy is wired without an import cycle.

---

## Backend (`backend/app/`)

### Layer Map

Layers are listed bottom-up. Code may only import from layers **below** it. The backend is not a strict linear stack—several justified cross-layer edges exist (documented below).

```
Main         main.py                          App bootstrap, lifespan, CORS, routers
  ^
Routers      routers/{auth,notes,settings,health}   API endpoint handlers (thin delegation)
  ^
Services     services/                        Notes/auth/settings orchestration, health checks, note-event broker/streams
  ^
Auth         auth/                            JWT, OIDC, dependencies
  ^
Schemas      schemas/                         Pydantic request/response models
  ^
Models       models/                          SQLAlchemy ORM (User, Note, NoteTag)
  ^
Database     database/                        Engine, sessions, init, seed
```

`utils/markdown.py` sits outside the stack as a leaf helper (no app imports); services may use it.

### Dependency Rules

| Layer | May Import From |
|-|-|
| Database | Nothing (foundation) |
| Models | Database (Base class only) |
| Schemas | Nothing from app (standalone Pydantic models) |
| Utils | Nothing from app (pure helpers) |
| Auth | Models, Schemas, Database |
| Services | Auth, Schemas, Models, Database, Utils |
| Routers | Auth, Services, Models, Schemas, Database |
| Main | All layers (wiring only) |

### Known Cross-Layer Edges

| Edge | Reason |
|-|-|
| `models/models.py` → `database` | Models import `Base` for declarative ORM—unavoidable SQLAlchemy pattern |
| `database/seed.py` → `auth`, `models` | Seed needs `get_password_hash` for default user passwords and the `User`/`Note` ORM classes to create default rows; runs on startup |
| `main.py` → `auth/oidc_validator` | Lifespan imports the OIDC validator singleton for `close()` on shutdown |
| `main.py` → `services/note_events`, `services/note_event_streams` | Lifespan starts a per-worker Postgres `LISTEN` consumer (`create_note_event_listener`) on startup and closes active SSE streams (`note_event_stream_manager.close_all()`) before stopping the consumer on shutdown |

### Routers And Services

Routers are thin dependency wiring; CRUD and auth business logic lives in services:

- **`routers/notes.py`**: dependency wiring plus calls into `services/notes_service.py` for CRUD; keeps the SSE stream — `GET /api/notes/events` (`stream_note_events`) returns a `StreamingResponse` of Server-Sent Events, backed by the note-event broker and stream manager in `services/`
- **`services/notes_service.py`**: CRUD orchestration (list/create/update/delete/get), note-ID generation, ORM→schema conversion, markdown processing, ownership 404s, and `SQLAlchemyError` → 500 handling
- **`routers/auth.py`**: dependency wiring plus calls into `services/auth_service.py` for login, token refresh, and user lookup
- **`services/auth_service.py`**: login credential validation, token issuance/refresh, and `get_user_by_username`
- **`routers/settings.py`**: settings endpoints that depend on the current user and DB session, then delegate account info, password change, full-notes export, and account deletion to `services/settings_service.py`
- **`services/settings_service.py`**: account info, local-password changes, account deletion (cascades notes via the ORM relationship), export filename sanitization, batched note collection, ZIP entry generation, and streaming export responses

The `services/` package also holds health checks and the note-event broker: `health_service.py` (DB connectivity), `note_events.py` (an in-process note-event broker + per-worker Postgres `LISTEN` consumer on channel `notes_events`), and `note_event_streams.py` (`NoteEventStreamManager`, coordinating active SSE streams).

### Dependency Injection

Protected routes use FastAPI's `Depends()` to pull `get_current_user` (Auth layer) and `get_async_db` (Database layer). `get_current_user` resolves via: Bearer token → try local JWT → fall back to OIDC → return User model. OIDC users are auto-created on first login.

---

## Cross-Cutting Concerns

### Authentication

Two auth providers unified behind a single dependency:

- **Local JWT**: HS256 tokens (30min access, 7-day refresh), passwords hashed with bcrypt
- **OIDC (Authelia)**: Opaque tokens validated via userinfo endpoint, JWT tokens validated via JWKS

Frontend: the `useAuth()` composable is a module-level singleton holding the session (`accessToken`, `refreshToken`, `user`), persisted to `localStorage` under `pm_auth` via `@vueuse/core`'s `useStorage`. `App.vue` calls `restoreSession()` on mount (validating via `GET /auth/me`) before revealing `LoginView` or `AppShell`. `services/http.ts` performs a single refresh-and-retry on a `401`, deduping concurrent refreshes via a shared promise.

Backend: `get_current_user` dependency tries local JWT first, then OIDC. All endpoints enforce user ownership (`Note.user_id == current_user.id`).

### Error Handling

**Frontend**: a single `ApiError` class in `services/http.ts` carries the HTTP `status` plus a `detail` string parsed from the backend's `{ detail }` body. Non-API failures surface as plain reactive `error` state on the relevant composable/SFC (e.g. `useAuth`'s `error` ref).

**Backend**: `HTTPException` for expected errors. Custom handlers in `main.py` return structured JSON for unhandled exceptions.

### Markdown Processing

The backend owns title/H1 handling in `utils/markdown.py`: a `MarkdownService` class (exposed as the `markdown_service` singleton) with `extract_title`, `format_content`, `remove_h1`, and `create_empty_note` methods, applied when notes are created or updated.

The frontend processes markdown for **display only**, against notes fetched from the backend:

- `features/notes/noteMockHelpers.ts` — pure helpers including `extractTitle` and `stripTitle` (strips the leading H1 before rendering).
- `features/notes/markdownRender.ts` — `renderMarkdownBody()` parses with `marked` (GFM), rewrites `language-mermaid` fences into `<div class="mermaid">`, then sanitizes with `dompurify` (allowing GFM task-list `input` elements). No mermaid runtime is wired — mermaid blocks are emitted as markup only.

The notes list is fetched from the backend (`GET /api/notes/` via `useNotes`), so the frontend and backend title/H1 handling round-trip through `extract_title`/`remove_h1` and `stripTitle`/`extractTitle` must stay in sync — use the `parchmark-markdown-sync` skill after editing either side.

---

## Dependency Rules (Summary)

1. **Import downward only.** Higher layers may import from any lower layer. Lower layers must not import from higher layers.
2. **Minimize cross-feature imports.** Frontend features may import from sibling features, but keep these unidirectional.
3. **Keep schemas pure.** Backend `schemas/` has zero internal dependencies; frontend types are declared alongside their feature.
4. **Helpers are leaf nodes.** Pure helper modules (e.g. `noteMockHelpers.ts`) depend only on the standard library or external packages—never on services or other features.
5. **`http.ts` stays import-free of the app.** The auth composable injects token/refresh hooks via `setAuthHooks()` rather than `http.ts` importing the store, so the HTTP client has no inbound feature dependency.

New cross-layer dependencies require explicit justification and must be documented in this file.

---

## Data Flow

### Request Lifecycle (auth + notes CRUD)

The paths that reach the backend are authentication (above) and note list/create/update/delete calls:

```
User action (login / app mount)
    → Vue SFC or App.vue gate
    → useAuth() composable (login / restoreSession / refresh)
    → services/auth.ts wrapper
    → services/http.ts (attaches Bearer token, single refresh-and-retry on 401)
    → FastAPI router
    → Depends(get_current_user) + Depends(get_async_db)
    → JSON response
    → reactive refs update; gate reveals LoginView or AppShell
```

The notes list is fetched from the backend on mount: `AppShell.vue` calls `useNotes().fetchNotes()` -> `services/notes.ts` `listNotes()` -> `GET /api/notes/` -> `useNotes` maps each `NoteDTO` to `NoteMock` (ISO timestamps -> epoch ms, normalized `tags` copied from `NoteResponse`). `SidebarDrawer.vue` surfaces the `loading`/`error` refs and emits `retry` to refetch. `AppShell.vue` also persists note create, content save, delete, and tag add/remove through `useNotes()` mutation wrappers; tag edits send the full replacement tag set through `PUT /api/notes/{note_id}`. Note selection, search/tag filters, copy, and single-note export stay local to the browser. The settings view uses `useSettings()` -> `services/settings.ts` -> `GET /api/settings/export-notes` for full-notes ZIP downloads. While authenticated, `AppShell.vue` also opens the note-events SSE stream (`useNoteEvents` -> `services/noteEvents.ts` -> `requestStream` -> `GET /api/notes/events`): each created/updated/deleted event schedules one debounced `fetchNotes`, so a change made in any session refreshes the canonical list, and a refreshed list that drops the active note reselects the newest remaining one. The stream tears down on unmount and on sign-out and reopens on re-authentication.

### State Management

No store library. State is held in Vue reactivity:

| Holder | Persisted | Ephemeral |
|-|-|-|
| `useAuth()` (composable singleton) | `pm_auth` = `{ accessToken, refreshToken, user }` (localStorage via `useStorage`) | `error`, `pending`, `refreshPromise` |
| `useNotes()` (composable singleton) | Nothing | `notes`, `loading`, `error`, `creating`, `updating`, `deletingId`, `mutationError` (reset on reload; `fetchNotes()` populates from `GET /notes/`) |
| `useSettings()` (composable singleton) | Nothing | `userInfo`, `loading`, `error`, `changingPassword`, `passwordError`, `passwordSuccess`, `exportingNotes`, `exportError`, `deletingAccount`, `deleteError` |
| `AppShell.vue` (local refs) | Nothing | `activeId`, `mode` (read/edit), `search`, `activeTags`, `menuOpen`, `navOpen`, `settingsActive` |
| Theme (`AppShell.vue`) | `pm_theme` = `"light"` \| `"dark"` (localStorage; read on init, written on change, mirrored to the `data-theme` attribute) | `theme` ref |

`useAuth()` returns the same shared module-level refs on every call. Per-view UI state stays local to the SFC that owns it.

---

## Infrastructure

CI runs on Forgejo (origin). Tests must pass before images build. Deploy is automated via k3s `kubectl rollout restart` on push to main. Compose files, make targets, and CI workflow details are catalogued in [AGENTS.md](../AGENTS.md).
