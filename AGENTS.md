Guidance for Claude Code working with the ParchMark codebase. This file is a table of contents — follow links for depth.

## Project at a Glance

**ParchMark** — full-stack markdown note-taking app.

| Layer | Stack |
|-|-|
| Frontend | Vue 3 (`<script setup>` SFCs), TypeScript, Vite, custom DTCG design-token system, Vue composables (no Pinia, no router) |
| Backend | FastAPI, Python 3.13, SQLAlchemy 2.0 (async), JWT + OIDC auth, PostgreSQL |
| Deploy | Docker, Nginx, k3s, Forgejo CI |

Deeper references:
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — domain / layer maps, dependency rules
- [`docs/design-docs/index.md`](docs/design-docs/index.md) — core beliefs, UI design, code patterns, design context
- [`PRODUCTION_DEPLOYMENT.md`](PRODUCTION_DEPLOYMENT.md) — deployment runbook

Domain invariants live in [`docs/design-docs/core-beliefs.md`](docs/design-docs/core-beliefs.md). Tech debt is tracked in `docs/exec-plans/tech-debt-tracker.md`.

## Feature & Bug Workflow

**Every feature or bug fix MUST use a new branch. No exceptions.**

> **Docs-only exception:** If the change touches **only markdown / documentation files** and no code (`.ts`, `.tsx`, `.js`, `.py`, `.yml`, `.json`, etc.), you may commit directly to `main` and skip the PR. The moment any code file is touched, the full branch + PR + CI workflow applies.

### 1. Create a Branch (first step)

```bash
git checkout main
git pull origin main
git checkout -b feat/<short-description>   # or fix/<short-description>
```

- Branch off `main` — never commit directly to `main`
- Worktrees are optional; if you prefer isolation, use `git worktree add .worktrees/<branch> -b <branch>` (`.worktrees/` is gitignored)

The `parchmark-branch-setup` skill automates this.

### 2. Implement & Test

- Run `make test` from the repo root on the branch
- Commit to the feature/fix branch

### 3. Open a PR on Forgejo using `tea`

```bash
git push -u origin <branch-name>
tea pr create --title "PR title" --description "## Summary ..." --base main --head <branch-name>
tea pr view <number>           # check CI status
tea pr merge -s merge <number> # merge after CI passes
```

Use `tea` for all Forgejo PR management. Do **not** use `gh` (GitHub only) or raw `curl`.

### 4. Wait for CI

**Work is NOT complete until CI is green on the PR.** If CI fails, fix on the branch, push again, wait for green.

### 5. Clean up

After merge, delete the local branch. If you used a worktree, `git worktree remove .worktrees/<branch>`.

## Commands

All run from project root. `make help` for the full list.

```bash
# Development
make dev              # all: PostgreSQL + Backend + Frontend
make dev-ui           # frontend only (localhost:5173)
make dev-backend      # backend only (localhost:8000)
make docker-dev       # PostgreSQL container only

# Testing
make test             # full CI pipeline (UI + Backend)
make test-ui-all      # UI: lint + tests
make test-backend-all # Backend: lint + format + types + pytest

# User management
make user-create USERNAME=x PASSWORD=y
make user-list
make user-delete USERNAME=x

# Deployment
make deploy-verify    # production health check
make deploy-ssh       # SSH to production
make deploy-logs      # container logs
```

## Directory Structure

```
parchmark/
├── ui/                  # Frontend (Vue 3)
│   └── src/
│       ├── main.ts      # createApp(App).mount("#app"); imports tokens.css then base.css
│       ├── App.vue      # top-level auth gate: loading → LoginView → AppShell
│       ├── features/    # auth/, shell/, notes/ (feature-first; SFCs + .ts)
│       ├── design-system/  # base.css, tokens.css (generated), tokens/ (DTCG JSON + build.mjs), components/ (Ds*.vue), icons/
│       └── services/    # http.ts (ofetch) + auth.ts + notes.ts (notes API client)
├── backend/             # Backend (FastAPI)
│   └── app/             # auth/, database/, models/, routers/, schemas/, services/
├── makefiles/           # modular make targets
├── deploy/              # production scripts
├── docs/
│   ├── design-docs/     # core beliefs, UI design, code patterns, design context
│   ├── exec-plans/      # completed handoffs, tech-debt-tracker
│   ├── product-specs/   # feature specs
│   └── references/      # external docs, llms.txt
└── .claude/             # skills
```

## API Surface

The full, current API is discoverable at:
- Dev: <http://localhost:8000/docs>
- Prod: <https://assets-api.engen.tech/docs>

Notable non-obvious endpoints: `GET /api/health` (DB + version info).

## Environment Variables

### Frontend (`ui/.env`)
```bash
VITE_API_URL=/api
```

