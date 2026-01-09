# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the ParchMark codebase.

## Project Overview

**ParchMark** is a full-stack markdown note-taking application with a React frontend and FastAPI backend.

### Tech Stack
- **Frontend**: React 18, TypeScript, Vite, Chakra UI v2, Zustand, React Router v7
- **Backend**: FastAPI, Python 3.13, SQLAlchemy, JWT Auth, PostgreSQL
- **Deployment**: Docker, Nginx, GitHub Actions, GitHub Container Registry (GHCR)
- **Infrastructure**: Production server with SSH-based deployment, automated CI/CD pipeline

## Directory Structure

```
parchmark/
├── ui/                      # Frontend React application
│   ├── src/                 # Source code
│   │   ├── features/        # Feature-based organization
│   │   │   ├── auth/        # Authentication (LoginForm, ProtectedRoute, UserLoginStatus)
│   │   │   ├── notes/       # Notes management (NoteContent, NoteActions, NotesContainer)
│   │   │   └── ui/          # UI components (Header, Sidebar, NotFoundPage)
│   │   ├── services/        # API and markdown services
│   │   ├── utils/           # Shared utilities (errorHandler, markdown)
│   │   ├── config/          # Type-safe constants (api, storage)
│   │   ├── styles/          # Theme and global styles
│   │   └── __tests__/       # Vitest test files mirroring src structure
│   ├── public/              # Static assets
│   └── Dockerfile           # Frontend container configuration
├── backend/                 # Backend FastAPI application
│   ├── app/                 # Application code
│   │   ├── auth/            # Authentication logic (JWT, password hashing)
│   │   ├── database/        # Database configuration and initialization
│   │   ├── models/          # SQLAlchemy models (User, Note)
│   │   ├── routers/         # API endpoints (auth, notes)
│   │   ├── schemas/         # Pydantic schemas for validation
│   │   ├── utils/           # Shared utilities (markdown)
│   │   └── main.py          # FastAPI application entry point
│   ├── tests/               # Pytest test files
│   └── Dockerfile           # Backend container configuration
├── makefiles/               # Modular Makefile organization
│   ├── common.mk            # Shared variables, colors, helper functions
│   ├── help.mk              # Auto-generated help system
│   ├── ui.mk                # UI test and development targets
│   ├── backend.mk           # Backend test and development targets
│   ├── docker.mk            # Docker-related targets
│   ├── users.mk             # User management targets (templated)
│   └── deploy.mk            # Deployment targets (25 commands)
├── .github/
│   └── workflows/
│       └── deploy.yml       # Automated deployment pipeline (5 jobs)
├── docs/deployment_upgrade/ # Deployment system documentation
│   ├── DEPLOYMENT_VALIDATED.md     # Architecture and implementation guide
│   ├── DEPLOYMENT_PROGRESS.md      # Implementation status tracker
│   ├── FUTURE_IMPROVEMENTS.md      # Security enhancement roadmap
│   ├── PHASE3_SERVER_SETUP.md      # Server setup instructions
│   └── PHASE4_GITHUB_SECRETS.md    # GitHub Secrets configuration guide
├── Makefile                 # Main orchestrator (includes all makefiles/*.mk)
├── docker-compose.yml       # Development orchestration (all services)
├── docker-compose.dev.yml   # PostgreSQL-only for local development
└── docker-compose.prod.yml  # Production orchestration (GHCR images)

```

## Prerequisites

- **Docker & Docker Compose** (required for PostgreSQL and tests)
- **Node.js 18+** for frontend
- **Python 3.13** for backend

Note: PostgreSQL runs exclusively in Docker containers. No local PostgreSQL installation is needed.

## Build & Run Commands

### Frontend (UI)
```bash
# Preferred: Use Makefile from project root
make dev-ui                  # Start Vite dev server (auto-opens browser at :5173)
make test-ui-all             # Run all UI tests (lint + tests)

# Or run commands directly from ui directory
cd ui
npm install                  # Install dependencies
npm run dev                  # Start Vite dev server (auto-opens browser at :5173)
npm run build                # Build for production
npm run lint                 # Run ESLint
npm run format               # Format with Prettier
npm test                     # Run Vitest tests
npm run test:coverage        # Generate coverage report
npm run test:watch           # Watch mode for development
```

