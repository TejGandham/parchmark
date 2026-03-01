# CLAUDE.md

Guidance for Claude Code working with the ParchMark codebase.

## Task Tracking

This repo uses [beads](https://github.com/steveyegge/beads) (`bd`) for task tracking.

**Do NOT use:** TodoWrite, TaskCreate, or markdown files for task tracking.

```bash
# View tasks
bd ready              # Show unblocked tasks ready for work
bd list               # Show all open issues
bd show <id>          # Show issue details

# Create tasks
bd q "Title"                                   # Quick create (outputs ID only)
bd create --title="..." --type=task --priority=2  # Full create

# Update tasks
bd update <id> --status=in_progress  # Claim work before coding
bd close <id>                        # Close completed issue
bd dep add <id> <dep>                # Add dependency

# Sync (REQUIRED at session end)
bd sync
```

**Priority:** 0=critical, 1=high, 2=medium, 3=low, 4=backlog (NOT "high"/"medium"/"low")

**Warning:** Never use `bd edit` - it opens $EDITOR which blocks agents.

**When to create issues:**
- Multi-step implementation work (before writing code)
- Bugs/issues discovered during ANY work (including research)
- Improvements identified while exploring code
- Remaining/incomplete work at session end

**When NOT to create issues:**
- Single-line trivial fixes
- One-off questions with no follow-up work

Run `bd prime` for full workflow context after session restart.

## Feature & Bug Workflow

**Every feature or bug fix MUST use a new worktree + branch. No exceptions.**

### 1. Create a Worktree (FIRST step)

```bash
# Feature
git worktree add .worktrees/feat/<short-description> -b feat/<short-description>
export BEADS_NO_DAEMON=1  # MANDATORY: prevents beads daemon from committing to wrong branch

# Bug fix
git worktree add .worktrees/fix/<short-description> -b fix/<short-description>
export BEADS_NO_DAEMON=1  # MANDATORY: prevents beads daemon from committing to wrong branch
```

- Worktrees live in `.worktrees/` (gitignored). Create the directory if it doesn't exist.
- **ALWAYS set `export BEADS_NO_DAEMON=1`** after creating a worktree. Worktrees share the beads database and the daemon may commit to the wrong branch.
- Branch off `main`. Never commit directly to `main`.
- Work inside the worktree directory for that feature/fix.

### 2. Implement & Test

- Work inside `.worktrees/<branch>/` — run `make test` from there
- Commit to the feature/fix branch

### 3. Open a PR on Origin (Forgejo) using `tea`

```bash
# Push branch to origin
git push -u origin <branch-name>

# Create PR using tea CLI
tea pr create --title "PR title" --description "## Summary" --base main --head <branch-name>

# List PRs
tea pr list

# Check PR status
tea pr view <number>

# Merge PR (after CI passes)
tea pr merge -s merge <number>
```

> **Use `tea` for all Forgejo PR management.** Do NOT use `gh` (GitHub only) or raw `curl`.

### 4. Wait for CI

**Work is NOT complete until CI passes on the PR.**

- Check CI status: `tea pr view <number>`
- If CI fails, fix the issues on the branch, push again, and wait for green
- Only report success to the user after CI is green

### 5. Clean up worktree

```bash
git worktree remove .worktrees/feat/<short-description>
```

## Project Overview

**ParchMark** - Full-stack markdown note-taking app.

| Layer | Stack |
|-------|-------|
| Frontend | React 18, TypeScript, Vite, Chakra UI v2, Zustand, React Router v7 (Data Router) |
| Backend | FastAPI, Python 3.13, SQLAlchemy 2.0 (async), JWT Auth, PostgreSQL |
| Deploy | Docker, Nginx, k3s, Forgejo CI |

## Directory Structure

```
parchmark/
├── ui/                      # Frontend (React)
│   ├── src/features/        # auth/, notes/, settings/, ui/ (feature-first)
│   ├── src/router.tsx       # Data Router config (loaders, actions, routes)
│   ├── src/services/        # API client
│   ├── src/utils/           # errorHandler, markdown, dateGrouping, dateFormatting, noteScoring, compactTime, mermaidInit
│   ├── src/config/          # Type-safe constants (api, storage)
│   ├── src/types/           # Shared TypeScript types (Note, SimilarNote)
│   └── src/__tests__/       # Vitest tests
├── backend/                 # Backend (FastAPI)
│   ├── app/                 # auth/, database/, models/, routers/, schemas/
│   │   └── services/        # embeddings (OpenAI), health_service, backfill
│   ├── tests/               # unit/, integration/
│   └── migrations/          # Alembic migrations
├── makefiles/               # Modular make targets
├── deploy/                  # Production deployment scripts
└── docs/                    # Extended documentation
```

## Commands

All commands run from project root. Use `make help` for full list.

### Development

```bash
make dev                     # Start all (PostgreSQL + Backend + Frontend)
make dev-ui                  # Frontend only (localhost:5173)
make dev-backend             # Backend only (localhost:8000)
make docker-dev              # PostgreSQL container only
```

### Testing

```bash
make test                    # Full CI pipeline (UI + Backend)
make test-ui-all             # UI: lint + tests
make test-backend-all        # Backend: lint + format + types + pytest
```

### User Management

```bash
make user-create USERNAME=x PASSWORD=y
make user-list
make user-delete USERNAME=x
```

### Deployment

```bash
make deploy-verify           # Health check production
make deploy-ssh              # SSH to production server
make deploy-logs             # View container logs
```

See `PRODUCTION_DEPLOYMENT.md` for full deployment guide.

## API Endpoints

```
POST /api/auth/login          # Returns access + refresh tokens
POST /api/auth/refresh        # Refresh access token
POST /api/auth/logout         # Signal logout (stateless, client-side token removal)
GET  /api/auth/me             # Current user

GET    /api/notes/            # List user's notes
POST   /api/notes/            # Create note
GET    /api/notes/{id}        # Get note
PUT    /api/notes/{id}        # Update note
DELETE /api/notes/{id}        # Delete note
POST   /api/notes/{id}/access # Track note access (fire-and-forget, for "For You" scoring)
GET    /api/notes/{id}/similar # Similar notes via cosine similarity on embeddings

GET    /api/settings/user-info        # Account info + note count + auth_provider
POST   /api/settings/change-password  # Local users only
GET    /api/settings/export-notes     # Streaming ZIP of all notes
DELETE /api/settings/delete-account   # Delete account and all notes

GET /api/health               # Full health check with DB status + version info
```

## Environment Variables

### Frontend (ui/.env)
```bash
VITE_API_URL=/api
VITE_TOKEN_WARNING_SECONDS=60       # Optional
VITE_OIDC_ISSUER_URL=https://auth.engen.tech
VITE_OIDC_CLIENT_ID=parchmark
VITE_OIDC_REDIRECT_URI=<origin>/oidc/callback
VITE_OIDC_LOGOUT_REDIRECT_URI=<origin>/login
```

### Backend (backend/.env)
```bash
DATABASE_URL=postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
OIDC_ISSUER_URL=https://auth.engen.tech
OIDC_AUDIENCE=parchmark
OIDC_OPAQUE_TOKEN_PREFIX=           # Optional: restrict opaque token format (e.g. "authelia_at_")
OIDC_DISCOVERY_URL=                 # Optional: separate URL for OIDC discovery (e.g. internal cluster DNS)
OIDC_USERNAME_CLAIM=preferred_username
OPENAI_API_KEY=                     # Required for embeddings; feature silently disabled if absent
EMBEDDING_MODEL=text-embedding-3-small  # Optional override
```

### Build-time (injected in Docker)
```bash
GIT_SHA=                            # Set at docker build for version info
BUILD_DATE=                         # Set at docker build for version info
```

## Code Patterns

### Error Handling (Frontend)
```typescript
import { handleError } from '../utils/errorHandler';
const appError = handleError(error);  // Normalizes all error types
```

### Type-Safe Constants
```typescript
import { API_ENDPOINTS } from '../config/api';
import { STORAGE_KEYS } from '../config/storage';
```

### Markdown Processing
```typescript
// Frontend: ui/src/utils/markdown.ts
// Backend: backend/app/utils/markdown.py (mirrors frontend)
markdownService.extractTitle(content)   // Get H1 title
markdownService.removeH1(content)       // Remove first H1 only
```

### Zustand Stores
```typescript
useAuthStore   // Auth state, login/logout
useNotesStore  // Notes CRUD, current note
useUIStore     // Command palette state, preferences
```

### React Router Data Router
```typescript
// Route loaders fetch data before render (ui/src/router.tsx)
loader: async () => { const notes = await api.getNotes(); return { notes }; }

// Route actions handle mutations (ui/src/features/notes/actions.ts)
action: createNoteAction  // Form submissions via useFetcher().submit()

// Access loader data in components
const { notes } = useRouteLoaderData('notes-layout');
```

### Async SQLAlchemy (Backend)
```python
# Use async session dependency
from app.database.database import get_async_db

async def my_endpoint(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Model))
    return result.scalars().all()
```

## Testing Patterns

### Frontend (Vitest + RTL)
```typescript
import { render } from 'test-utils/render';  // Custom render with providers
vi.mock('../features/auth/store');           // Mock stores
fireEvent.submit(form);                      // Use submit, not click
```

### Backend (Pytest)
- Parallel execution with pytest-xdist (each worker gets own PostgreSQL)
- Fixtures: `client`, `sample_user`, `auth_headers`
- 90% coverage enforced

## Code Style

### TypeScript
- Strong typing (avoid `any`)
- Functional components with hooks
- Chakra UI components, avoid inline styles

### Python
- Type hints where beneficial
- Ruff for linting/formatting
- 120 char line length

## Gotchas

### Docker
- `docker-compose.dev.yml` = PostgreSQL only (for local dev)
- `docker-compose.yml` = Full stack (for testing containers)
- `docker-compose.prod.yml` = Production (GHCR images)
- `docker-compose.oidc-test.yml` = PostgreSQL + Authelia (OIDC integration testing)

### Testing
- Backend tests require Docker (testcontainers)
- Some unit tests (`TestGetCurrentUser`, `TestDependencyIntegration`, etc.) depend on conftest fixtures that need Docker — these error locally without Docker running but pass in CI
- Run focused unit tests without Docker: `cd backend && uv run pytest tests/unit/auth/test_oidc_validator.py -v`
- Frontend form tests: use `fireEvent.submit()`, not button click
- Mock stores for isolated component tests
- **Important:** Always ensure new code has adequate test coverage before pushing.

### Markdown
- `removeH1()` removes only the FIRST H1, not all
- Frontend and backend markdown utils must stay in sync

### Auth
- Access tokens: 30min, Refresh tokens: 7 days
- `useTokenExpirationMonitor()` logs out 1 min before expiry
- 10-second clock skew buffer for client/server time differences
- Route protection via `requireAuth()` loader in router.tsx (no ProtectedRoute component)
- Hybrid auth: local JWT (HS256) + OIDC via Authelia (opaque or JWT access tokens)
- OIDC validator (`app/auth/oidc_validator.py`): shared httpx client, discovery/JWKS caching with double-checked locking
- Authelia issues opaque tokens (`authelia_at_...`) by default — validated via userinfo endpoint, not JWT decode
- OIDC env vars: `OIDC_ISSUER_URL`, `OIDC_AUDIENCE`, `OIDC_USERNAME_CLAIM`, `OIDC_OPAQUE_TOKEN_PREFIX`

### Migrations
- Run automatically on container startup (`APPLY_MIGRATIONS=true`)
- Test locally before deploying: `cd backend && uv run alembic upgrade head`
- Downgrade may fail if data constraints violated

### Git Remotes
- `origin` = Forgejo on brahma (`brahma.myth-gecko.ts.net:3000`), primary remote (CI + deploy)
- `github` = GitHub mirror (`github.com/TejGandham/parchmark`), code backup only (no active CI/deploy)
- Use `tea` CLI for origin PRs; `gh` CLI is GitHub mirror only
- Push to both: `git push origin <branch> && git push github <branch>`

### Embeddings
- `OPENAI_API_KEY` is optional — embeddings and similarity search silently degrade if absent
- Backfill existing notes: `cd backend && uv run python -m app.services.backfill`
- Note model has `embedding` (pgvector `Vector(1536)`), `access_count`, `last_accessed_at` fields

### Command Palette
- Primary navigation UI (replaced sidebar); triggered via the search button in the header
- Uses `react-window` for virtualized rendering of large note lists
- "For You" section blends heuristic scoring (recency+frequency) with AI similarity when available

### Deployment
- Tests must pass before images build (CI gate)
- Deploy: k3s via `kubectl rollout restart` (automated by Forgejo CI)
- SHA-tagged images enable rollback

## CI/CD (Forgejo)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `test.yml` | Push/PR to main | UI lint+test, backend lint+format+types+pytest |
| `deploy.yml` | Push to main | Build images → push to Forgejo registry → deploy to k3s via kubectl |

> **Note:** GitHub (`github` remote) is a code backup mirror only. Its workflows are inactive.

## Visual QA

Use Chrome DevTools MCP before committing UI changes:

```
1. mcp__chrome-devtools__navigate_page → localhost:5173
2. mcp__chrome-devtools__take_snapshot → Get element UIDs
3. mcp__chrome-devtools__fill → Login as qauser/QaPass123!
4. mcp__chrome-devtools__list_console_messages → Check for errors
```

## URLs

| Environment | Frontend | Backend |
|-------------|----------|---------|
| Dev | localhost:5173 | localhost:8000/docs |
| Production | notes.engen.tech | assets-api.engen.tech/docs |

## Guidelines

1. Use Makefile commands from project root
2. Always run `make test` before committing
3. Visual QA before UI changes
4. Use centralized error handling (`handleError()`)
5. Use type-safe constants from `config/`
6. Use `markdownService` for all markdown operations
7. Never commit `.env` files with secrets

## Session Completion

**Work is NOT complete until CI passes on the PR.**

```bash
# 1. File issues for remaining work
bd create --title="..." --type=task

# 2. Run quality gates
make test

# 3. Commit and push (on your feature/fix branch)
git add <files>
bd sync
git commit -m "..."
git push -u origin <branch-name>

# 4. Open PR on origin using tea CLI — see "Feature & Bug Workflow" above
# 5. Wait for CI to pass on the PR before reporting success
# 6. If CI fails, fix and push again until green
# 7. After merge, clean up: git worktree remove .worktrees/<branch>
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs with git:

- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

<!-- END BEADS INTEGRATION -->
