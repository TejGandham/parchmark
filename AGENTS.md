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

Run `bd prime` for full workflow context after session restart.

## Project Overview

**ParchMark** - Full-stack markdown note-taking app.

| Layer | Stack |
|-------|-------|
| Frontend | React 18, TypeScript, Vite, Chakra UI v2, Zustand, React Router v7 |
| Backend | FastAPI, Python 3.13, SQLAlchemy, JWT Auth, PostgreSQL |
| Deploy | Docker, Nginx, GitHub Actions, GHCR |

## Directory Structure

```
parchmark/
├── ui/                      # Frontend (React)
│   ├── src/features/        # auth/, notes/, ui/ (feature-first)
│   ├── src/services/        # API client
│   ├── src/utils/           # errorHandler, markdown
│   ├── src/config/          # Type-safe constants (api, storage)
│   └── src/__tests__/       # Vitest tests
├── backend/                 # Backend (FastAPI)
│   ├── app/                 # auth/, database/, models/, routers/, schemas/
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
POST /api/auth/login         # Returns access + refresh tokens
POST /api/auth/refresh       # Refresh access token
GET  /api/auth/me            # Current user

GET    /api/notes/           # List user's notes
POST   /api/notes/           # Create note
GET    /api/notes/{id}       # Get note
PUT    /api/notes/{id}       # Update note
DELETE /api/notes/{id}       # Delete note
```

## Environment Variables

### Frontend (ui/.env)
```bash
VITE_API_URL=/api
VITE_TOKEN_WARNING_SECONDS=60  # Optional
```

### Backend (backend/.env)
```bash
DATABASE_URL=postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
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
useUIStore     // Sidebar, preferences
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

### Testing
- Backend tests require Docker (testcontainers)
- Frontend form tests: use `fireEvent.submit()`, not button click
- Mock stores for isolated component tests

### Markdown
- `removeH1()` removes only the FIRST H1, not all
- Frontend and backend markdown utils must stay in sync

### Auth
- Access tokens: 30min, Refresh tokens: 7 days
- `useTokenExpirationMonitor()` logs out 1 min before expiry
- 10-second clock skew buffer for client/server time differences

### Migrations
- Run automatically on container startup (`APPLY_MIGRATIONS=true`)
- Test locally before deploying: `cd backend && uv run alembic upgrade head`
- Downgrade may fail if data constraints violated

### Deployment
- Tests must pass before images build (CI gate)
- Manual SSH deployment: `./deploy/update.sh`
- SHA-tagged images enable rollback

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

**Work is NOT complete until `git push` succeeds.**

```bash
# 1. File issues for remaining work
bd create --title="..." --type=task

# 2. Run quality gates
make test

# 3. Commit and push
git add <files>
bd sync
git commit -m "..."
git push

# 4. Verify
git status  # Must show "up to date with origin"
```