### Backend
```bash
# Preferred: Use Makefile from project root
make docker-dev              # Start PostgreSQL container
make dev-backend             # Start backend dev server on :8000
make test-backend-all        # Run all backend tests (lint + format + types + pytest)

# Or run commands directly from backend directory
cd backend
uv sync                      # Install dependencies
uv run uvicorn app.main:app --reload  # Start dev server on :8000
uv run ruff check            # Run Ruff linter
uv run ruff format           # Format Python code
uv run pytest                # Run tests with coverage
uv run pytest tests/unit     # Run unit tests only
uv run pytest tests/integration  # Run integration tests only
uv run mypy app              # Run type checking
```

### CI/CD Testing with Makefile
```bash
# From project root - mirrors GitHub Actions CI pipeline
make help                    # Show all available commands
make test                    # Run ALL tests (UI + Backend)
make test-all                # Same as 'make test'

# Individual test suites
make test-ui-all             # Run all UI tests (lint + tests)
make test-backend-all        # Run all backend tests (lint + format + types + pytest)

# Granular testing
make test-ui-lint            # ESLint only
make test-ui-test            # Vitest tests only
make test-backend-lint       # Ruff linting check
make test-backend-format     # Ruff formatting check
make test-backend-types      # Mypy type checking
make test-backend-pytest     # Pytest with coverage

# Development convenience
make dev-ui                  # Start UI dev server
make dev-backend             # Start backend dev server
make docker-dev              # Start PostgreSQL container
make docker-dev-down         # Stop PostgreSQL container

# Maintenance
make install-all             # Install all dependencies
make clean                   # Clean test artifacts and cache
```

### Docker

#### Two Docker Compose Files Explained

**`docker-compose.dev.yml`** - PostgreSQL-only for local development:
- Runs ONLY PostgreSQL in a container
- Backend and frontend run directly on your host machine
- Faster development with hot-reload and easier debugging
- Direct access to code changes without rebuilding containers
- Use this for day-to-day development work

**`docker-compose.yml`** - Full containerized stack:
- Runs ALL services (PostgreSQL, backend, frontend) in containers
- Mimics production environment exactly
- Used for testing the complete Docker deployment
- Ensures everything works together in containers before deployment
- Use this to verify production readiness

```bash
# Local Development (PostgreSQL only in Docker)
make docker-dev              # Start PostgreSQL container
make docker-dev-down         # Stop PostgreSQL container
# Then run backend/frontend directly on host using make dev-backend / make dev-ui

# Full Stack in Docker (all services containerized)
docker compose up -d         # Start all services in containers
docker compose logs -f       # View logs from all containers
docker compose down          # Stop all containers

# Production
docker compose -f docker-compose.prod.yml up -d
```

## Application Architecture

### Authentication & Security
- **JWT-based authentication** with refresh token support
  - Access tokens: 30-minute expiration
  - Refresh tokens: 7-day expiration
  - Token refresh endpoint for seamless session extension
- **OIDC/SSO support** via Authelia (optional)
  - Hybrid auth mode: supports both local and OIDC authentication
  - PKCE-enabled public client for secure browser-based auth
  - Auto-creates users on first OIDC login
  - See `docs/AUTHELIA_OIDC_QUICKSTART.md` for setup
- **Proactive token expiration monitoring**: Automatically logs out users 1 minute before token expires
- **Token expiration checking**: Monitors tokens every 3 minutes with configurable warning threshold
- **Clock skew protection**: 10-second buffer to handle client/server time differences
- **Dual-layer security**: Proactive monitoring + 401 interceptor as fallback
- **Bcrypt password hashing** for secure storage
- **Protected routes** using React Router v7 guards
- **Persistent sessions** via localStorage (Zustand persist middleware)
- **CORS configuration** for frontend-backend communication
- **User isolation**: Each user can only access their own notes

### Frontend Architecture

