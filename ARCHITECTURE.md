# Architecture

> Domain map, layer dependencies, and cross-cutting concerns for ParchMark.

ParchMark is a full-stack markdown note-taking app with two domains: a React frontend (`ui/`) and a FastAPI backend (`backend/`). They communicate exclusively over a JSON REST API (`/api/*`). For API endpoints, environment variables, commands, and coding patterns, see [AGENTS.md](./AGENTS.md).

```
┌──────────────────────┐         ┌──────────────────────┐
│       Frontend       │  HTTP   │       Backend        │
│   React / Vite / TS  │ ──────► │  FastAPI / SQLAlchemy │
│   localhost:5173     │ ◄────── │  localhost:8000       │
└──────────────────────┘  JSON   └──────────────────────┘
                                          │
                                          ▼
                                 ┌────────────────┐
                                 │   PostgreSQL    │
                                 │   + pgvector    │
                                 └────────────────┘
```

---

## Frontend (`ui/src/`)

### Layer Map

Layers are listed bottom-up. Code may only import from layers **below** it—never above.

```
 ┌─────────────────────────────────────┐
 │  Router                             │  Route definitions, loaders, lazy imports
 │  router.tsx                         │
 ├─────────────────────────────────────┤
 │  Features                           │  Feature modules (components, actions, hooks)
 │  features/{auth,notes,settings,ui}/ │
 ├─────────────────────────────────────┤
 │  Stores                             │  Zustand state (one per feature)
 │  features/*/store/                  │
 ├─────────────────────────────────────┤
 │  Services                           │  HTTP client, markdown service wrapper
 │  services/                          │
 ├─────────────────────────────────────┤
 │  Utils                              │  Error handling, date formatting, scoring
 │  utils/                             │
 ├─────────────────────────────────────┤
 │  Config                             │  API endpoints, env constants, storage keys
 │  config/                            │
 ├─────────────────────────────────────┤
 │  Types                              │  Note, SimilarNote, User interfaces
 │  types/                             │
 └─────────────────────────────────────┘
```

### Dependency Rules

| Layer | May Import From |
|-------|----------------|
| Types | Nothing (leaf) |
| Config | Nothing (environment only) |
| Utils | Types, Config |
| Services | Utils, Config, Types, Stores* |
| Stores | Services, Utils, Config, Types, feature-local utils** |
| Features | Stores, Services, Utils, Config, Types |
| Router | Features, Stores, Services, Config |

\* **Circular dependency: `api.ts` ↔ `useAuthStore`**. The API service imports `useAuthStore` to attach auth tokens to requests; the auth store imports the API service for login/refresh calls. This cycle works because Zustand defers store access—`useAuthStore.getState()` is called inside functions, not at module load time. This pattern is fragile and must not be replicated elsewhere.

\*\* Stores may import from their own feature's `utils/` directory (e.g., `useAuthStore` imports `tokenUtils.ts` and `oidcUtils.ts`). Cross-feature store imports should be avoided.

### Directory Reference

```
ui/src/
├── types/index.ts              # Note, SimilarNote, User
├── config/
│   ├── api.ts                  # API_ENDPOINTS constant
│   ├── constants.ts            # Vite env vars (API_BASE_URL, etc.)
│   ├── storage.ts              # STORAGE_KEYS for localStorage
│   └── oidc.ts                 # OIDC_CONFIG, OIDC_ENDPOINTS
├── utils/
│   ├── errorHandler.ts         # AppError class, handleError()
│   ├── markdown.ts             # MarkdownService (synced with backend)
│   ├── dateFormatting.ts       # Relative/short/full date display
│   ├── dateGrouping.ts         # Group & sort notes by date
│   ├── noteScoring.ts          # "For You" heuristic scoring
│   ├── compactTime.ts          # Compact relative time ("5m", "2h")
│   ├── markdownStrip.ts        # Plain text extraction from markdown
│   └── mermaidInit.ts          # Lazy mermaid diagram loader
├── services/
│   ├── api.ts                  # HTTP client (fetch + auth token injection)
│   └── markdownService.ts      # Thin wrapper over utils/markdown.ts
├── features/
│   ├── auth/
│   │   ├── store/auth.ts       # useAuthStore (Zustand + Immer + Persist)
│   │   ├── components/         # LoginForm, OIDCCallback, UserLoginStatus
│   │   ├── hooks/              # useTokenExpirationMonitor
│   │   └── utils/              # tokenUtils, oidcUtils
│   ├── notes/
│   │   ├── store/notesUI.ts    # useNotesUIStore (edit state)
│   │   ├── actions.ts          # Route actions (create/update/delete)
│   │   ├── components/         # NotesLayout, NoteContent, NotesExplorer
│   │   └── styles/             # notes.css, markdown.css
│   ├── ui/
│   │   ├── store/ui.ts         # useUIStore (palette, sort/filter prefs)
│   │   ├── components/         # Header, CommandPalette, NotFoundPage
│   │   └── styles/             # layout.css
│   └── settings/
│       └── components/         # Settings page
├── components/                 # Shared components (Mermaid, PageTransition)
├── store/index.ts              # Barrel re-export of all feature stores
├── styles/                     # Chakra theme, design tokens, global CSS
├── router.tsx                  # React Router Data Router config
├── App.tsx                     # ChakraProvider + RouterProvider
└── main.tsx                    # Entry point
```

