# MUST USE KEEL framework. you are not allowed to sidestep it. If you strongly feel KEEL framework needs to be sidestepped get explicity consent from the user first. This is NOT a blanket consent and applies for the one particular case you obatained it for.

Guidance for Claude Code working with the ParchMark codebase. This file is a table of contents — follow links for depth.

## Project at a Glance

**ParchMark** — full-stack markdown note-taking app.

| Layer | Stack |
|-|-|
| Frontend | React 18, TypeScript, Vite, Chakra UI v2, Zustand, React Router v7 (Data Router) |
| Backend | FastAPI, Python 3.13, SQLAlchemy 2.0 (async), JWT + OIDC auth, PostgreSQL |
| Deploy | Docker, Nginx, k3s, Forgejo CI |

Deeper references:
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — domain / layer maps, dependency rules
- [`docs/north-star.md`](docs/north-star.md) — vision, four loops, growth stages
- [`docs/design-docs/index.md`](docs/design-docs/index.md) — core beliefs, UI design, code patterns, design context
- [`docs/process/THE-KEEL-PROCESS.md`](docs/process/THE-KEEL-PROCESS.md) — KEEL pipeline + agent roster
- [`PRODUCTION_DEPLOYMENT.md`](PRODUCTION_DEPLOYMENT.md) — deployment runbook

## KEEL Framework

All feature work flows through KEEL (Knowledge-Encoded Engineering Lifecycle).

```bash
/keel-refine docs/prds/<name>.md                # draft backlog entries from a PRD
/keel-pipeline F<id> docs/product-specs/<name>.md  # run pre-check → tests → impl → reviews → landing
/safety-check                                   # quick invariant audit on current diff
/keel-adopt                                     # (one-time) complete brownfield config — fills north-star, wires hooks
```

- **Specs** live in `docs/product-specs/` (template at `_TEMPLATE.md`)
- **Backlog** at `docs/exec-plans/active/feature-backlog.md`
- **Tech debt** at `docs/exec-plans/tech-debt-tracker.md`
- **Active plans** in `docs/exec-plans/active/`, completed in `completed/`
- `/keel-adopt` has not been run yet — `docs/north-star.md` still contains `[YOUR APPROACH]` placeholders and the hooks in `.claude/hooks/` are not wired into `settings.json`

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
├── ui/                  # Frontend (React)
│   └── src/
│       ├── features/    # auth/, notes/, settings/, ui/ (feature-first)
│       ├── router.tsx   # Data Router (loaders, actions, routes)
│       ├── services/    # API client
│       ├── utils/       # errorHandler, markdown, dateGrouping, noteScoring, mermaidInit
│       ├── config/      # type-safe constants (api, storage)
│       ├── types/       # shared types (Note, SimilarNote)
│       └── __tests__/   # Vitest
├── backend/             # Backend (FastAPI)
│   └── app/             # auth/, database/, models/, routers/, schemas/, services/
├── makefiles/           # modular make targets
├── deploy/              # production scripts
├── docs/
│   ├── north-star.md
│   ├── process/         # KEEL reference guides
│   ├── design-docs/     # core beliefs, UI design, code patterns, design context
│   ├── exec-plans/      # active + completed plans, feature-backlog, tech-debt
│   ├── product-specs/   # feature specs
│   └── references/      # external docs, llms.txt
└── .claude/             # agents, skills, hooks
```

## API Surface

The full, current API is discoverable at:
- Dev: <http://localhost:8000/docs>
- Prod: <https://assets-api.engen.tech/docs>

Notable non-obvious endpoints: `POST /api/notes/{id}/access` (fire-and-forget tracking for the "For You" scoring), `GET /api/notes/{id}/similar` (cosine similarity over embeddings), `GET /api/health` (DB + version info).

## Environment Variables

### Frontend (`ui/.env`)
```bash
VITE_API_URL=/api
VITE_TOKEN_WARNING_SECONDS=60       # optional
VITE_OIDC_ISSUER_URL=https://auth.engen.tech
VITE_OIDC_CLIENT_ID=parchmark
VITE_OIDC_REDIRECT_URI=<origin>/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=<origin>/login
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
OPENAI_API_KEY=                     # optional: embeddings silently disable if absent
EMBEDDING_MODEL=text-embedding-3-small  # optional override
```

### Build-time (Docker)
```bash
GIT_SHA=                            # set at docker build for version info
BUILD_DATE=                         # set at docker build for version info
```

## Testing

| Side | Tooling | Notes |
|-|-|-|
| Frontend | Vitest + RTL | Use `render` from `test-utils/render` (wraps providers); mock stores; form tests use `fireEvent.submit()` not button click |
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

### Markdown
- `removeH1()` removes **only the first H1**, not all
- Frontend (`ui/src/utils/markdown.ts`) and backend (`backend/app/utils/markdown.py`) must stay in sync — use the `parchmark-markdown-sync` skill after editing either

### Auth
- Access tokens 30 min; refresh tokens 7 days
- `useTokenExpirationMonitor()` logs out 1 min before expiry
- 10-second clock-skew buffer for client/server drift
- Route protection is the `requireAuth()` loader in `router.tsx` — there is **no `ProtectedRoute` component**
- Hybrid auth: local JWT (HS256) + OIDC via Authelia (opaque or JWT access tokens). Authelia issues opaque tokens (`authelia_at_...`) by default — validated via userinfo endpoint, not JWT decode
- OIDC validator (`app/auth/oidc_validator.py`) uses a shared httpx client with discovery/JWKS caching (double-checked locking)

### Migrations
- Run automatically on container startup (`APPLY_MIGRATIONS=true`)
- Test locally before deploying: `cd backend && uv run alembic upgrade head`
- Downgrade may fail if data constraints are violated

### Git Remotes
- `origin` = Forgejo on brahma (`brahma.myth-gecko.ts.net:3000`) — primary remote, CI + deploy
- `github` = GitHub mirror (`github.com/TejGandham/parchmark`) — code backup only (no active CI/deploy)
- Use `tea` for origin PRs; `gh` is for the GitHub mirror only
- Push to both: `git push origin <branch> && git push github <branch>`

### Embeddings
- `OPENAI_API_KEY` is optional — embeddings and similarity search silently degrade if absent
- Backfill existing notes: `cd backend && uv run python -m app.services.backfill`
- Note model has `embedding` (pgvector `Vector(1536)`), `access_count`, `last_accessed_at`

### Command Palette
- Primary navigation (replaced sidebar); triggered via the search button in the header
- `react-window` virtualizes large note lists
- "For You" section blends heuristic scoring (recency + frequency) with AI similarity when available

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

### KEEL (`.claude/skills/`)
- **`keel-refine`** — draft backlog entries from a PRD (never auto-runs the pipeline)
- **`keel-pipeline`** — orchestrate pre-check → test-writer → implementer → reviews → landing
- **`keel-adopt`** — one-time brownfield setup (CLAUDE.md refinement, domain invariants, hook wiring)
- **`keel-setup`** — greenfield interview-driven setup
- **`safety-check`** — scan current diff against domain invariants

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