### Backend (`backend/.env`)
```bash
DATABASE_URL=postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
OIDC_ISSUER_URL=https://auth.engen.tech
OIDC_AUDIENCE=parchmark
OIDC_OPAQUE_TOKEN_PREFIX=           # optional: restrict opaque token format (e.g. "authelia_at_")
OIDC_DISCOVERY_URL=                 # optional: separate URL for discovery (e.g. internal cluster DNS)
OIDC_USERNAME_CLAIM=preferred_username
```

### Build-time (Docker)
```bash
GIT_SHA=                            # set at docker build for version info
BUILD_DATE=                         # set at docker build for version info
```

## Testing

| Side | Tooling | Notes |
|-|-|-|
| Frontend | Vitest + `@vue/test-utils` | `mount()`/`shallowMount` Vue SFCs (NOT React Testing Library); `environment: "jsdom"`; tests under `src/` (mixed: beside source and in `__tests__/`), matched by `src/**/*.test.ts` |
| Backend | Pytest + pytest-xdist | Each worker gets its own PostgreSQL (testcontainers); fixtures: `client`, `sample_user`, `auth_headers` |

Coverage floor: **90% frontend, 90% backend** (enforced by config).

Some unit tests (e.g. `TestGetCurrentUser`, `TestDependencyIntegration`) depend on conftest fixtures that need Docker and error locally without it, but pass in CI. Run focused tests without Docker: `cd backend && uv run pytest tests/unit/auth/test_oidc_validator.py -v`.

For code patterns, conventions, and style, see [`docs/design-docs/code-patterns.md`](docs/design-docs/code-patterns.md).

## Gotchas

### Docker Compose files
- `docker-compose.dev.yml` — PostgreSQL only (local dev)
- `docker-compose.yml` — full stack (container testing)
- `docker-compose.prod.yml` — production (GHCR images)
- `docker-compose.oidc-test.yml` — PostgreSQL + Authelia (OIDC integration testing)

### Design system (frontend)
- **DTCG token JSON → CSS pipeline.** Sources in `ui/src/design-system/tokens/`: `primitives.json`, `semantic.json` (light "Parchment"), `semantic.dark.json` (dark "Desk lamp"). W3C DTCG format (`$type`/`$value`), with a custom `$extensions["com.parchmark.cssName"]` to emit short var names (`--accent`, `--surface`, …)
- Built by `npm run build:tokens` (`node src/design-system/tokens/build.mjs`, via **style-dictionary**): light → `:root`, dark → `[data-theme="dark"]`, concatenated into the **generated** `design-system/tokens.css` (do not edit by hand)
- Reusable SFCs in `design-system/components/`: `DsMenu.vue`, `DsSegment.vue`, `DsToolButton.vue`. Icons are a hand-authored SVG factory in `design-system/icons/index.ts` (`createIcon(...)` → 18 components like `PlusIcon`, `SearchIcon`, `LockIcon`) — **no icon library dependency**

### Markdown
- Frontend rendering lives in `ui/src/features/notes/markdownRender.ts`: `marked` (GFM) → rewrite `language-mermaid` fences into `<div class="mermaid">` → sanitize with `dompurify` (allows GFM task-list `input`s). `stripTitle()` (in `noteMockHelpers.ts`) drops the leading H1 before render; `MarkdownProse.vue` emits via `v-html`
- Mermaid blocks are produced as markup only — **no mermaid runtime is wired** in this worktree
- Backend (`backend/app/utils/markdown.py`) extracts the H1 title for note records; FE and BE title/H1 handling must stay in sync — use the `parchmark-markdown-sync` skill after editing either

### Auth (frontend)
- Access tokens 30 min; refresh tokens 7 days (backend defaults)
- Frontend auth is a **composable singleton**, `features/auth/useAuth.ts` — module-level refs shared across every `useAuth()` call; **no Pinia/Vuex**. Session persisted via `@vueuse/core` `useStorage` under key `pm_auth` as `{ accessToken, refreshToken, user }`
- The single refresh-and-retry policy lives in `services/http.ts` (an `ofetch` instance, `retry: false`): on a `401` for any non-`/auth/refresh` call it calls the refresh hook **once** and retries once. Auth hooks are injected via `setAuthHooks()` so `http.ts` never imports the store (avoids a cycle)
- Route "protection" is the **auth gate in `App.vue`** — a `ready` ref gates first paint, then `v-if !ready` → `v-else-if !isAuthenticated` `<LoginView/>` → `v-else` `<AppShell/>`. There is **no router and no `requireAuth()` loader** in this worktree
- `App.vue` calls `restoreSession()` on mount (validates the stored token via `GET /auth/me`, clears on any error) before revealing `LoginView` vs `AppShell`
- Login (`POST /auth/login`) returns tokens only; `useAuth.login()` then fetches `/auth/me` for the user. Logout (`POST /auth/logout`) is best-effort