---

## Backend (`backend/app/`)

### Layer Map

Layers are listed bottom-up. Code may only import from layers **below** it. The backend is not a strict linear stack—several justified cross-layer edges exist (documented below).

```
 ┌─────────────────────────────────────┐
 │  Main                               │  App bootstrap, lifespan, CORS, routers
 │  main.py                            │
 ├─────────────────────────────────────┤
 │  Routers                            │  API endpoint handlers
 │  routers/{auth,notes,settings,health}│
 ├─────────────────────────────────────┤
 │  Services                           │  Embeddings, health checks
 │  services/                          │
 ├─────────────────────────────────────┤
 │  Auth                               │  JWT, OIDC, dependencies
 │  auth/                              │
 ├─────────────────────────────────────┤
 │  Schemas                            │  Pydantic request/response models
 │  schemas/                           │
 ├─────────────────────────────────────┤
 │  Models                             │  SQLAlchemy ORM (User, Note)
 │  models/                            │
 ├─────────────────────────────────────┤
 │  Database                           │  Engine, sessions, init, seed
 │  database/                          │
 └─────────────────────────────────────┘
```

### Dependency Rules

| Layer | May Import From |
|-------|----------------|
| Database | Nothing (foundation) |
| Models | Database (Base class only) |
| Schemas | Nothing from app (standalone Pydantic models) |
| Auth | Models, Schemas, Database |
| Services | Database, Models (embeddings is standalone) |
| Routers | Auth, Services, Models, Schemas, Database, Utils |
| Main | All layers (wiring only) |

### Known Cross-Layer Edges

| Edge | Reason |
|------|--------|
| `models/models.py` → `database` | Models import `Base` for declarative ORM—unavoidable SQLAlchemy pattern |
| `database/seed.py` → `auth` | Seed needs `get_password_hash` for default user passwords; runs on startup |
| `main.py` → `auth/oidc_validator` | Lifespan imports the OIDC validator singleton for `close()` on shutdown |

### Fat Routers, Thin Services

Business logic currently lives in routers, not in a services layer:

- **`routers/notes.py`**: CRUD orchestration, ORM→schema conversion, markdown processing, background embedding generation, cosine similarity queries
- **`routers/settings.py`**: filename sanitization, batched streaming export, password change with auth provider checks, cascading account deletion

The `services/` package holds only embeddings, health checks, and the backfill CLI—not general business logic.

### Directory Reference

