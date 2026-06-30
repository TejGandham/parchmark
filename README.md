# ParchMark 📝

A modern, full-stack markdown note-taking application built with Vue 3 and FastAPI. ParchMark provides a clean, intuitive interface for creating, organizing, and managing your markdown notes with real-time preview and syntax highlighting.

[![codecov](https://codecov.io/gh/TejGandham/parchmark/graph/badge.svg?token=HKRRJA432X)](https://codecov.io/gh/TejGandham/parchmark)

## ✨ Features

- **Markdown Rendering**: GitHub Flavored Markdown rendered with `marked` and sanitized with `dompurify` (tables, task lists, strikethrough, and more)
- **Username/Password Login**: Token-based auth gate with `/auth/login`, `/auth/refresh`, and `/auth/me`, persisted via `@vueuse/core` storage
- **Backend OIDC Support**: The FastAPI backend also supports OIDC hybrid auth (local accounts and Authelia SSO)
- **User Isolation**: Each user has their own private note collection (backend, owner-scoped)
- **App Shell Navigation**: Topbar, sidebar drawer, breadcrumb trail, search box, and tag filter with read/edit segment toggle
- **Live Note Sync**: The notes list refreshes on its own when a note changes in another session, over an authenticated Server-Sent Events stream (`GET /api/notes/events`)
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode Support**: Toggle between light ("Parchment") and dark ("Desk lamp") themes via the design-token system
- **Mermaid Diagrams**: Mermaid code fences are rendered into `<div class="mermaid">` markup blocks
- **Design-Token System**: DTCG (W3C) token JSON compiled to CSS via Style Dictionary

> **Note:** In this v2 worktree the notes list and note mutations (create, edit, delete, and tag edits) use the backend notes API. `NoteResponse.tags` returns normalized persisted tags for tag chips and filters.

## 🚀 Quick Start

### Prerequisites

- **Node.js** 24 (CI pin) and npm
- **Python** 3.13+
- **Docker** and Docker Compose (REQUIRED for PostgreSQL and testing)
- **Git**

**Note:** PostgreSQL runs exclusively in Docker containers. No local PostgreSQL installation is needed.

### Option 1: Local Development

#### 1. Clone the Repository

```bash
git clone https://github.com/TejGandham/parchmark.git
cd parchmark
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install uv package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Start PostgreSQL in Docker container (from project root)
cd ..
docker compose -f docker-compose.dev.yml up -d
cd backend

# Install dependencies
uv sync

# Generate a secure 128-bit secret key (choose one method):
# Method 1: Using Python
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")

# Method 2: Using OpenSSL
# SECRET_KEY=$(openssl rand -hex 16)

# Method 3: Using /dev/urandom (Linux/Mac)
# SECRET_KEY=$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')

# Create .env file with the generated secret key
cat > .env << EOF
DATABASE_URL=postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8080
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
EOF

# Run database initialization (creates tables and seed data)
uv run python -m app.database.init_db

# Start the backend server
uv run uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

#### 4. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd ui

# Install dependencies
npm install

# Create .env file (optional, defaults are usually fine)
cat > .env << EOF
VITE_API_URL=/api
EOF

# Start the development server
npm run dev
```

The frontend will automatically open in your browser at `http://localhost:5173`

#### 5. Default Login Credentials

The database initialization creates two default users:

**Test User:**

- **Username**: `testuser`
- **Password**: `testpass123`

**Demo User:**

- **Username**: `demouser`
- **Password**: `demopass`

### Option 2: Full Docker Deployment

#### 1. Clone and Setup

```bash
git clone https://github.com/TejGandham/parchmark.git
cd parchmark
```

#### 2. Create Environment Files

Backend environment file (`backend/.env.docker`):

```bash
# Generate a secure 128-bit secret key
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")

cat > backend/.env.docker << EOF
DATABASE_URL=postgresql://parchmark_user:parchmark_password@postgres:5432/parchmark_db
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:80
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
EOF
```

Frontend environment file (`ui/.env.docker`):

```bash
cat > ui/.env.docker << EOF
VITE_API_URL=/api
USE_HTTPS=false
EOF
```

#### 3. Build and Run

```bash
# Build and start the containers
docker compose up -d

# View logs
docker compose logs -f

# Stop the containers
docker compose down
```

Access the application at `http://localhost:8080`

## 🛠️ Development Guide

### Project Structure

```
parchmark/
├── ui/                      # Frontend Vue 3 application
│   ├── src/
│   │   ├── App.vue          # Root SFC — auth gate (login vs app shell)
│   │   ├── main.ts          # createApp(App).mount("#app"); imports tokens.css + base.css
│   │   ├── features/        # Feature-based modules
│   │   │   ├── auth/        # useAuth composable, LoginView.vue
│   │   │   ├── shell/       # AppShell, AppTopbar, SidebarDrawer, UserFooter, etc.
│   │   │   └── notes/       # MarkdownProse, markdownRender, mock notes data
│   │   ├── design-system/   # base.css, generated tokens.css, tokens/, Ds* components, icons/
│   │   └── services/        # http.ts (ofetch) + auth.ts (auth) + notes.ts (notes API)
│   ├── package.json
│   └── vite.config.ts       # Vite + Vitest config (jsdom, v8 coverage)
│
├── backend/                 # Backend FastAPI application
│   ├── app/
│   │   ├── auth/            # JWT + OIDC authentication
│   │   ├── database/        # Async SQLAlchemy + PostgreSQL
│   │   ├── models/          # SQLAlchemy models (User, Note, NoteTag)
│   │   ├── routers/         # API endpoints (auth, notes, settings, health)
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # health
│   │   └── utils/           # Markdown processing
│   ├── tests/               # unit/, integration/
│   ├── migrations/          # Alembic migrations
│   └── pyproject.toml
│
├── makefiles/               # Modular make targets
├── deploy/                  # Production deployment scripts
└── docs/                    # Extended documentation
```

### Available Scripts

#### Frontend Commands

```bash
cd ui

# Development
npm run dev              # Start Vite dev server (vite --host 0.0.0.0)
npm run build            # build:tokens → vue-tsc --noEmit → vite build
npm run build:tokens     # Build DTCG design tokens (Style Dictionary)
npm run preview          # Preview production build

# Testing
npm test                 # Run tests (vitest run)
npm run test:watch       # Run tests in watch mode (vitest)
npm run test:coverage    # Run tests with v8 coverage (threshold-gated)

# Code Quality
npm run lint             # Typecheck (vue-tsc --noEmit) + prettier --check
npm run format           # Format code with Prettier
```

#### Backend Commands

```bash
cd backend

# Development
uv run uvicorn app.main:app --reload    # Start with hot reload
uv run python -m app                     # Run as module

# Testing
uv run pytest                            # Run all tests
uv run pytest tests/unit                 # Unit tests only
uv run pytest tests/integration          # Integration tests only
uv run pytest --cov=app                  # With coverage

# Code Quality
uv run ruff check                        # Lint code
uv run ruff format                       # Format code
uv run mypy app                          # Type checking
```

### Running Tests

#### Frontend Tests

```bash
cd ui
npm test                    # Run all tests
npm run test:watch          # Watch mode
npm run test:coverage       # Coverage report
npm test -- -t "MarkdownProse"  # Run tests matching a name
```

#### Backend Tests

```bash
cd backend
uv run pytest                           # Run all tests
uv run pytest -v                        # Verbose output
uv run pytest tests/unit/auth/test_auth.py  # Specific file
uv run pytest -k "test_login"           # Match test names
uv run pytest -m "auth"                 # Run marked tests
```

### Database Management

**Note: PostgreSQL runs exclusively in Docker containers. No local installation needed.**

#### Start PostgreSQL Container

```bash
# For local development (PostgreSQL only)
docker compose -f docker-compose.dev.yml up -d

# Check container status
docker compose -f docker-compose.dev.yml ps
```

#### Initialize Database

```bash
cd backend
uv run python -m app.database.init_db
```

#### User Management

The `manage_users.py` script provides commands for user management across all environments.

**Local Development** (backend on host, PostgreSQL in Docker):

```bash
# Using Makefile (recommended)
make user-create USERNAME=admin PASSWORD=SecurePassword123
make user-list
make user-update-password USERNAME=admin PASSWORD=NewPassword456
make user-delete USERNAME=olduser

# Or run directly
cd backend
uv run python scripts/manage_users.py create admin SecurePassword123
uv run python scripts/manage_users.py list
uv run python scripts/manage_users.py update-password admin NewPassword456
uv run python scripts/manage_users.py delete olduser
```

**Docker Development** (all services in containers):

```bash
# First, build and start services (if not already running)
make docker-build
make docker-up

# Using Makefile (recommended)
make user-create-docker USERNAME=admin PASSWORD=SecurePassword123
make user-list-docker

# Or use docker compose exec
docker compose exec backend python scripts/manage_users.py create admin SecurePassword123
docker compose exec backend python scripts/manage_users.py list
```

**Production** (Docker with production config):

```bash
# First, build and start production services (if not already running)
make docker-build-prod
make docker-up-prod

# Using Makefile (recommended)
make user-create-prod USERNAME=admin PASSWORD=SecurePassword123
make user-list-prod

# Or use docker compose with production file
docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py create admin SecurePassword123
docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py list
```

**Important**: After any changes to the backend Dockerfile, you must rebuild the Docker images using `make docker-build` or `make docker-build-prod` before user management commands will work.

See `make help` for all available user management commands.

#### Reset Database

```bash
cd backend
# Drop and recreate PostgreSQL tables (data will be lost)
uv run python -m app.database.init_db  # Recreate
```

## 🏗️ Architecture

### Frontend Architecture

- **Vue 3** (SFCs with `<script setup lang="ts">`) and TypeScript for type safety
- **Vite** for fast development and optimized builds (`@vitejs/plugin-vue`)
- **Custom design-token system** (DTCG JSON → CSS via Style Dictionary) plus a small set of `Ds*` SFC components and a hand-authored SVG icon factory — no UI component library
- **Vue composables** for state (no Pinia/Vuex); the auth store is a composable singleton (`useAuth`) persisted via `@vueuse/core`
- **No Vue Router** — top-level routing is an auth gate in `App.vue` (login vs app shell); in-app navigation is `ref` toggles in `AppShell.vue`
- **`marked`** (GFM) for markdown parsing + **`dompurify`** for sanitization
- **`ofetch`** HTTP client with a single refresh-and-retry policy in `services/http.ts`
- **Live note refresh** via an authenticated Server-Sent Events client (`services/noteEvents.ts` + `useNoteEvents`) that debounces a notes-list refetch on backend change events
- **Vitest** + **`@vue/test-utils`** (jsdom) for testing

### Backend Architecture

- **FastAPI** for high-performance async API
- **SQLAlchemy 2.0** (async via asyncpg; a deprecated sync engine + `init_db` `create_all` remain for schema bootstrap) with PostgreSQL
- **Pydantic** for data validation
- **JWT + OIDC** hybrid authentication: local JWT is HS256, the OIDC JWT path is RS256 (JWKS); Authelia opaque tokens validated via the userinfo endpoint (local + Authelia SSO)
- **Bcrypt** for password hashing
- **Postgres LISTEN/NOTIFY → SSE** note-change events (`GET /api/notes/events`)
- **CalVer** versioning (`YYYYMMDD.HHMM.sha`)
- **uvicorn** ASGI server

### Key Design Patterns

1. **Feature-First Organization**: Code organized by features rather than file types
2. **Composable Singleton State**: Shared state via Vue composables with module-level refs (`useAuth`)
3. **Repository Pattern**: Database operations abstracted in models
4. **Dependency Injection**: FastAPI's dependency system for clean code; the frontend injects auth hooks into `http.ts` (`setAuthHooks`) to avoid an import cycle
5. **Type Safety**: Full TypeScript and Python type hints

## 📦 API Documentation

### Authentication Endpoints

| Method | Endpoint            | Description                                 |
|-|-|-|
| POST   | `/api/auth/login`   | User login, returns access & refresh tokens |
| POST   | `/api/auth/refresh` | Refresh access token using refresh token    |
| POST   | `/api/auth/logout`  | User logout                                 |
| GET    | `/api/auth/me`      | Get current user info                       |

### Notes Endpoints

| Method | Endpoint                  | Description                                       |
|-|-|-|
| GET    | `/api/notes/`             | List all user's notes                             |
| POST   | `/api/notes/`             | Create a new note                                 |
| GET    | `/api/notes/{id}`         | Get specific note                                 |
| PUT    | `/api/notes/{id}`         | Update a note                                     |
| DELETE | `/api/notes/{id}`         | Delete a note                                     |
| GET    | `/api/notes/events`       | SSE stream of per-user note-change events         |

### Settings Endpoints

| Method | Endpoint                         | Description                        |
|-|-|-|
| GET    | `/api/settings/user-info`        | Account info + note count          |
| POST   | `/api/settings/change-password`  | Change password (local users only) |
| GET    | `/api/settings/export-notes`     | Streaming ZIP export of all notes  |
| DELETE | `/api/settings/delete-account`   | Delete account and all notes       |

### Request/Response Examples

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Create Note

```bash
curl -X POST http://localhost:8000/api/notes/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Note",
    "content": "# My Note\n\nThis is the content"
  }'
```

## 🐳 Docker Deployment

### Development with Docker

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# View logs
docker compose logs -f frontend
docker compose logs -f backend

# Stop services
docker compose down

# Remove volumes (reset data)
docker compose down -v
```

### Production Deployment

ParchMark deploys to k3s automatically via Forgejo CI:

```bash
# Push to main branch (triggers Forgejo CI pipeline)
git push origin main

# CI automatically: runs tests → builds images → deploys to k3s via kubectl
```

The Forgejo CI pipeline will:
- Run full test suite (UI + backend)
- Build and push Docker images to Forgejo registry (SHA-tagged)
- Deploy to k3s via `kubectl rollout restart`
- Verify health checks

See `deploy/SERVER_SETUP.md` for initial server configuration.

### Docker Environment Variables

Create `.env.production` files:

Backend (`backend/.env.production`):

```env
DATABASE_URL=postgresql://username:password@postgres:5432/parchmark
SECRET_KEY=<generate-128-bit-key-see-instructions-below>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_ORIGINS=https://notes.example.com
ENVIRONMENT=production
```

**Generating a Secure 128-bit Secret Key:**

```bash
# Method 1: Python (recommended)
python -c "import secrets; print(secrets.token_hex(16))"

# Method 2: OpenSSL
openssl rand -hex 16

# Method 3: /dev/urandom (Linux/Mac)
head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n'
```

Frontend (`ui/.env.production`):

```env
VITE_API_URL=https://api.example.com
USE_HTTPS=true
```

## 🔧 Configuration

### Environment Variables

#### Frontend Environment Variables

| Variable                       | Description                | Default |
|-|-|-|
| `VITE_API_URL`                 | Backend API URL            | `/api`  |
| `VITE_TOKEN_WARNING_SECONDS`   | Token expiry warning (sec) | `60`    |
| `VITE_OIDC_ISSUER_URL`        | OIDC provider URL          | —       |
| `VITE_OIDC_CLIENT_ID`         | OIDC client ID             | —       |
| `VITE_OIDC_REDIRECT_URI`      | OIDC callback URL          | —       |
| `VITE_OIDC_LOGOUT_REDIRECT_URI` | Post-logout redirect     | —       |

#### Backend Environment Variables

| Variable                      | Description                          | Default                                                   |
|-|-|-|
| `DATABASE_URL`                | Database connection string           | `postgresql://username:password@localhost:5432/parchmark` |
| `SECRET_KEY`                  | JWT signing key (128-bit hex string) | (must be set - see generation instructions)               |
| `ALGORITHM`                   | JWT algorithm                        | `HS256`                                                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration                     | `30`                                                      |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token expiration             | `7`                                                       |
| `ALLOWED_ORIGINS`             | CORS origins                         | `http://localhost:5173`                                   |
| `HOST`                        | Server host                          | `0.0.0.0`                                                 |
| `PORT`                        | Server port                          | `8000`                                                    |
| `ENVIRONMENT`                 | Environment mode                     | `development`                                             |
| `OIDC_ISSUER_URL`             | OIDC issuer URL                      | —                                                         |
| `OIDC_AUDIENCE`               | OIDC audience identifier             | —                                                         |
| `OIDC_USERNAME_CLAIM`         | OIDC claim for username              | `preferred_username`                                      |

### Nginx Configuration

The frontend uses Nginx for production serving. Configuration files:

- `ui/nginx.http.conf` - HTTP configuration
- `ui/nginx.https.conf` - HTTPS configuration

## 🧪 Testing

**Important:** Backend tests require PostgreSQL and Docker to be running. Tests use testcontainers to create isolated PostgreSQL instances.

### Test Coverage Requirements

Both frontend and backend enforce 90% test coverage:

- Statements: 90%
- Branches: 90%
- Functions: 90%
- Lines: 90%

### Running Coverage Reports

Frontend:

```bash
cd ui
npm run test:coverage
# Open coverage/index.html in browser
```

Backend:

```bash
cd backend
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## 🚨 Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port
lsof -i :5173  # Frontend
lsof -i :8000  # Backend

# Kill process
kill -9 PID
```

#### Database Connection Error

```bash
# PostgreSQL runs in Docker - ensure container is running
# Check container status
docker compose -f docker-compose.dev.yml ps

# Restart container if needed
docker compose -f docker-compose.dev.yml restart postgres

# View container logs for issues
docker compose -f docker-compose.dev.yml logs postgres
```

#### Docker Build Fails

```bash
# Clean Docker cache
docker system prune -a
docker compose build --no-cache
```

#### Node Modules Issues

```bash
cd ui
rm -rf node_modules package-lock.json
npm install
```

#### Python Dependencies Issues

```bash
cd backend
rm -rf .venv uv.lock
uv sync
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Standards

- Write tests for new features (90% coverage required)
- Follow existing code style and patterns
- Update documentation as needed
- Use conventional commits format
- Run linters before committing

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Vue 3 and FastAPI
- Custom design-token system compiled with Style Dictionary
- Markdown rendering by `marked` + `dompurify`
- Hand-authored SVG icons (no icon library)
- Package management by uv (backend) and npm (frontend)

## 📞 Support

For issues, questions, or suggestions:

- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review the [CLAUDE.md](CLAUDE.md) file for detailed technical information

---

**Happy Note Taking! 📝**