#### State Management (Zustand)
```typescript
// Three main stores with specific responsibilities:
useAuthStore   // Authentication state, login/logout actions
useNotesStore  // Notes CRUD operations, current note tracking
useUIStore     // Sidebar state, dark mode toggle
```

#### Component Organization
```
features/{domain}/
├── components/     # React components
├── store/          # Zustand store
├── hooks/          # Custom hooks (e.g., useStoreRouterSync, useTokenExpirationMonitor)
├── utils/          # Utility functions (e.g., tokenUtils for JWT handling)
└── styles/         # Feature-specific CSS
```

#### Key Libraries
- **Chakra UI v2**: Component library with custom theme
- **React Markdown + RemarkGFM**: Markdown rendering with GitHub flavored markdown
- **FontAwesome**: Icon system throughout the app
- **Mermaid**: Diagram rendering support
- **Immer**: Immutable state updates in Zustand

### Backend Architecture

#### API Structure
- **RESTful endpoints** with OpenAPI documentation
- **Automatic title extraction** from markdown H1 headers
- **Pydantic models** for request/response validation
- **SQLAlchemy ORM** for database operations
- **Dependency injection** for database sessions and auth

#### Database Schema
```python
User:
  - id: Integer (Primary Key)
  - username: String (Unique)
  - password_hash: String
  - created_at: DateTime
  - notes: Relationship

Note:
  - id: String (Primary Key, format: "note-{timestamp}")
  - user_id: Integer (Foreign Key)
  - title: String
  - content: Text
  - created_at: DateTime
  - updated_at: DateTime
```

## Testing Infrastructure

### Frontend Testing
- **Framework**: Vitest + React Testing Library
- **Coverage**: 90% threshold enforced
- **Environment**: jsdom with browser API mocks
- **Structure**: Tests in `src/__tests__/` mirroring source
- **Key Patterns**:
  ```javascript
  // Use custom render with providers
  import { render } from 'test-utils/render';

  // Mock stores for isolated testing
  vi.mock('../features/auth/store');

  // Form submissions
  fireEvent.submit(form);  // Not button.click()
  ```

### Backend Testing
- **Framework**: Pytest with fixtures
- **Parallel Execution**: pytest-xdist with auto-detection (`-n auto`) and worksteal distribution
  - Each worker gets its own PostgreSQL container for complete isolation
  - No race conditions: workers operate on separate databases
  - Resource usage: ~100-200MB per container, ~2-5s startup per worker
  - Use `make test-backend-pytest-limited` (4 workers) for resource-constrained environments
