# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the ParchMark codebase.

## Project Overview

**ParchMark** is a full-stack markdown note-taking application with a React frontend and FastAPI backend.

### Tech Stack
- **Frontend**: React 18, TypeScript, Vite, Chakra UI v2, Zustand, React Router v7
- **Backend**: FastAPI, Python 3.13, SQLAlchemy, JWT Auth, PostgreSQL
- **Deployment**: Docker, Nginx, uv package manager

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
│   │   ├── styles/          # Theme and global styles
│   │   ├── config/          # Constants and environment configuration
│   │   └── __tests__/       # Jest test files mirroring src structure
│   ├── public/              # Static assets
│   └── Dockerfile           # Frontend container configuration
├── backend/                 # Backend FastAPI application
│   ├── app/                 # Application code
│   │   ├── auth/            # Authentication logic (JWT, password hashing)
│   │   ├── database/        # Database configuration and initialization
│   │   ├── models/          # SQLAlchemy models (User, Note)
│   │   ├── routers/         # API endpoints (auth, notes)
│   │   ├── schemas/         # Pydantic schemas for validation
│   │   └── main.py          # FastAPI application entry point
│   ├── tests/               # Pytest test files
│   └── Dockerfile           # Backend container configuration
└── docker-compose.yml       # Docker orchestration

```

## Prerequisites

- **Docker & Docker Compose** (required for PostgreSQL and tests)
- **Node.js 18+** for frontend
- **Python 3.13** for backend

Note: PostgreSQL runs exclusively in Docker containers. No local PostgreSQL installation is needed.

## Build & Run Commands

### Frontend (UI)
```bash
cd ui
npm install                  # Install dependencies
npm run dev                  # Start Vite dev server (auto-opens browser at :5173)
npm run build                # Build for production
npm run lint                 # Run ESLint
npm run format               # Format with Prettier
npm test                     # Run Jest tests
npm run test:coverage        # Generate coverage report
npm run test:watch           # Watch mode for development
```

### Backend
```bash
# First, start PostgreSQL container (from project root)
docker compose -f docker-compose.dev.yml up -d

# Then start backend
cd backend
uv sync                      # Install dependencies
uv run uvicorn app.main:app --reload  # Start dev server on :8000
uv run ruff check            # Run Ruff linter
uv run ruff format           # Format Python code
uv run pytest                # Run tests with coverage
uv run pytest tests/unit     # Run unit tests only
uv run pytest tests/integration  # Run integration tests only
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
docker compose -f docker-compose.dev.yml up -d  # Start PostgreSQL container
docker compose -f docker-compose.dev.yml down    # Stop PostgreSQL container
# Then run backend/frontend directly on host as shown above

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
├── hooks/          # Custom hooks (e.g., useStoreRouterSync)
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
- **Framework**: Jest + React Testing Library
- **Coverage**: 90% threshold enforced
- **Environment**: jsdom with browser API mocks
- **Structure**: Tests in `src/__tests__/` mirroring source
- **Key Patterns**:
  ```javascript
  // Use custom render with providers
  import { render } from 'test-utils/render';
  
  // Mock stores for isolated testing
  jest.mock('../features/auth/store');
  
  // Form submissions
  fireEvent.submit(form);  // Not button.click()
  ```

### Backend Testing
- **Framework**: Pytest with fixtures
- **Coverage**: 90% threshold enforced
- **Database**: PostgreSQL via testcontainers (requires Docker)
- **Test Isolation**: TRUNCATE CASCADE before/after each test
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
VITE_API_URL=/api        # API base URL (proxied in dev)
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
- **Health checks** for monitoring
- **Environment files**: `.env.docker` for dev, `.env.production` for prod
- **Volume mounting**: Persistent database storage in production

## Key Implementation Patterns

### Markdown Processing
```javascript
// Frontend: Extract title from H1
extractTitleFromMarkdown(content) // "# Title" -> "Title"

// Backend: Same logic in Python
extract_title_from_markdown(content)
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

## Development Workflow

### Local Development (Recommended)
1. Start PostgreSQL: `docker compose -f docker-compose.dev.yml up -d`
2. Start backend: `cd backend && uv run uvicorn app.main:app --reload`
3. Start frontend: `cd ui && npm run dev`
4. Access app at `http://localhost:5173`
5. API docs at `http://localhost:8000/docs`

This approach uses PostgreSQL in Docker but runs backend/frontend on host for faster development.

### Testing Changes
1. Frontend: `npm test` or `npm run test:watch`
2. Backend: `uv run pytest` or specific tests
3. Check coverage reports in `coverage_html/`

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

### Database Migrations
- PostgreSQL is the only supported database (SQLite removed)
- Currently using auto-migration via SQLAlchemy
- For production, use Alembic for migrations

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
- http://localhost:5173/ - Frontend dev server
- http://localhost:8000/ - Backend API
- http://localhost:8080/ - Docker deployment

Production:
- Configure based on deployment environment

## Important Guidelines

1. **Always test** before committing changes
2. **Follow existing patterns** in the codebase
3. **Write tests** for new functionality
4. **Update documentation** when adding features
5. **Use strong typing** in TypeScript
6. **Handle errors gracefully** with user feedback
7. **Keep components focused** and reusable
8. **Optimize for readability** over cleverness

## Additional Notes

- The application uses a **feature-first** organization pattern
- **State persistence** is handled via localStorage for auth/UI
- **Markdown title extraction** is synchronized between frontend and backend
- **Real-time updates** are not implemented (consider WebSockets for future)
- **File uploads** are not supported (markdown text only)
- **Multi-language support** is not implemented
- **Backup functionality** should be added for production use

---

Last Updated: 2025-08-23