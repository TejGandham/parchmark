# ParchMark Backend API

A FastAPI-based backend for the ParchMark note-taking application, providing JWT + OIDC hybrid authentication, note management, AI-powered similarity search, and user settings.

## 🚀 Quick Start

### Prerequisites

- Python 3.13 or higher
- Docker and Docker Compose (REQUIRED for PostgreSQL and tests)
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

Note: PostgreSQL runs in a Docker container. No local installation needed.

### Installation & Setup

1. **Install uv (if not already installed):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

3. **Install dependencies:**
   ```bash
   uv sync --dev
   ```

4. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   ```

5. **Start PostgreSQL in Docker:**
   ```bash
   # From the project root directory
   docker compose -f docker-compose.dev.yml up -d
   
   # Or if you're in the backend directory
   docker compose -f ../docker-compose.dev.yml up -d
   ```

6. **Configure environment variables:**
   - Copy `.env.example` to `.env` and update the `DATABASE_URL` if needed
   - Default uses: `postgresql://postgres:postgres@localhost:5432/parchmark`
   - Update the `SECRET_KEY` for production use

7. **Start the server:**
   ```bash
   make run
   # or
   uv run python -m app
   ```

The server will start at `http://localhost:8000` with the following endpoints available:
- **API Documentation:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/health

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── __main__.py          # Application entry point
│   ├── main.py              # FastAPI app configuration
│   ├── version.py           # CalVer version (YYYYMMDD.HHMM.sha)
│   ├── auth/
│   │   ├── auth.py          # JWT utilities and password hashing
│   │   ├── dependencies.py  # Authentication dependencies
│   │   └── oidc_validator.py # OIDC token validation (Authelia)
│   ├── database/
│   │   ├── database.py      # Async PostgreSQL configuration
│   │   ├── init_db.py       # Database initialization
│   │   └── seed.py          # Database seeding utilities
│   ├── models/
│   │   └── models.py        # SQLAlchemy models (User, Note w/ pgvector)
│   ├── routers/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── notes.py         # Notes CRUD + access tracking + similar
│   │   ├── settings.py      # User settings, export, account management
│   │   └── health.py        # Health check endpoint
│   ├── schemas/
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/
│   │   ├── embeddings.py    # OpenAI embedding generation
│   │   ├── health_service.py # Health check logic
│   │   └── backfill.py      # Backfill embeddings for existing notes
│   ├── utils/
│   │   └── markdown.py      # Markdown processing (mirrors frontend)
│   └── middleware/           # Request middleware
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── migrations/              # Alembic database migrations
├── pyproject.toml
└── README.md
```

## 🔐 Authentication

The API supports hybrid authentication — local JWT and OIDC (via Authelia):

- **Local Auth:** JWT (HS256) with bcrypt password hashing
- **OIDC Auth:** Authelia SSO (opaque or JWT access tokens)
- **Access Token Expiration:** 30 minutes (configurable)
- **Refresh Token Expiration:** 7 days (configurable)
- **OIDC Validator:** Shared httpx client, discovery/JWKS caching with double-checked locking
- **Authelia:** Issues opaque tokens (`authelia_at_...`) validated via userinfo endpoint

### Default Test Users

Created by database initialization:
- **Username:** `testuser` / **Password:** `testpass123`
- **Username:** `demouser` / **Password:** `demopass`

## 📚 API Endpoints

All endpoints are prefixed with `/api`.

### Authentication (`/api/auth`)

| Method | Endpoint           | Description                         |
| ------ | ------------------ | ----------------------------------- |
| POST   | `/api/auth/login`  | Login, returns access+refresh tokens |
| POST   | `/api/auth/refresh`| Refresh access token                |
| POST   | `/api/auth/logout` | Signal logout (stateless)           |
| GET    | `/api/auth/me`     | Current user info                   |

### Notes (`/api/notes`)

| Method | Endpoint                    | Description                              |
| ------ | --------------------------- | ---------------------------------------- |
| GET    | `/api/notes/`               | List user's notes                        |
| POST   | `/api/notes/`               | Create note                              |
| GET    | `/api/notes/{id}`           | Get note                                 |
| PUT    | `/api/notes/{id}`           | Update note                              |
| DELETE | `/api/notes/{id}`           | Delete note                              |
| POST   | `/api/notes/{id}/access`    | Track note access (for "For You" scoring)|
| GET    | `/api/notes/{id}/similar`   | Similar notes via cosine similarity      |

### Settings (`/api/settings`)

| Method | Endpoint                          | Description                        |
| ------ | --------------------------------- | ---------------------------------- |
| GET    | `/api/settings/user-info`         | Account info + note count          |
| POST   | `/api/settings/change-password`   | Change password (local users only) |
| GET    | `/api/settings/export-notes`      | Streaming ZIP of all notes         |
| DELETE | `/api/settings/delete-account`    | Delete account and all notes       |

### Health (`/api/health`)

| Method | Endpoint       | Description                           |
| ------ | -------------- | ------------------------------------- |
| GET    | `/api/health`  | Health check with DB status + version |

## 🔧 Configuration

The application uses environment variables for configuration. Key settings in `.env`:

```env
# Database (PostgreSQL REQUIRED)
DATABASE_URL=postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db

# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080

# Server
HOST=0.0.0.0
PORT=8000

# OIDC (optional — enables Authelia SSO)
OIDC_ISSUER_URL=https://auth.engen.tech
OIDC_AUDIENCE=parchmark
OIDC_USERNAME_CLAIM=preferred_username
OIDC_OPAQUE_TOKEN_PREFIX=           # e.g. "authelia_at_"
OIDC_DISCOVERY_URL=                 # optional: internal cluster DNS