```
backend/app/
├── database/
│   ├── database.py             # Async engine, session factory, get_async_db()
│   ├── init_db.py              # Table creation, pgvector extension
│   └── seed.py                 # Default users and notes
├── models/
│   └── models.py               # User, Note (with pgvector embedding column)
├── schemas/
│   └── schemas.py              # Pydantic schemas (no model imports)
├── auth/
│   ├── auth.py                 # JWT creation/validation, password hashing
│   ├── dependencies.py         # get_current_user (hybrid JWT + OIDC)
│   └── oidc_validator.py       # OIDC token validation, discovery caching
├── services/
│   ├── embeddings.py           # OpenAI embedding generation, cosine similarity
│   ├── health_service.py       # DB connectivity check
│   └── backfill.py             # CLI: backfill embeddings for existing notes
├── routers/
│   ├── auth.py                 # /api/auth/* endpoints
│   ├── notes.py                # /api/notes/* endpoints (+ background embedding)
│   ├── settings.py             # /api/settings/* endpoints (streaming ZIP export)
│   └── health.py               # /api/health endpoint
├── utils/
│   └── markdown.py             # Title extraction, H1 removal (synced with frontend)
├── main.py                     # FastAPI app, lifespan, CORS, exception handlers
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

Frontend: `useAuthStore` manages token state with Zustand persistence. `useTokenExpirationMonitor` hook auto-refreshes before expiry.

Backend: `get_current_user` dependency tries local JWT first, then OIDC. All endpoints enforce user ownership (`Note.user_id == current_user.id`).

### Error Handling

**Frontend** has two error types:

| Type | Location | Purpose |
|------|----------|---------|
| `AppError` | `utils/errorHandler.ts` | General error normalization via `handleError()` |
| `ApiError` | `services/api.ts` | API-specific errors with HTTP `status` and `data` |

These are separate hierarchies—`ApiError` is not converted to `AppError`.

**Backend**: `HTTPException` for expected errors. Custom handlers in `main.py` return structured JSON for unhandled exceptions.

### Markdown Processing

Both domains implement the same operations and must stay in sync:

| Operation | Frontend (`utils/markdown.ts`) | Backend (`utils/markdown.py`) |
|-----------|-------------------------------|-------------------------------|
| Extract title | `extractTitle(content)` | `extract_title(content)` |
| Remove first H1 | `removeH1(content)` | `remove_h1(content)` |
| Format content | `formatContent(content)` | `format_content(content)` |
| Create empty note | `createEmptyNote(title)` | `create_empty_note(title)` |

The frontend includes shared test cases (`markdownTestCases`) to verify parity.

### Embeddings & Similarity

Optional feature—silently degrades when `OPENAI_API_KEY` is absent.

```
Note created/updated
    → Background task: generate embedding via OpenAI
    → Store as pgvector Vector(1536) on Note model

GET /api/notes/{id}/similar
    → cosine_distance() query in PostgreSQL
    → Return ranked similar notes

Command Palette "For You"
    → Blend heuristic score (recency + frequency) with similarity score
    → 0.4 * heuristic + 0.6 * similarity (when available)
```

---

## Dependency Rules (Summary)

1. **Import downward only.** Higher layers may import from any lower layer. Lower layers must not import from higher layers.
2. **Minimize cross-feature imports.** Frontend features may import from sibling features, but keep these unidirectional.
3. **Keep schemas/types pure.** Backend `schemas/` and frontend `types/` have zero internal dependencies.
4. **Utils are leaf nodes.** Utility modules depend only on standard library, config constants, or external packages—never on services, stores, or features.
5. **Stores may import feature-local utils.** A store within `features/X/store/` may import from `features/X/utils/`, but not from other features' internals.

New cross-layer dependencies require explicit justification and must be documented in this file.

---

## Data Flow

### Request Lifecycle

```
User action (keyboard/click)
    → React component
    → Route action (useFetcher.submit) or store action
    → services/api.ts (attaches Bearer token, auto-refresh on 401)
    → FastAPI router
    → Depends(get_current_user) + Depends(get_async_db)
    → SQLAlchemy async query
    → JSON response
    → Component re-renders via loader revalidation or store update
```

Route loaders fetch data before render. Components access data via `useLoaderData()`. Mutations use route actions via `useFetcher().submit()`, which automatically revalidate affected loaders.

### State Management

Three Zustand stores, each persisted to localStorage:

| Store | Persisted | Ephemeral |
|-------|-----------|-----------|
| `useAuthStore` | `isAuthenticated`, `user`, `token`, `refreshToken`, `tokenSource` | `error`, `oidcLogoutWarning` |
| `useUIStore` | `notesSortBy`, `notesSortDirection`, `notesGroupByDate` | `isPaletteOpen`, `paletteSearchQuery`, `notesSearchQuery` |
| `useNotesUIStore` | Nothing | `editedContent` |

Route loaders fetch server data; stores hold client-side UI state. This separation avoids duplicating server state in client stores.

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