- **Coverage**: 90% threshold enforced
- **Database**: PostgreSQL via testcontainers (requires Docker)
- **Test Isolation**: TRUNCATE CASCADE before/after each test (within each worker's database)
- **Structure**:
  - `tests/unit/` - Function and class tests
  - `tests/integration/` - API endpoint tests
- **Key Fixtures**:
  - `client`: TestClient with DB override
  - `sample_user`: User with hashed password
  - `auth_headers`: JWT Bearer token headers

## Code Style Guidelines

### TypeScript/React
- **Strong typing**: Avoid `any`, use interfaces
- **Functional components** with hooks
- **Zustand stores** for global state
- **Chakra UI** components, avoid inline styles
- **Import order**: External libs, then internal

### Python
- **Type hints** where beneficial
- **Docstrings** for functions and classes
- **Ruff** for linting and formatting
- **Import sorting** with isort rules
- **Line length**: 120 characters max

## API Endpoints

### Authentication
```
POST /api/auth/login     - User login (returns access & refresh tokens)
POST /api/auth/refresh   - Refresh access token using refresh token
POST /api/auth/logout    - User logout
GET  /api/auth/me        - Current user info
```

### Notes
```
GET    /api/notes/       - List user's notes
POST   /api/notes/       - Create new note
GET    /api/notes/{id}   - Get specific note
PUT    /api/notes/{id}   - Update note
DELETE /api/notes/{id}   - Delete note
```

## Environment Variables

### Frontend (.env)
```bash
VITE_API_URL=/api                    # API base URL (proxied in dev)
VITE_TOKEN_WARNING_SECONDS=60        # Optional: Seconds before token expiration to trigger logout (default: 60)
```

### Backend (.env)
```bash
# PostgreSQL in Docker container (no local install needed)
DATABASE_URL=postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development  # or production
```

## Docker Configuration

### Frontend Container
- **Multi-stage build** with Node.js 23 Alpine
- **Nginx** for serving static files
- **Dynamic config** switching (HTTP/HTTPS)
- **API proxy** to backend service

### Backend Container
- **Multi-stage build** with Python 3.13
- **uv package manager** for fast dependency installation
- **Non-editable install** for production
- **Module execution**: `python -m app`

### Docker Compose
- **Networks**: Internal communication between services
- **Health checks** for monitoring (curl-based, standardized across services)
- **Environment files**: `.env.docker` for dev, `.env.production` for prod
- **Volume mounting**: Persistent database storage in production
- **Three compose files**:
  - `docker-compose.dev.yml` - PostgreSQL only (for local development)
  - `docker-compose.yml` - Full stack (for testing containerized environment)
  - `docker-compose.prod.yml` - Production (uses GHCR images with health checks)

## Deployment System

### Production Environment
- **Frontend**: https://notes.engen.tech
- **Backend API**: https://assets-api.engen.tech
- **API Documentation**: https://assets-api.engen.tech/docs
- **Health Endpoints**:
  - Backend: `/api/health` (includes database connectivity check)
  - Frontend: `/` (served by Nginx)

### Automated Deployment Pipeline

The deployment system uses GitHub Actions for automated CI/CD with the following workflow:

**Workflow Structure** (`.github/workflows/deploy.yml`):
1. **Job 1 - Test**: Runs full test suite (UI + Backend)
   - Ensures broken code never gets deployed
   - Uses `make test-all` for comprehensive validation
2. **Job 2 - Build Backend**: Builds and pushes backend image to GHCR
3. **Job 3 - Build Frontend**: Builds and pushes frontend image to GHCR
4. **Job 4 - Deploy**: SSH-based deployment to production server
   - Requires manual approval (production environment protection)
   - Pulls new images, runs migrations, updates services
   - Health checks with retries and exponential backoff
5. **Job 5 - Notify**: Post-deployment status notification

**Key Features**:
- **Dual image tagging**: `:latest` and `:sha-xxxxx` for easy rollbacks
- **Test gate**: All tests must pass before building images
- **Migration safety**: Deployment fails if database migrations fail
- **Health verification**: 12 retries with 5-second delay and exponential backoff
- **Error handling**: `set -Eeuo pipefail` with ERR trap for fail-fast behavior
- **Security**: Production environment requires manual approval

**Triggers**:
- Automatic on push to `main` branch
- Manual via `workflow_dispatch`

### Deployment Commands (Makefile)

25 deployment commands organized into categories:

**Verification** (3 commands):
```bash
make deploy-verify              # Health check backend + frontend
make deploy-verify-backend      # Backend health only
make deploy-verify-frontend     # Frontend health only
```

**Status & Logs** (6 commands):
```bash
make deploy-status              # Recent GitHub Actions runs
make deploy-status-latest       # Latest deployment details
make deploy-logs                # Container logs (last 50 lines)
make deploy-logs-follow         # Real-time log streaming
make deploy-logs-backend        # Backend logs only
make deploy-logs-frontend       # Frontend logs only
```

**Deployment Control** (3 commands):
```bash
make deploy-trigger             # Manually trigger GitHub Actions
make deploy-watch               # Watch deployment progress
make deploy-rollback SHA=xxx    # Rollback to specific version
```

**Pre-Deployment** (3 commands):
```bash
make deploy-push-check          # Run all pre-deployment checks
make deploy-test-local          # Validate docker-compose.prod.yml
make deploy-build-local         # Build production images locally
```

**SSH Operations** (3 commands):
```bash
make deploy-ssh                 # SSH into production server
make deploy-ps                  # Show running containers
make deploy-disk-usage          # Check disk space
```

**Utilities** (2 commands):
```bash
make deploy-list-images         # List available image versions
make deploy-help                # Comprehensive deployment guide
```

### Deployment Workflow

1. **Development & Testing**:
   ```bash
   make test-all                # Run all tests locally
   make deploy-test-local       # Validate docker-compose files
   ```

2. **Pre-Deployment Checks**:
   ```bash
   make deploy-push-check       # Runs tests + validation
   ```

3. **Trigger Deployment**:
   ```bash
   git push origin main         # Auto-triggers workflow
   # OR
   make deploy-trigger          # Manual trigger via gh CLI
   ```

4. **Monitor Deployment**:
   ```bash
   make deploy-status           # Check deployment runs
   make deploy-watch            # Watch progress
   ```

5. **Verify Deployment**:
   ```bash
   make deploy-verify           # Health checks
   make deploy-logs             # View container logs
   ```

6. **Rollback** (if needed):
   ```bash
   make deploy-list-images      # List available SHA tags
   make deploy-rollback SHA=abc123
   ```

### Container Health Checks

All services use standardized curl-based health checks:

**Backend** (`backend/Dockerfile.prod`):
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1
```

**Frontend** (`docker-compose.prod.yml`):
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/"]
  interval: 30s
  timeout: 10s
  start_period: 20s
  retries: 3
```

**PostgreSQL**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U parchmark_user -d parchmark_db"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### Security Measures

- **GitHub Secrets**: Encrypted storage for sensitive credentials
- **Read-only GHCR token**: `read:packages` scope only
- **SSH key authentication**: ED25519 keys (no passwords)
- **Manual approval**: Required for production deployments
- **Branch restriction**: Only `main` branch can deploy
- **Token rotation**: 90-day expiration with reminders
- **Test gate**: No deployment without passing tests
- **Migration validation**: Deployment fails if migrations fail
- **Health verification**: Extensive retries before marking success

### Documentation

Comprehensive deployment documentation available in `docs/deployment_upgrade/`:
- **DEPLOYMENT_VALIDATED.md** - Architecture and implementation guide
- **DEPLOYMENT_PROGRESS.md** - Implementation status and history
- **FUTURE_IMPROVEMENTS.md** - Security enhancement roadmap
- **PHASE3_SERVER_SETUP.md** - Server setup instructions
- **PHASE4_GITHUB_SECRETS.md** - GitHub Secrets configuration

## Key Implementation Patterns

### Centralized Error Handling
```typescript
// ui/src/utils/errorHandler.ts
import { handleError, AppError, ERROR_CODES } from '../utils/errorHandler';

// Usage in stores and services
try {
  const notes = await api.getNotes();
  set({ notes, isLoading: false });
} catch (error: unknown) {
  const appError = handleError(error);
  set({ error: appError.message, isLoading: false });
}

// Error codes available:
// UNKNOWN_ERROR, NETWORK_ERROR, TYPE_ERROR, PARSE_ERROR,
// AUTHENTICATION_ERROR, AUTHORIZATION_ERROR, VALIDATION_ERROR,
// NOT_FOUND, SERVER_ERROR
```

### Type-Safe Constants
```typescript
// ui/src/config/storage.ts
import { STORAGE_KEYS } from '../config/storage';
localStorage.getItem(STORAGE_KEYS.AUTH); // Type-safe, autocomplete

// ui/src/config/api.ts
import { API_ENDPOINTS } from '../config/api';
httpClient.get(API_ENDPOINTS.NOTES.LIST); // Type-safe endpoint URLs
httpClient.put(API_ENDPOINTS.NOTES.UPDATE('note-123')); // Dynamic routes
```

### Markdown Processing
```typescript
// Frontend: ui/src/utils/markdown.ts
import { markdownService } from '../utils/markdown';

const title = markdownService.extractTitle('# Hello\n\nContent'); // "Hello"
const formatted = markdownService.formatContent('# Title'); // "# Title\n\n"
const withoutH1 = markdownService.removeH1('# Title\n\nBody'); // "Body"
const newNote = markdownService.createEmptyNote('My Note'); // "# My Note\n\n"

// Backend: backend/app/utils/markdown.py (mirrors frontend exactly)
from app.utils.markdown import markdown_service

title = markdown_service.extract_title("# Hello\n\nContent")  # "Hello"
formatted = markdown_service.format_content("# Title")  # "# Title\n\n"
without_h1 = markdown_service.remove_h1("# Title\n\nBody")  # "Body"
new_note = markdown_service.create_empty_note("My Note")  # "# My Note\n\n"

// Both use same regex patterns:
// H1_REGEX = /^#\s+(.+)$/m (TypeScript) or r"^#\s+(.+)$" (Python)
// H1_REMOVE_REGEX removes ONLY the first H1 heading (not all)
```

### Note ID Generation
```javascript
// Unique IDs with timestamp
`note-${Date.now()}`  // "note-1703123456789"
```

### Store Actions Pattern
```javascript
// Actions embedded in store
const store = create((set) => ({
  state: value,
  actions: {
    doSomething: () => set(...)
  }
}));
```

### Router Sync Hook
```javascript
// Sync URL params with store state
useStoreRouterSync() // In NotesContainer
```

### JWT Token Monitoring Pattern
```javascript
// Frontend: Proactive token expiration monitoring
useTokenExpirationMonitor() // In App.tsx, checks every 3 minutes

// Token utilities for JWT handling
getTokenExpiration(token) // Returns expiration timestamp or null
isTokenExpiringSoon(token, withinSeconds) // Checks if token expires soon
```

## Development Workflow

### Local Development (Recommended)
1. Start PostgreSQL: `make docker-dev` (from project root)
2. Start backend: `make dev-backend` (from project root)
3. Start frontend: `make dev-ui` (from project root)
4. Access app at `http://localhost:5173`
5. API docs at `http://localhost:8000/docs`

This approach uses PostgreSQL in Docker but runs backend/frontend on host for faster development.

### Testing Changes
1. **Recommended**: Use `make test` to run the full CI pipeline locally (both UI + Backend)
2. Frontend only: `make test-ui-all` (or `make test-ui-lint` / `make test-ui-test` for specific checks)
3. Backend only: `make test-backend-all` (or specific targets like `make test-backend-pytest`)
4. Quick development testing:
   - Frontend watch mode: `npm run test:watch` (in `ui/` directory)
   - Backend specific tests: `uv run pytest tests/path/to/test.py` (in `backend/` directory)
5. Check coverage reports:
   - Frontend: `ui/coverage/`
   - Backend: `backend/htmlcov/`

### Full Stack Docker Development
1. Build: `docker compose build`
2. Run: `docker compose up -d`
3. Access at `http://localhost:8080`
4. Logs: `docker compose logs -f`

This runs all services in containers, useful for testing production-like environment.

## Common Tasks

### Add a New Feature
1. Create feature directory: `features/newfeature/`
2. Add components, store, hooks as needed
3. Write tests in `__tests__/features/newfeature/`
4. Update router if new routes needed
5. Add backend endpoints if required

### Update Dependencies
- Frontend: `npm update` then test thoroughly
- Backend: `uv lock --upgrade` then `uv sync`

### User Management
The `backend/scripts/manage_users.py` script provides user management commands:
- `create <username> <password>` - Create a new user
- `update-password <username> <password>` - Update user password
- `delete <username>` - Delete a user
- `list` - List all users

#### Local Development (PostgreSQL in Docker, backend on host)
```bash
# Using Makefile targets (recommended)
make user-create USERNAME=admin PASSWORD=SecurePassword123
make user-update-password USERNAME=admin PASSWORD=NewPassword456
make user-delete USERNAME=olduser
make user-list

# Or run directly from backend directory
cd backend
uv run python scripts/manage_users.py create admin SecurePassword123
uv run python scripts/manage_users.py update-password admin NewPassword456
uv run python scripts/manage_users.py delete olduser
uv run python scripts/manage_users.py list
```

#### Docker Development (all services in containers)
```bash
# First, ensure Docker images are built (after any Dockerfile changes)
make docker-build

# Then start services
make docker-up

# Using Makefile targets (recommended)
make user-create-docker USERNAME=admin PASSWORD=SecurePassword123
make user-update-password-docker USERNAME=admin PASSWORD=NewPassword456
make user-delete-docker USERNAME=olduser
make user-list-docker

# Or run docker compose exec directly
docker compose exec backend python scripts/manage_users.py create admin SecurePassword123
docker compose exec backend python scripts/manage_users.py update-password admin NewPassword456
docker compose exec backend python scripts/manage_users.py delete olduser
docker compose exec backend python scripts/manage_users.py list
```

#### Production (Docker with production config)
```bash
# First, ensure production Docker images are built (after any Dockerfile changes)
make docker-build-prod

# Then start production services
make docker-up-prod

# Using Makefile targets (recommended)
make user-create-prod USERNAME=admin PASSWORD=SecurePassword123
make user-update-password-prod USERNAME=admin PASSWORD=NewPassword456
make user-delete-prod USERNAME=olduser
make user-list-prod

# Or run docker compose with production file
docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py create admin SecurePassword123
docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py update-password admin NewPassword456
docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py delete olduser
docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py list
```

**Note**: After updating the backend Dockerfile, you must rebuild the Docker images before user management commands will work in Docker/production environments.

### Database Migrations
- **PostgreSQL** is the only supported database
- **Alembic** manages schema migrations in `backend/migrations/`
- Migrations are idempotent and check for existing columns/indexes

#### Running Migrations
```bash
# Check current migration status
cd backend && uv run alembic current

# Apply all pending migrations
cd backend && uv run alembic upgrade head

# Rollback one migration
cd backend && uv run alembic downgrade -1

# View migration history
cd backend && uv run alembic history
```

#### Creating New Migrations
```bash
# Auto-generate migration from model changes
cd backend && uv run alembic revision --autogenerate -m "description"

# Create empty migration for manual edits
cd backend && uv run alembic revision -m "description"
```

#### Production Deployment
Migrations run automatically during deployment via GitHub Actions.
For manual deployment:
```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

**Important**: Always test migrations locally before deploying. Downgrade migrations may fail if data constraints are violated (e.g., OIDC users with NULL passwords).

## Security Considerations

- **Never commit** `.env` files with real secrets
- **JWT secrets** must be strong and unique in production
- **Password requirements** enforced at API level
- **CORS origins** strictly configured
- **SQL injection** prevented via SQLAlchemy ORM
- **XSS protection** via React's built-in escaping

## Performance Optimization

### Frontend
- **Code splitting** with React.lazy()
- **Memoization** where beneficial
- **Virtualization** for long lists (if needed)
- **Bundle analysis** with Vite

### Backend
- **Database indexes** on frequently queried fields
- **Connection pooling** for production
- **Async operations** throughout
- **Response caching** where appropriate

## Troubleshooting

### Common Issues

#### Frontend won't start
- Check Node version (18+)
- Clear node_modules and reinstall
- Check for port conflicts (5173)

#### Backend API errors
- Check Python version (3.13)
- Verify .env file exists
- Check database connection and permissions

#### Docker issues
- Ensure Docker daemon running
- Check port availability (8080, 8000)
- Review container logs

#### Test failures
- Mock environment variables properly
- Clear test database between runs
- Check for timing issues in async tests

## Allowed URLs

Development:
- http://localhost:5173/ - Frontend dev server (Vite)
- http://localhost:8000/ - Backend API (FastAPI with docs at /docs)
- http://localhost:8080/ - Docker deployment (full stack)

Production:
- https://notes.engen.tech - Frontend application
- https://assets-api.engen.tech - Backend API
- https://assets-api.engen.tech/docs - API documentation (Swagger UI)
- https://assets-api.engen.tech/api/health - Health check endpoint

## Important Guidelines

1. **Use Makefile commands** from project root instead of manual commands (see `make help` for all options)
2. **Always test** before committing changes - use `make test` to run full CI pipeline
3. **Follow existing patterns** in the codebase
4. **Write tests** for new functionality (add regression tests for bugs)
5. **Update documentation** when adding features
6. **Use strong typing** in TypeScript and Python
7. **Use centralized error handling** via `handleError()` for all error scenarios (see ui/src/utils/errorHandler.ts)
8. **Use type-safe constants** from `config/` directory instead of magic strings
9. **Use MarkdownService** for all markdown operations to maintain frontend/backend parity
10. **Handle errors gracefully** with user feedback
11. **Keep components focused** and reusable
12. **Optimize for readability** over cleverness
13. **Run linting and formatting** before commits (enforced in Makefile)
14. **Deployment safety**: Never commit secrets; use `make deploy-push-check` before deploying
15. **Migration safety**: Test database migrations locally before deploying
16. **Verify deployments**: Always run `make deploy-verify` after deploying to production
17. **Monitor production**: Use `make deploy-logs` and `make deploy-status` to monitor deployments

## Additional Notes

### Architecture & Patterns
- The application uses a **feature-first** organization pattern
- **Centralized error handling** with 9 specific error codes
- **Type-safe constants** for all API endpoints and storage keys
- **Synchronized markdown utilities** between frontend/backend using Protocol/Interface pattern
- **Modular Makefile** organization with auto-generated help system

### State Management & Storage
- **State persistence** is handled via localStorage for auth/UI
- **JWT token monitoring** proactively prevents expired token usage with automatic logout
- **Token expiration resilience** with clock skew protection and dual-layer verification
- **Refresh token support** enables seamless session extension without re-authentication

### Testing & Quality
- **Test coverage**: 90%+ enforced (315 UI tests + 467 backend tests = 782 total)
- **CI/CD testing** can be replicated locally using the Makefile
- **Code duplication**: Reduced to <2% through centralized utilities and constants
- **Markdown processing**: removeH1() correctly removes only first H1 heading

### Deployment & Production
- **Automated CI/CD**: 5-job GitHub Actions workflow (Test → Build → Deploy → Notify)
- **Test gate**: All tests must pass before images are built
- **Migration safety**: Deployment fails if database migrations fail
- **Health checks**: Standardized curl-based checks across all services with retries
- **Rollback support**: SHA-tagged images enable instant rollback to any version
- **25 Makefile commands**: Comprehensive deployment management (`make deploy-help`)
- **Security posture**: 9.5/10 (manual approval, test gate, migration validation, error handling)
- **Monitoring**: Real-time logs, deployment status, and health verification via Makefile
- **Production URLs**: notes.engen.tech (frontend), assets-api.engen.tech (backend)

### UI/UX Features
- **Dark Mode Support**: Full light and dark theme implementation
  - Color mode toggle in Header with moon/sun icons
  - Semantic tokens automatically adapt for both themes
  - User preference persists via Chakra UI's localStorage
  - Smooth transitions between themes
- **Empty State Design**: Consistent pattern with helpful guidance
  - Sidebar "No Notes Yet" state with circular icon, helpful copy, and CTA button
  - NoteContent "No Note Selected" state with welcoming messaging and feature tips
  - 404 page with clear navigation options and visual hierarchy
  - Theme-aware circular icon containers (primary.50 light / primary.900 dark)
- **Accessibility (WCAG AA)**: Comprehensive keyboard and screen reader support
  - Descriptive ARIA labels on all interactive elements (e.g., "Select note: {title}", "Delete note: {title}")
  - Keyboard navigation with Enter/Space key support on note items
  - Skip-to-content link for screen readers (appears on focus)
  - Semantic landmark roles (nav, main) for navigation structure
  - Focus-visible indicators with primary.500 outline (keyboard-only)
  - Decorative icons marked aria-hidden for cleaner screen reader experience
- **Responsive Layouts**: Optimized space utilization
  - Sidebar: Full viewport height (h="100%")
  - Edit textarea: Dynamic height calc(100vh - 250px) for maximum writing space

### Known Limitations & Future Enhancements
- **Real-time updates** are not implemented (consider WebSockets for future)
- **File uploads** are not supported (markdown text only)
- **Multi-language support** is not implemented
- **Backup functionality** should be added for production use
- **Token revocation** is not yet implemented (consider Redis-based blacklist for future)
