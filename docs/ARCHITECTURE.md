# Architecture

> Domain map, layer dependencies, runtime contracts, and cross-cutting concerns for ParchMark. Implementation plans should be able to rely on this document without re-deriving the system from source; where a detail is deliberately delegated (commands, env-var values, endpoint catalogs), the pointer says where it lives.

ParchMark is a full-stack markdown note-taking app with two domains: a Vue 3 frontend (`ui/`) and a FastAPI backend (`backend/`). They communicate over `/api/*`; most calls are JSON REST endpoints, the settings notes export returns a ZIP download, and live note refresh rides an authenticated Server-Sent Events stream. Auth, note CRUD, tag edits, full-notes export, and live note-events refresh are wired to the backend. Copy and single-note export stay browser-only. For API endpoints, environment variables, commands, and coding patterns, see [AGENTS.md](../AGENTS.md).

```
+----------------------+         +-----------------------+
|       Frontend       |  HTTP   |       Backend         |
|    Vue 3 / Vite / TS  | ------> |  FastAPI / SQLAlchemy |
|    localhost:5173     | <------ |  localhost:8000       |
+----------------------+ JSON/ZIP +-----------------------+
                          /SSE             |
                                           v
                                  +-----------------+
                                  |   PostgreSQL    |
                                  |  (also the SSE  |
                                  |   event source) |
                                  +-----------------+
```