# Embeddings (optional — similarity search disabled if absent)
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small
```

## 🌐 Frontend Integration

### CORS Configuration

The API is configured to accept requests from common frontend development servers:
- `http://localhost:3000` (Create React App)
- `http://localhost:5173` (Vite)
- `http://localhost:8080` (Docker/other)

### Authentication Flow

1. **Login:** POST to `/auth/login` with username/password
2. **Store Tokens:** Save both `access_token` and `refresh_token` from the response
3. **Authenticated Requests:** Include `Authorization: Bearer <access_token>` header
4. **Token Refresh:** When access token expires (30 min), use refresh token to get new tokens via `/auth/refresh`
5. **Re-authentication:** If refresh token expires (7 days), user must log in again

### Frontend Store Integration

The API endpoints are designed to match the existing frontend store operations:

**Auth Store (`src/features/auth/store/auth.ts`):**
- `login()` → POST `/api/auth/login`
- `logout()` → POST `/api/auth/logout` + client-side token removal
- `getCurrentUser()` → GET `/api/auth/me`

**Notes Store (`src/features/notes/store/notes.ts`):**
- `fetchNotes()` → GET `/api/notes`
- `createNote()` → POST `/api/notes`
- `updateNote()` → PUT `/api/notes/{id}`
- `deleteNote()` → DELETE `/api/notes/{id}`

### Error Handling

The API returns consistent error responses:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## 🗄️ Database

**PostgreSQL is the only supported database.** SQLite support has been removed.

### Models

**User Model:**
- `id`: Integer (Primary Key)
- `username`: String (Unique)
- `password_hash`: String
- `created_at`: DateTime

**Note Model:**
- `id`: String (Primary Key, UUID)
- `user_id`: Integer (Foreign Key to User)
- `title`: String
- `content`: Text
- `created_at`: DateTime
- `updated_at`: DateTime
- `access_count`: Integer (for "For You" scoring)
- `last_accessed_at`: DateTime
- `embedding`: Vector(1536) (pgvector, for similarity search)

### Database Operations

**Initialize Database:**
```python
from app.database.init_db import init_database
init_database()
```

**Seed with Default Data:**
```python
from app.database.seed import seed_database
seed_database()
```

**Reset and Seed (Development):**
```bash
python -c "from app.database.seed import reset_and_seed_database; reset_and_seed_database()"
```

## 🧪 Development

### Running in Development Mode

```bash
python -m app
```

This starts the server with:
- Auto-reload enabled
- Debug logging
- CORS configured for local development
- Database auto-initialization

## 🧪 Testing

**Important:** Tests require PostgreSQL and Docker to be running. The test suite uses testcontainers to create isolated PostgreSQL instances for each test.

### Running Tests

The project uses pytest with pytest-xdist for parallel test execution:

```bash
# Run all tests with coverage (parallel execution)
make test

# Run tests without coverage (faster)
make test-fast

# Generate HTML coverage report
make test-cov

# Run specific test file
uv run pytest tests/unit/auth/test_auth.py

# Run with verbose output
uv run pytest -vv
```

### Code Quality

The project uses ruff for linting/formatting and mypy for type checking:

```bash
# Run linting
make lint

# Format code
make format

# Check formatting without changes
make format-check

# Run type checking
make typecheck

# Run all pre-commit hooks
make pre-commit
```

### Pre-commit Hooks

Pre-commit hooks run automatically on git commit. They include:
- Ruff linting and formatting
- MyPy type checking
- Trailing whitespace removal
- YAML/JSON/TOML validation

To run manually:
```bash
uv run pre-commit run --all-files
```

### Testing the API

1. **Using the Interactive Docs:**
   - Visit http://localhost:8000/docs
   - Use the "Try it out" feature for each endpoint

2. **Using curl:**
   ```bash
   # Login
   curl -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "user", "password": "password"}'

   # Get notes (replace TOKEN with actual token)
   curl -X GET "http://localhost:8000/notes" \
        -H "Authorization: Bearer TOKEN"
   ```

3. **Using the Frontend:**
   - Start the frontend development server
   - The existing UI should work with the backend API

## 🚀 Production Deployment

### Environment Configuration

1. **Generate a secure SECRET_KEY:**
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. **Update `.env` for production:**
   ```env
   SECRET_KEY=your-generated-secure-key
   DEBUG=false
   DATABASE_URL=your-production-database-url
   ALLOWED_ORIGINS=https://your-frontend-domain.com
   ```

### Security Considerations

- Change the default `SECRET_KEY` in production
- Use HTTPS in production
- Configure proper CORS origins
- Ensure PostgreSQL is properly configured and secured
- Implement rate limiting for production use
- Set up proper logging and monitoring

## 📝 Notes

- The API automatically creates database tables on startup
- Default test data is seeded automatically for development
- All timestamps are in ISO 8601 format
- Note titles are automatically extracted from markdown H1 headers
- User passwords are securely hashed using bcrypt
- JWT tokens are stateless and contain user information

## 🤝 Contributing

When making changes to the API:

1. Update the corresponding Pydantic schemas if changing data structures
2. Update this README if adding new endpoints or changing existing ones
3. Test with both the interactive docs and the frontend application
4. Ensure CORS settings accommodate your development environment

---

For questions or issues, please refer to the interactive API documentation at `/docs` when the server is running.