### Auth (backend)
- Hybrid auth: local JWT (HS256) + OIDC via Authelia (opaque or JWT access tokens). OIDC JWT path is **RS256** (JWKS); Authelia issues opaque tokens (`authelia_at_...`) by default — validated via userinfo endpoint, not JWT decode
- Logout is **stateless** — no server-side invalidation/blacklist
- OIDC validator (`app/auth/oidc_validator.py`) uses a shared httpx client with discovery/JWKS caching (double-checked locking)

### Migrations
- Run automatically on container startup (`APPLY_MIGRATIONS=true`)
- Test locally before deploying: `cd backend && uv run alembic upgrade head`
- Downgrade may fail if data constraints are violated

### Git Remotes
- `origin` = Forgejo on brahma (`brahma.myth-gecko.ts.net:3000`) — the only remote developers push to; hosts CI and deploy
- GitHub (`github.com/TejGandham/parchmark`) is a read-only offsite backup mirror, populated by automated sync — no local remote is configured and developers never push to it manually
- Use `tea` for all Forgejo PR management

### Navigation & view switching
- **No router.** Inside the app, "navigation" is ref toggles in `features/shell/AppShell.vue`: `mode` (`"read"|"edit"`), `activeId` (selected note), `settingsActive`, `navOpen` (mobile drawer). Views are `v-if`/`v-else-if` `<section>`s (settings placeholder vs read pane vs empty state)
- Shell pieces live in `features/shell/`: `AppTopbar`, `SidebarDrawer`, `UserFooter`, `BreadcrumbTrail`, `SearchBox`, `TagFilter`, `ReadEditSegment`, `ThemeToggleButton`, `OverflowNoteMenu`
- The notes list is fetched from the backend `GET /notes/` endpoint via the `useNotes` composable (`features/notes/useNotes.ts`, a module-singleton mirroring `useAuth`); `AppShell.vue` calls `useNotes()` and `fetchNotes()` on mount. `services/notes.ts` (`listNotes()`, `NoteDTO`) is the notes API client. `NoteDTO.tags` comes from the backend `NoteResponse` contract and is copied into `NoteMock` for `TagFilter`/`NoteCard`. Note ops other than listing (create/delete/select/toggle-tag, copy/export) are still local ref mutations + clipboard/Blob, so UI tag toggles are not persisted until the mutation wiring work lands. `SidebarDrawer.vue` accepts `loading`/`error` props and emits a `retry` event to refetch.

### Deployment
- Tests must pass before images build (CI gate)
- Deploy via k3s `kubectl rollout restart` (automated by Forgejo CI)
- SHA-tagged images enable rollback

## CI/CD (Forgejo)

| Workflow | Trigger | Purpose |
|-|-|-|
| `test.yml` | Push/PR to main | UI lint+test, backend lint+format+types+pytest |
| `deploy.yml` | Push to main | Build images → push to Forgejo registry → deploy to k3s |

GitHub mirror workflows are inactive.

## Visual QA

Before committing UI changes, use Chrome DevTools MCP:

1. `mcp__chrome-devtools__navigate_page` → `localhost:5173`
2. `mcp__chrome-devtools__take_snapshot` → element UIDs
3. `mcp__chrome-devtools__fill` → log in as `qauser` / `QaPass123!`
4. `mcp__chrome-devtools__list_console_messages` → verify no errors

## URLs

| Env | Frontend | Backend |
|-|-|-|
| Dev | localhost:5173 | localhost:8000/docs |
| Production | notes.engen.tech | assets-api.engen.tech/docs |

## Skills

### Project-specific (`.claude/skills/`)
- **`parchmark-branch-setup`** — fresh branch (or optional worktree) before any code change
- **`parchmark-land`** — session-end: commit, push, verify
- **`parchmark-markdown-sync`** — run after editing markdown utils to verify FE/BE parity
- **`migration-check`** — validate Alembic migrations before deploying

## Landing a PR (Session Completion)

**Work is NOT complete until `git push` succeeds AND CI is green.**

```bash
# 1. Run quality gates (if code changed)
make test

# 2. Commit + push on the feature/fix branch
git add <files>
git commit -m "..."
git pull --rebase origin main
git push -u origin <branch>

# 3. Open PR via tea (see Feature & Bug Workflow above)

# 4. Wait for CI — fix + push until green

# 5. After merge, delete the local branch
```

**Critical:**
- NEVER stop before pushing — that leaves work stranded
- NEVER say "ready to push when you are" — YOU push
- If push fails, resolve and retry until it succeeds

The `parchmark-land` skill automates steps 1–5.