In production both containers run on k3s behind `notes.engen.tech`; nginx in the frontend container proxies `/api/` same-origin to the backend service. See [Runtime Topology](#runtime-topology--configuration).

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

There is **no `types/`, `config/`, `utils/`, `store/`, or `router/` directory** in this tree. Pure helpers live inside their feature (e.g. `features/notes/noteMockHelpers.ts`); types are declared alongside the code that uses them (e.g. `features/shell/headerTypes.ts` holds the shared `NoteMode`/`NoteMenuAction` string-literal union types — the topbar/menu/shell contract in one file).

### Dependency Rules

| Layer | May Import From |
|-|-|
| Services | Nothing from app (external libs only) |
| Design system | Services-free; self-contained tokens/components/icons |
| Features | Design system, Services |
| App shell / gate | Features, Design system, Services |

**No service↔store cycle.** `services/http.ts` never imports the auth composable. Instead, the auth composable injects token/refresh callbacks via `setAuthHooks({ getToken, onRefresh })` at module load (`useAuth.ts:98-101`), so `http.ts` stays dependency-free and the 401 refresh-and-retry policy is wired without an import cycle.

### Composition Root

`AppShell.vue` is the only holder of shell-wide UI state — eight refs (`activeId`, `mode`, `search`, `activeTags`, `menuOpen`, `navOpen`, `settingsActive`, `draftContent`) plus `theme`. Shell children hold no shared state and are mostly props-down/events-up (`SidebarDrawer` receives all list/filter concerns as props and emits mutations back), with two sanctioned exceptions that read composable singletons directly: `UserFooter` (`useAuth`) and `SettingsView` (`useSettings`). Non-obvious wiring a plan must preserve:

- `main.ts` imports `tokens.css` **before** `base.css` — base.css consumes variables tokens.css defines; new global CSS keeps that order.
- `App.vue`'s gate is three-state: an `aria-busy` themed blank frame until `restoreSession()` resolves, then `LoginView` or `AppShell` — deliberate anti-flash so an authenticated reload never shows the login form.
- On mount the shell fetches notes and selects the **newest by `updatedAt`**; the SSE stream starts once the initial fetch **settles** (`fetchNotes` never rejects — failures land in its `error` ref, so the stream opens even when the first list load failed) and only while authenticated (a `watch(isAuthenticated)` handles re-auth start and sign-out stop).
- A `watch(notes)` invariant repairs dangling selection: if a refresh drops the active note, reselect the newest remaining, clear the draft, force read mode.
- Draft save is gated by `canSaveDraft` = dirty AND `trim().length >= 4` AND not already saving.
- Tag edits send the **full replacement set**, then prune active tag filters that no longer exist.
- Theme lives in `AppShell` (not a composable): `pm_theme` in localStorage, mirrored to `document.documentElement.dataset.theme`, matching the `[data-theme="dark"]` selector the token build emits. A second theme consumer would require extracting it.
- Search matches title+content lowercase substring; the tag filter is OR-any, not AND. Both compose in one `filteredNotes` computed, newest-first.

### Design-Token Pipeline

`design-system/tokens/build.mjs` (style-dictionary) runs **two separate builds** — light (`primitives.json` + `semantic.json` → `:root`) and dark (`semantic.dark.json` alone → `[data-theme="dark"]`) — because merging sources would deep-merge multi-layer shadow arrays per-index instead of replacing them. A custom name transform reads `$extensions["com.parchmark.cssName"]` for short var names. Output is concatenated into the **committed, generated** `design-system/tokens.css`. `npm run build` regenerates tokens first, so stale tokens cannot ship — but dev serves the committed file, so editing token JSON without `npm run build:tokens` shows stale values locally. The dark theme holds only overrides: a new token needs a light entry and, when theme-dependent, a dark override. Icons come from a `createIcon(...)` render-function factory with built-in a11y (hidden unless `title` is passed); no icon library.

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

`utils/markdown.py` and `version.py` sit outside the stack as leaf modules (no app imports); services and main may use them.

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

Routers are thin dependency wiring; CRUD and auth business logic lives in services. **Endpoint handler bodies never raise** (sole exception: `routers/health.py`, 503 on DB failure); `routers/notes.py` additionally raises a 401 inside its router-local SSE auth dependency. Domain services own all other `HTTPException` raising:

- **`routers/notes.py`**: dependency wiring plus calls into `services/notes_service.py` for CRUD; keeps the SSE stream — `GET /api/notes/events` returns a `StreamingResponse` of Server-Sent Events (see [Live Note Events](#live-note-events-pipeline))
- **`services/notes_service.py`**: CRUD orchestration, note-ID generation, ORM→schema conversion, markdown processing, ownership 404s, and `SQLAlchemyError` → 500 handling. All functions take `(db, current_user, ...)` and return response schemas; the single ownership gate is `_get_owned_note` (`Note.id == note_id AND Note.user_id == user_id`)
- **`routers/auth.py`** / **`services/auth_service.py`**: login credential validation, token issuance/refresh, user lookup
- **`routers/settings.py`** / **`services/settings_service.py`**: account info, local-password changes, account deletion (ORM cascade), export filename sanitization, ZIP streaming

`services/` also holds `health_service.py` (DB connectivity), `note_events.py` (in-process broker + per-worker `LISTEN` consumer), and `note_event_streams.py` (`NoteEventStreamManager`).

### Dependency Injection

Protected routes use FastAPI's `Depends()` to pull `get_current_user` (Auth layer) and `get_async_db` (Database layer). `get_current_user` resolves via: Bearer token → try local JWT → fall back to OIDC → return User model. OIDC users are auto-created on first login. Sessions are request-scoped; see [Concurrency Model](#concurrency-model).

---

## Data Model & Schema Evolution

### Entities (`backend/app/models/models.py`)

| Entity | Key facts |
|-|-|
| `User` | int autoincrement PK; `username` String(50) unique+indexed; `password_hash` **nullable** (OIDC users); `oidc_sub` String(255) unique+indexed nullable; `auth_provider` defaults `"local"`; table-level CHECK `valid_auth_credentials` (local ⇒ password_hash NOT NULL, oidc ⇒ oidc_sub NOT NULL); `notes` relationship `cascade="all, delete-orphan"` — account deletion cascades in the **ORM**, not via DB FK |
| `Note` | **String(50) PK, app-generated**: `f"note-{epoch_ms}"` in `notes_service.py` (seed rows use literal ids "1"/"2"/"3"); `user_id` FK indexed, **no `ondelete`** (cascade is ORM-side only); `updated_at` via `onupdate=func.now()` |
| `NoteTag` | one row per tag; `note_id` FK **with DB-side `ondelete="CASCADE"`** + `passive_deletes=True`; `UniqueConstraint(note_id, tag)`; CHECK `length(tag) > 0`; ordered by tag |

### Dual-Path Schema Creation (the central invariant)

Two independent mechanisms produce schema, and every migration must tolerate either order:

1. **`Base.metadata.create_all`** runs on **every** startup (`main.py` lifespan → `init_database()`); startup fails fast on error. After it, `seed_database()` seeds `demouser`/`testuser` plus three notes **in any environment, production included** — the gate checks that both default users exist AND `demouser` holds exactly its three seed notes, so a production DB containing only real users still gets seeded.
2. **Alembic** runs only when `APPLY_MIGRATIONS=true` (`backend/scripts/docker-entrypoint.sh` runs `alembic upgrade head` before the app; set true in the full-stack and prod compose files). The run-it-on-one-deployment-only discipline for scaled replicas is convention documented in the entrypoint — the k3s manifests that would prove it live outside the repo.

Consequence: **migrations are brownfield-only deltas.** On a fresh DB, `upgrade head` no-ops through inspector guards and stamps head; `create_all` then builds the current schema. Every migration therefore uses the guard pattern (`_table_exists`/column/index inspection + early return). Migration history conventions (immutable revision ids/filenames/intent; bodies patchable only for dep-removal hygiene, with fresh-DB and stamped-brownfield tests) are defined in the project [CLAUDE.md](../CLAUDE.md) and enforced by the migration test suites.

Alembic's `env.py` overrides `sqlalchemy.url` from `DATABASE_URL` and runs **sync** (psycopg2); the app engine rewrites the same URL to `postgresql+asyncpg://`. The alembic.ini URL is a placeholder.

### Known Fresh-vs-Brownfield Divergences (verified)

- The `valid_auth_credentials` CHECK exists **only on fresh DBs** — no migration creates it (tracked in the tech-debt tracker).
- `ix_users_email` (unique) exists **only on brownfield DBs** — a migration creates it but the model doesn't declare it, so `create_all` omits it. Same migration types `auth_provider` String(20) vs the model's String(50).
- **Greenfield trigger gap:** the note-events NOTIFY trigger is installed only by a migration. A truly fresh deployment (empty DB → stamp head → `create_all`) gets **no live note events** until the trigger function/triggers are installed manually. Production today is brownfield, so the trigger exists.
- Downgrades may legitimately fail on data (e.g. re-NOT-NULLing `password_hash` with OIDC users present).

### Recipe: schema change

1. Edit `models.py` (fresh-DB path). 2. Author a guarded migration chained off the current head. 3. Add a stamped-brownfield integration test under `backend/tests/integration/migrations/` (stamp parent revision on a vanilla `postgres:17` container, upgrade, assert end state — mirror the note-tags migration test). 4. Validate with the `migration-check` skill. Never rely on `create_all` for non-table DDL (triggers, functions, extensions) — only migrations create those, and see the greenfield gap above.

---

## Live Note Events Pipeline

**The database is the producer; services never publish.** A migration installs plpgsql function `notify_notes_events()` plus two AFTER-ROW triggers on `notes`: INSERT/DELETE, and UPDATE **only when title or content actually change** (tag-only edits emit nothing). Payload on channel `notes_events`: `{"user_id": <int>, "kind": "created"|"updated"|"deleted", "note_id": <string>}`. NOTIFY is transactional — rolled-back writes emit nothing. Because the trigger is the source, **every** write path emits (seed, cascades, out-of-band SQL); adding a service-level publish would double-fire.

**Backend chain** (`services/note_events.py` → `note_event_streams.py` → `routers/notes.py`):

- One dedicated asyncpg `LISTEN` connection **per worker**; malformed payloads are logged and dropped.
- The in-process `NoteEventBroker` delivers only to subscribers keyed by `event.user_id`. Each subscriber is a bounded `asyncio.Queue` (max 50); on overflow the broker **force-unsubscribes the slow consumer**, whose SSE loop then exits.
- `GET /api/notes/events` authenticates **once at open** via a dedicated dependency (`HTTPBearer(auto_error=False)` + explicit 401 so missing headers yield 401, never 403); mid-stream token expiry does not close the stream. The loop races queue-get vs shutdown with a 30s timeout: event → `data: {"kind","note_id"}` frame (no `user_id` on the wire); timeout → disconnect re-check + `:heartbeat` comment frame. Response sets `Cache-Control: no-cache` and `X-Accel-Buffering: no` (nginx must not buffer).
- Lifespan is **fail-fast**: if the LISTEN connection cannot start, the worker refuses to boot. Shutdown order is deliberate: close SSE streams → stop listener → close OIDC client.

**Multi-worker semantics:** Postgres NOTIFY fans out to every listening connection, so each worker/replica sees every event and serves only its locally connected SSE clients. No cross-worker bus exists or is needed.

**Cross-user isolation, three enforcement points:** trigger embeds `user_id`; broker delivers per-user; endpoint subscribes as the authenticated user. A full DB-round-trip isolation test exists (`tests/integration/notes/test_cross_user_event_stream_isolation.py`).

**Frontend:** `services/noteEvents.ts` opens the stream via `requestStream` — plain `fetch` + `ReadableStream`, **not `EventSource`**, precisely so the Bearer header can be attached; one refresh-and-retry on 401 applies **at open only**. Hand-rolled SSE parsing ignores comment/heartbeat frames and malformed JSON. `useNoteEvents` is deliberately **not** a module singleton (per-component lifecycle, idempotent start/stop, auto-stop on unmount). Events are hints, not data: the handler calls `useNotes().scheduleRefetch()` — a module-level **200ms trailing debounce** collapsing bursts into one `fetchNotes`; `cancelScheduledRefetch()` runs on sign-out and shell unmount.

**Known gaps (deliberate, tracked):** there is **no auto-reconnect** on either side — a dropped stream stays dead until re-auth or remount (frontend), and a dropped LISTEN connection silently stops events for that worker until restart (backend). Plans touching this subsystem should treat reconnect as unbuilt.

**Recipe — new event kind or source table:** migration (new revision; trigger must embed `user_id`) → payload validation + `NoteEvent` in `note_events.py` → SSE serialization in `routers/notes.py` → frontend `NoteEventKind`/`parseFrame`. The FE type tolerates unknown kinds, so backend-first rollout is safe. Heartbeat/queue limits live in `note_event_streams.py` / `note_events.py` constants; the queue limit and the heartbeat frame string are test-asserted (the 30s interval value itself is not — tests inject their own).

---

## Cross-Cutting Concerns

### Authentication

Two auth providers unified behind a single dependency:

- **Local JWT**: HS256, bcrypt-hashed passwords. Both tokens carry `{sub, exp, type}` where `type` ∈ `access`/`refresh` and is **enforced** — a refresh token can never authenticate a request, an access token can never refresh. Expiries 30min/7d (env-overridable). `SECRET_KEY` is fail-fast at import: missing or <32 chars refuses to boot.
- **OIDC (Authelia)**: opaque tokens (heuristic: not 3 dot-segments, ≥20 chars, optional `OIDC_OPAQUE_TOKEN_PREFIX` gate) validated via the userinfo endpoint with `azp`/`client_id` checks; JWT access tokens validated RS256/JWKS; when audience validation fails as a **mismatch**, the validator retries without `aud` verification and accepts only if the token's `client_id` equals the configured audience — but a token entirely **lacking** an `aud` claim is rejected outright (the retry gate matches the mismatch error text, which the missing-claim error does not contain). Discovery and JWKS are cached 1h behind double-checked `asyncio.Lock`s; `OIDC_DISCOVERY_URL` may differ from the issuer (CDN bypass). One shared `httpx.AsyncClient`, closed by lifespan.

**Resolution order** (`auth/dependencies.py::get_current_user`): local JWT first (failure is a control-flow branch, logged at debug) → OIDC validate → look up by `oidc_sub`, fetching userinfo if claims are missing → **auto-provision** (`auth_provider="oidc"`, `password_hash=None`) with IntegrityError race recovery (rollback + re-query). All expected OIDC failures collapse into a shared 401.

**Statelessness decisions:** refresh mints a new pair but the old refresh token is **not invalidated** (replayable until `exp`); logout proves auth and returns a message — no server-side revocation of any kind. Local login is refused for OIDC-only users (`password_hash IS NULL`).

**Public routes** are an explicit allowlist governed by [core-beliefs.md](design-docs/core-beliefs.md) (belief #2): health endpoints, login, refresh. Adding a public endpoint requires updating that table; enforcement is convention plus per-endpoint 401 tests (no auto-enumerating test exists — verified).

**Frontend:** the `useAuth()` composable is a module-level singleton holding `{accessToken, refreshToken, user}`, persisted to localStorage under `pm_auth` via `useStorage`. `restoreSession()` (App.vue mount) validates via `GET /auth/me` and clears the session on any error; `login()` stores the pair then fetches `/auth/me` (login response carries no user); `logout()` is best-effort then clears unconditionally. Refresh dedup: a module-level `refreshPromise` shares one in-flight refresh across concurrent 401s. `http.ts` owns the retry rule across all three transports (`request`, `requestRaw` for downloads, `requestStream` for SSE): **exactly one refresh + one retry on 401, never for `/auth/refresh` itself** — `isRefreshCall` matches only that exact path, so every other `/auth/*` route still gets the retry. ofetch is created `retry: false` so it cannot double-retry. Refresh failure clears the session and the gate drops to `LoginView` reactively.

**Recipes:** *protected endpoint* — `Depends(get_current_user)` + `Depends(get_async_db)` in the router, logic in a service, every query filtered by `current_user.id`, plus an unauthenticated-401 test; the FE wrapper gets token+refresh for free by using the `http.ts` transports. *Public endpoint* — omit the dependency AND append to the core-beliefs allowlist; if it must never be 401-retried, extend `isRefreshCall`.

### Error Contracts

**Backend, three tiers** (`main.py`):

1. Every `HTTPException` is re-serialized to `{detail, status_code, path}` (headers forwarded, so `WWW-Authenticate` survives). This 3-field shape is **test-pinned** (`tests/integration/test_main.py`) — do not change it.
2. The catch-all handler logs and returns 500 with literal `"Internal server error"`; exception text never reaches the client.
3. There is **no custom validation handler**: Pydantic 422s use FastAPI's default `{"detail": [...]}` — a list, without `status_code`/`path`. Cross-file consequence: the FE's `toApiError` accepts only string `detail`, so 422s surface as bare status text. A plan adding client-visible field errors must add a backend handler or teach the FE to flatten the list.

**Conventions:** domain services own the raising for notes/settings/auth flows (the health router and the auth dependencies raise their own); the fixed DB-error pattern is `except SQLAlchemyError → rollback → log → HTTPException(500, "Database error") from None` (the `from None` deliberately severs the chain). Ownership failures are **404 "Note not found", never 403** — other users' notes are indistinguishable from nonexistent ones. Login/refresh 401 messages are FE-facing contracts.

**Frontend:** all transports throw `ApiError{status, detail}` (transport failures get `status: 0`). Composables keep per-concern `ref<string | null>` error state (`error` vs `mutationError` in `useNotes`; four separate refs in `useSettings`), set via `caught instanceof ApiError ? caught.detail : String(caught)`. A failed refetch leaves existing data untouched. **No runtime `console.*` calls exist in the app source** (the single one in `ui/src` is in the Node-only token build script) — user-visible state is the only channel. SSE errors set a non-blocking `error` ref without touching the notes list.

### Notes & Settings Domain Invariants

- **Title precedence:** on create, a non-blank client `title` is honored; on any content-bearing update the title is **re-derived from content and the client title is ignored**. Title-only updates require omitting content.
- **Tags:** normalized at the schema boundary (strip, drop leading `#`, whitespace→`-`, lowercase, `^[a-z0-9_-]+$`, ≤64, dedupe, sorted) by a single shared validator. `PUT` semantics are full replacement — omitted or explicit-null keeps existing tags, `[]` clears them. Uniqueness is DB-enforced per note.
- **IDs:** `note-<epoch-ms>` app-generated strings; concurrent same-millisecond creates are unguarded (PK collision → 500).
- **Responses:** `NoteResponse` uses literal camelCase field names (`createdAt`/`updatedAt`, ISO strings); after every mutation the note is **re-fetched from the DB** before conversion. Validation floors: content ≥4 chars, title 4-255 — the FE's default new note (`"# Untitled\n\n"`) is sized to clear the floor.
- **Settings:** change-password requires `auth_provider == "local"` and a hash. Delete-account keys off `password_hash`, not provider: hash-bearing accounts must send the verifying password; hash-less (OIDC) accounts accept any ≥4-char string — the FE sends the typed `"DELETE"` confirmation, and the schema's `min_length=4` is exactly what makes that pass. Deletion is the ORM cascade (`db.delete(user)` removes notes and tags).
- **Export:** ZIP is streamed to the client but note content is materialized in memory first; filenames dedupe via a sanitizing counter; `notes_metadata.json` is appended last and **tags are not exported** (the metadata dict is hand-built — new Note fields are silently omitted from export unless added there).
- FE mapping: `useNotes` maps `NoteDTO` → `NoteMock` (epoch-ms timestamps, tags copied verbatim); `NoteMock` has **no title field** — the FE re-derives the title from content with its own `extractTitle`, deliberately ignoring the wire `title` (recorded decision in `useNotes.ts`).

### Markdown Processing

The backend owns title/H1 handling in `utils/markdown.py`: a `MarkdownService` class (exposed as the `markdown_service` singleton); `extract_title` and `format_content` are applied when notes are created or updated (`remove_h1` and `create_empty_note` exist on the service but are currently uncalled). `format_content` is near-identity (strips; only rewrites bare-H1-only content). **Markdown is stored verbatim — there is no server-side sanitization.**

The frontend processes markdown for **display only**: `noteMockHelpers.ts` (`extractTitle`, `stripTitle`, preview/word-count/grouping helpers) and `markdownRender.ts` — `renderMarkdownBody()` strips the H1 (shown separately as the doc title), parses with `marked` (GFM), rewrites `language-mermaid` fences into `<div class="mermaid">` **before** sanitizing, then applies `dompurify` (allowing GFM task-list `input`s). No mermaid runtime is wired.

**Round-trip invariant:** backend `extract_title`/`remove_h1` and frontend `extractTitle`/`stripTitle` must agree on what an H1 title is — use the `parchmark-markdown-sync` skill after editing either side.

### Security Boundaries

- **XSS defense is exactly one funnel:** DOMPurify over marked output in `markdownRender.ts`, consumed via `v-html` only in `MarkdownProse.vue`. The backend stores user markdown verbatim. Any new render surface must route through `renderMarkdownBody` or re-sanitize.
- **No security headers** are set anywhere (no CSP, X-Frame-Options, X-Content-Type-Options — verified in both nginx confs); **no rate limiting** exists on login, refresh, or anything else (no middleware, no nginx `limit_req`). Plans must not assume either.
- **Tokens live in localStorage; there are no cookies**, hence no CSRF surface by construction. The SSE stream authenticates via `fetch`+`ReadableStream` specifically because `EventSource` cannot send an Authorization header.
- **CORS** (`ALLOWED_ORIGINS`, credentialed, 5 methods) matters in dev; in production nginx serves `/api/` same-origin so CORS is mostly inert.
- **Tenant isolation:** every note query filters by `current_user.id` (single gate `_get_owned_note`; 404 masking); the event stream isolates per-user at three layers (see pipeline section). These are core-beliefs invariants with dedicated tests.
- Export filenames pass a sanitizer before entering the ZIP; OIDC validation checks `aud`/`azp`/`client_id` against `OIDC_AUDIENCE`.

### Concurrency Model

- **Backend is fully async, one process per container** (uvicorn is started without a `workers` arg; horizontal scale = k8s replicas). Each process has its own DB pool (`pool_pre_ping=True`, `pool_recycle=3600`), its own LISTEN connection, and its own in-process broker.
- **DB sessions are request-scoped** via `Depends(get_async_db)`; services receive the session and own transaction boundaries (commit + rollback-on-error per the fixed pattern). Module-level session construction is prohibited (tracked convention).
- The SSE endpoint holds its subscription for the stream lifetime — and because its auth dependency takes a request-scoped `Depends(get_async_db)`, that session stays checked out until the stream closes: every connected SSE client consumes DB pool capacity. Heartbeats bound disconnect detection at ≤30s.
- `MarkdownService` is a stateless singleton. `NoteEventStreamManager` keys shutdown events **per event loop** (pytest workers create several).
- Frontend: one shared `refreshPromise` dedupes token refresh across concurrent 401s; `scheduleRefetch`'s 200ms debounce is module-level in `useNotes`.

---

## Dependency Rules (Summary)

1. **Import downward only.** Higher layers may import from any lower layer. Lower layers must not import from higher layers.
2. **Minimize cross-feature imports.** Frontend features may import from sibling features, but keep these unidirectional.
3. **Keep schemas pure.** Backend `schemas/` has zero internal dependencies; frontend types are declared alongside their feature.
4. **Helpers are leaf nodes.** Pure helper modules (e.g. `noteMockHelpers.ts`) depend only on the standard library, external packages, or their own feature's local types—never on services or other features.
5. **`http.ts` stays import-free of the app.** The auth composable injects token/refresh hooks via `setAuthHooks()` rather than `http.ts` importing the store, so the HTTP client has no inbound feature dependency.

New cross-layer dependencies require explicit justification and must be documented in this file.

---

## Data Flow

### Request Lifecycle (auth + notes CRUD)

```
User action (login / app mount)
    → Vue SFC or App.vue gate
    → useAuth() composable (login / restoreSession / refresh)
    → services/auth.ts wrapper
    → services/http.ts (attaches Bearer token, single refresh-and-retry on 401)
    → FastAPI router
    → Depends(get_current_user) + Depends(get_async_db)
    → service function (owns logic, transactions, and HTTPExceptions)
    → JSON response
    → reactive refs update; gate reveals LoginView or AppShell
```

The notes list is fetched from the backend on mount: `AppShell.vue` calls `useNotes().fetchNotes()` → `services/notes.ts` `listNotes()` → `GET /api/notes/` → `useNotes` maps each `NoteDTO` to `NoteMock`. `SidebarDrawer.vue` surfaces the `loading`/`error` refs and emits `retry`. `AppShell.vue` persists note create, content save, delete, and tag add/remove through `useNotes()` wrappers. Note selection, search/tag filters, copy, and single-note export stay local to the browser. The settings view uses `useSettings()` → `GET /api/settings/export-notes` for ZIP downloads. Live refresh rides the note-events stream (see pipeline section): change events schedule one debounced `fetchNotes`, and a refreshed list that drops the active note reselects the newest remaining one.

**Scale ceiling (intentional):** the note list is fetched **unpaginated** and search/tag filtering is **client-side only**. There is no backend search, no pagination, and no server-generated single-note export. Plans that outgrow this ceiling are product-scope changes (tracked as open decisions in the tech-debt tracker).

### State Management

No store library. State is held in Vue reactivity:

| Holder | Persisted | Ephemeral |
|-|-|-|
| `useAuth()` (composable singleton) | `pm_auth` = `{ accessToken, refreshToken, user }` (localStorage via `useStorage`) | `error`, `pending`, `refreshPromise` |
| `useNotes()` (composable singleton) | Nothing | `notes`, `loading`, `error`, `creating`, `updating`, `deletingId`, `mutationError` (reset on reload; `fetchNotes()` populates from `GET /notes/`) |
| `useSettings()` (composable singleton) | Nothing | `userInfo`, `loading`, `error`, `changingPassword`, `passwordError`, `passwordSuccess`, `exportingNotes`, `exportError`, `deletingAccount`, `deleteError` |
| `AppShell.vue` (local refs) | Nothing | `activeId`, `mode` (read/edit), `search`, `activeTags`, `menuOpen`, `navOpen`, `settingsActive`, `draftContent` |
| Theme (`AppShell.vue`) | `pm_theme` = `"light"` \| `"dark"` (localStorage; read on init, written on change, mirrored to the `data-theme` attribute) | `theme` ref |

`useAuth()` returns the same shared module-level refs on every call. Per-view UI state stays local to the SFC that owns it. `useNoteEvents` is intentionally **not** a singleton.

---

## Runtime Topology & Configuration

### Configuration (decentralized, import-time)

There is **no settings object**. Each module reads its own env vars at import time (with `load_dotenv()`), so env must be set before `app.*` is imported. Architectural consequences, not a value catalog (values live in [AGENTS.md](../AGENTS.md)):

- `DATABASE_URL` is validated postgresql-only and rewritten to `postgresql+asyncpg://` for the app engine (`database/database.py`); alembic uses the sync URL.
- `SECRET_KEY` refuses to boot when missing/short (`auth/auth.py`).
- `ALLOWED_ORIGINS` drives CORS (`main.py`); OIDC vars are read by `oidc_validator.py`; `HOST`/`PORT`/`ENVIRONMENT` are dev-server knobs (`__main__.py`).
- Frontend config is **build-time only**: `VITE_API_URL` (default `/api`) plus `__GIT_SHA__`/`__BUILD_DATE__` define-constants from `vite.config.ts`.

### Process Model (production)

- **Backend:** one uvicorn worker per container (no `workers` arg); scale-out is k3s replicas. Non-root user, multi-stage uv build (`backend/Dockerfile.prod`), container HEALTHCHECK curls `/api/health`. The entrypoint runs `alembic upgrade head` iff `APPLY_MIGRATIONS=true` **before** the app starts — enabled on a single deployment path; replicas run false.
- **Frontend:** static Vite `dist/` served by nginx (`ui/Dockerfile`). `USE_HTTPS` selects the conf, and **the two confs differ materially**: `nginx.http.conf` proxies `location /api/` → `http://parchmark-backend:8000` (same-origin; the upstream name must resolve as a service), while `nginx.https.conf` is **static-only** — no `/api` proxy — and assumes an external proxy routes the API. A backend route outside `/api` is unreachable through same-origin serving.
- **CI/CD (Forgejo):** `test.yml` (UI: Node 24 lint+tests; backend: ruff/format/mypy/pytest against DinD) and `deploy.yml` (push to main: build both images with `GIT_SHA`/`BUILD_DATE`, tag `latest` + `sha-<7>`, push to the **cluster-internal** Forgejo registry, `kubectl rollout restart`). **Verified caveat: `deploy.yml` has no `needs:` dependency on `test.yml`** — the "tests gate images" ordering is convention/timing, not enforced. Rollback = repin a `sha-` tag on the k3s Deployment.
- **Out of repo:** k3s manifests (Deployments, ingress, secrets, replica counts, runtime env). Adding a backend env var requires a manifest change no PR here can make. `docker-compose.prod.yml` + `deploy/update.sh` are the retired pre-k3s path — reference only.

### Observability & Versioning

- Logging is `logging.basicConfig(level=INFO)` plain text; per-module `getLogger(__name__)`. **No request IDs, no structured logging, no metrics, no tracing.** Secrets-out-of-logs is convention (verified: no token/password interpolation today), not enforced by tests.
- Two health endpoints with different consumers: `GET /health` (liveness + version, no DB; used by the deploy verify step in-pod) and `GET /api/health` (DB `SELECT 1`, 503 on failure; used by container/compose healthchecks).
- Version identity: images bake `GIT_SHA`/`BUILD_DATE`; **`APP_VERSION` is never passed by CI, so prod reports `version: "dev"`** — `gitSha` is the only trustworthy identity field. The API namespace is unversioned (`/api/*`); FE/BE compatibility is same-repo, same-deploy.
- Startup is fail-fast (DB init or LISTEN failure aborts boot) — a crash-looping pod is the intended failure mode for broken config.

---

## Testing Architecture & CI-Pinned Contracts

### Backend

`pyproject.toml` bakes the gates into `addopts`: parallel xdist (`-n auto`), strict markers/config, and **coverage ≥90% on every pytest run**. Coverage must keep `concurrency = ["thread", "greenlet"]` — removing it silently under-reports async coverage and fails the gate. Each xdist worker gets its own `postgres:17` testcontainer built with **`create_all`, not alembic** — so migration behavior is invisible to ordinary tests and needs dedicated stamped-brownfield tests. Per-test isolation is `DELETE FROM` (not TRUNCATE, to avoid lock conflicts with the async pool). The `client` fixture patches `init_database` and the note-event listener out of the lifespan — **any new lifespan side-effect must be similarly patchable or every client-based test hangs.** Canonical fixtures: `client`, `sample_user`, `auth_headers` (real HS256 tokens), `sample_note`, `multiple_notes`.

### Frontend

Vitest + `@vue/test-utils` (jsdom), `pool: "forks"` with `fileParallelism: false` — test files run serially because module singletons make parallel files unsafe. Coverage v8, 90% on all four axes. Singleton isolation patterns: `useAuth.test.ts` uses `vi.resetModules()` + fresh imports (`ApiError` must be re-imported from the same fresh module or `instanceof` fails); everything else mutates the shared refs in `beforeEach`.

### Contract suites that pin architecture and docs

These are permanent regression gates, not feature tests:

- **Docs sweep** (`tests/integration/test_f21_docs_sweep.py`): scans the whole repo for nine retired-feature literals outside a whitelist, and **pins doc paths and content** — `docs/ARCHITECTURE.md` (this file) and `docs/design-docs/core-beliefs.md` must exist at these exact paths with certain retired headings/terms absent. Doc edits can fail CI on wording alone; run this suite (Docker-free) after editing either file.
- **Migration pins**: brownfield replay suites stamp a vanilla container at a parent revision and upgrade, asserting end state; static greps keep retired dependencies out of migration sources. Together they implement the CLAUDE.md migration-patching rules.
- **Absence/removal contracts**: removed endpoints must 404 and their path strings must stay out of router sources; app-boot tests assert the backend boots with retired vendor config unset.

**Keep-green checklist for plans:** new backend code lands with ≥90% coverage or the default addopts fail; new lifespan wiring must be conftest-patchable; doc edits → run the docs sweep; new migrations → add a stamped-brownfield test; UI files count against thresholds immediately and must be `*.test.ts` under `src/`.

---

## Extension Recipes

Architectural checkpoints (not command lists — commands live in AGENTS.md):

| Change | Touch, in order |
|-|-|
| Protected endpoint | `schemas/` → `services/x_service.py` (owns logic + HTTPExceptions + rollback pattern) → thin `routers/` wrapper → 401 test + feature tests → FE `services/*.ts` wrapper (transports give token+refresh free) → composable per-concern error refs |
| Public endpoint | As above, minus auth dependency; **must** be added to the core-beliefs allowlist; note `http.ts` skips the 401 refresh-retry only for the exact `/auth/refresh` path — other routes (including `/auth/*`) are still retried |
| New Note field | `models.py` → guarded migration + stamped-brownfield test → `schemas` → `_note_to_response` → `NoteDTO` → `mapDtoToNote` → `NoteMock`; decide export inclusion explicitly (the export metadata dict silently omits new fields) |
| New settings action | `settings_service` fn → router wrapper → `services/settings.ts` → `useSettings` ref-pair (`xing` flag + `xError`) mirroring existing quadruples |
| New event kind/table | New migration (trigger embeds `user_id`) → payload validation in `note_events.py` → SSE serialization → FE `parseFrame`/kind union (backend-first rollout is safe) |
| New view/panel | `xActive` ref + open/close handlers in AppShell (clear draft, mutationError, navOpen, menuOpen — mirror `openSettings`) → `v-else-if` branch beside SettingsView → null the state in `selectNote` |
| New Ds component / token / icon | SFC in `design-system/components/` consuming only `var(--token)`; token = semantic.json entry (+ dark override) with `cssName` → `npm run build:tokens` → commit regenerated tokens.css; icon = `createIcon(...)` export |
| New backend env var | `os.getenv` in the owning module (import-time!) → AGENTS.md env table → k3s manifest change (out of repo) |
| Tag rule change | `normalize_tag` in `schemas.py` only — both create and update validators delegate to it |
| Migration | Never edit an existing revision (CLAUDE.md conventions); new guarded revision + brownfield test + `migration-check` skill |

---

## Known Gaps & Sharp Edges (verified, current)

Deliberate simplifications and latent hazards a plan should treat as facts, not surprises:

- **No SSE reconnect on either side** (frontend stream and backend LISTEN connection); recovery is re-auth/remount or pod restart.
- **Greenfield deployments get no note-events trigger** (migration-only DDL vs `create_all` bootstrap).
- **422 responses don't match the pinned error shape**, and the FE renders them as bare status text.
- **`deploy.yml` doesn't wait for `test.yml`** — the test gate is convention, not CI-enforced.
- **No rate limiting, no security headers/CSP** anywhere.
- **Seeding runs in every environment**, production included; seeded IDs are non-standard (`"1"`,`"2"`,`"3"`).
- **Fresh-vs-brownfield schema divergences** (CHECK constraint, email index, `auth_provider` length).
- **Prod `version` reports `"dev"`** — trust `gitSha` only.
- Note-ID collisions under same-millisecond concurrent creates surface as 500s.

Resolutions and open product decisions are tracked in [docs/exec-plans/tech-debt-tracker.md](exec-plans/tech-debt-tracker.md).
