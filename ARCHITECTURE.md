# Architecture

> Domain map, layer dependencies, and cross-cutting concerns for ParchMark.

ParchMark is a full-stack markdown note-taking app with two domains: a Vue 3 frontend (`ui/`) and a FastAPI backend (`backend/`). They communicate over `/api/*`; most calls are JSON REST endpoints, and the settings notes export returns a ZIP download. In this `parchmark-v2` worktree auth, note CRUD, tag edits, full-notes export, and live note-events refresh are wired to the backend. Copy and single-note export stay browser-only. For API endpoints, environment variables, commands, and coding patterns, see [AGENTS.md](./AGENTS.md).

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

\* **No service↔store cycle.** `services/http.ts` never imports the auth composable. Instead, the auth composable injects token/refresh callbacks via `setAuthHooks({ getToken, onRefresh })`, so `http.ts` stays dependency-free and the 401 refresh-and-retry policy is wired without an import cycle.

### Directory Reference

```
ui/src/
├── main.ts                     # createApp(App).mount("#app"); imports tokens.css + base.css
├── App.vue                     # Auth gate: ready -> LoginView | AppShell
├── vite-env.d.ts
├── services/
│   ├── http.ts                 # ofetch + native-fetch helpers, ApiError, setAuthHooks(), 401 refresh-and-retry (request/requestRaw/requestStream)
│   ├── auth.ts                 # login/refresh/getCurrentUser/logout wrappers
│   ├── notes.ts                # list/create/update/delete wrappers + NoteDTO
│   ├── noteEvents.ts           # Authenticated SSE client (openNoteEventStream) for note-change events
│   └── settings.ts             # account info/password/export wrappers
├── features/
│   ├── auth/
│   │   ├── useAuth.ts          # Composable singleton (session via useStorage "pm_auth")
│   │   └── LoginView.vue       # Two-pane username/password login
│   ├── shell/
│   │   ├── AppShell.vue        # In-app view switching (mode/activeId/settings via refs)
│   │   ├── AppTopbar.vue, SidebarDrawer.vue, UserFooter.vue
│   │   ├── BreadcrumbTrail.vue, OverflowNoteMenu.vue, ReadEditSegment.vue
│   │   ├── SearchBox.vue, TagFilter.vue, ThemeToggleButton.vue
│   │   └── headerTypes.ts
│   ├── notes/
│   │   ├── MarkdownProse.vue   # v-html prose pane with scoped typography
│   │   ├── markdownRender.ts   # marked + DOMPurify rendering
│   │   ├── NoteCard.vue
│   │   ├── useNotes.ts         # Notes store composable singleton (fetch/create/update/delete + status refs + debounced live-event refetch)
│   │   ├── useNoteEvents.ts    # Composable managing the note-events SSE stream lifecycle (start/stop, unmount teardown)
│   │   ├── mockNotes.ts        # NoteMock type + in-memory seed (no longer the list source)
│   │   └── noteMockHelpers.ts  # extractTitle/stripTitle/relTime/groupByTime/...
│   └── settings/
│       ├── SettingsView.vue    # Account details, password change, full-notes ZIP export
│       └── useSettings.ts      # Settings composable singleton (user info/password/export status refs)
├── design-system/
│   ├── base.css                # Static base styles
│   ├── tokens.css              # GENERATED — do not edit by hand
│   ├── tokens/                 # primitives.json, semantic.json, semantic.dark.json, build.mjs
│   ├── components/             # DsMenu.vue, DsSegment.vue, DsToolButton.vue
│   └── icons/index.ts          # createIcon() factory + 18 hand-authored SVG icons
```

---

## Backend (`backend/app/`)

### Layer Map

Layers are listed bottom-up. Code may only import from layers **below** it. The backend is not a strict linear stack—several justified cross-layer edges exist (documented below).

```
Main         main.py                          App bootstrap, lifespan, CORS, routers
  ^
Routers      routers/{auth,notes,settings,health}   API endpoint handlers
  ^
Services     services/                        Health checks + note-event broker/streams
  ^
Auth         auth/                            JWT, OIDC, dependencies
  ^
Schemas      schemas/                         Pydantic request/response models
  ^
Models       models/                          SQLAlchemy ORM (User, Note)
  ^
Database     database/                        Engine, sessions, init, seed
```

### Dependency Rules

| Layer | May Import From |
|-|-|
| Database | Nothing (foundation) |
| Models | Database (Base class only) |
| Schemas | Nothing from app (standalone Pydantic models) |
| Auth | Models, Schemas, Database |
| Services | Database, Models |
| Routers | Auth, Services, Models, Schemas, Database, Utils |
| Main | All layers (wiring only) |

### Known Cross-Layer Edges

| Edge | Reason |
|-|-|
| `models/models.py` → `database` | Models import `Base` for declarative ORM—unavoidable SQLAlchemy pattern |
| `database/seed.py` → `auth` | Seed needs `get_password_hash` for default user passwords; runs on startup |
| `main.py` → `auth/oidc_validator` | Lifespan imports the OIDC validator singleton for `close()` on shutdown |
| `main.py` → `services/note_events`, `services/note_event_streams` | Lifespan starts a per-worker Postgres `LISTEN` consumer (`create_note_event_listener`) on startup and closes active SSE streams (`note_event_stream_manager.close_all()`) before stopping the consumer on shutdown |

### Routers And Services

Most endpoint orchestration lives in routers. Shared backend behavior that must be reused or tested directly lives in services:

- **`routers/notes.py`**: CRUD orchestration, ORM→schema conversion, markdown processing, and the SSE stream — `GET /api/notes/events` (`stream_note_events`) returns a `StreamingResponse` of Server-Sent Events, backed by the note-event broker and stream manager in `services/`
- **`routers/settings.py`**: settings endpoints that depend on the current user and DB session, then delegate account info, password change, and full-notes export to `services/settings_service.py`; account deletion still runs in the router
- **`services/settings_service.py`**: account info, local-password changes, export filename sanitization, batched note collection, ZIP entry generation, and streaming export responses

The `services/` package also holds health checks and the note-event broker: `health_service.py` (DB connectivity), `note_events.py` (an in-process note-event broker + per-worker Postgres `LISTEN` consumer on channel `notes_events`), and `note_event_streams.py` (`NoteEventStreamManager`, coordinating active SSE streams).

### Directory Reference

```
backend/app/
├── database/
│   ├── database.py             # Async engine, session factory, get_async_db()
│   ├── init_db.py              # Table creation
│   └── seed.py                 # Default users and notes
├── models/
│   └── models.py               # User, Note
├── schemas/
│   └── schemas.py              # Pydantic schemas (no model imports)
├── auth/
│   ├── auth.py                 # JWT creation/validation, password hashing
│   ├── dependencies.py         # get_current_user (hybrid JWT + OIDC)
│   └── oidc_validator.py       # OIDC token validation, discovery caching
├── services/
│   ├── health_service.py       # DB connectivity check
│   ├── note_events.py          # Note-event broker + Postgres LISTEN consumer (notes_events)
│   ├── note_event_streams.py   # NoteEventStreamManager: coordinates active SSE streams
│   └── settings_service.py     # Account info, password change, full-notes ZIP export
├── routers/
│   ├── auth.py                 # /api/auth/* endpoints
│   ├── notes.py                # /api/notes/* endpoints (incl. GET /events SSE stream)
│   ├── settings.py             # /api/settings/* endpoints (streaming ZIP export)
│   └── health.py               # /api/health endpoint
├── utils/
│   └── markdown.py             # Title extraction, H1 removal (synced with frontend)
├── main.py                     # FastAPI app, lifespan (starts per-worker note-event LISTEN consumer, closes SSE streams on shutdown), CORS, exception handlers
├── __main__.py                 # uvicorn entry point
└── version.py                  # CalVer version info

backend/
├── tests/                      # Pytest: unit/ and integration/
└── migrations/                 # Alembic schema migrations
```

### Dependency Injection

Protected routes use FastAPI's `Depends()`:

```python
async def endpoint(
    current_user: User = Depends(get_current_user),  # Auth layer
    db: AsyncSession = Depends(get_async_db),         # Database layer
):
```

`get_current_user` resolves via: Bearer token → try local JWT → fall back to OIDC → return User model. OIDC users are auto-created on first login.

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

The backend owns title/H1 handling in `utils/markdown.py` (`extract_title`, `remove_h1`), applied when notes are created or updated.

In this `parchmark-v2` worktree the frontend processes markdown for **display only**, against notes fetched from the backend:

- `features/notes/noteMockHelpers.ts` — pure helpers including `extractTitle` and `stripTitle` (strips the leading H1 before rendering).
- `features/notes/markdownRender.ts` — `renderMarkdownBody()` parses with `marked` (GFM), rewrites `language-mermaid` fences into `<div class="mermaid">`, then sanitizes with `dompurify` (allowing GFM task-list `input` elements). No mermaid runtime is wired in this worktree — mermaid blocks are emitted as markup only.

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

The paths that reach the backend in this worktree are authentication (above) and note list/create/update/delete calls:

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
| `useSettings()` (composable singleton) | Nothing | `userInfo`, `loading`, `error`, `changingPassword`, `passwordError`, `passwordSuccess`, `exportingNotes`, `exportError` |
| `AppShell.vue` (local refs) | Nothing | `activeId`, `mode` (read/edit), `search`, `activeTags`, `menuOpen`, `navOpen`, `settingsActive` |
| Theme (`AppShell.vue`) | `pm_theme` = `"light"` \| `"dark"` (localStorage; read on init, written on change, mirrored to the `data-theme` attribute) | `theme` ref |

`useAuth()` returns the same shared module-level refs on every call. Per-view UI state stays local to the SFC that owns it.

---

## Infrastructure

```
deploy/                       # Production deployment scripts
docker-compose.dev.yml        # PostgreSQL only (local dev)
docker-compose.yml            # Full stack (container testing)
docker-compose.prod.yml       # Production (registry images)
docker-compose.oidc-test.yml  # PostgreSQL + Authelia (OIDC testing)
makefiles/                    # Modular make targets
.forgejo/workflows/           # CI: test.yml (PR gate), deploy.yml (push to main)
```

CI runs on Forgejo (origin). Tests must pass before images build. Deploy is automated via k3s `kubectl rollout restart` on push to main.
