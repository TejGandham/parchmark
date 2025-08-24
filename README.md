# ParchMark 📝

A modern, full-stack markdown note-taking application built with React and FastAPI. ParchMark provides a clean, intuitive interface for creating, organizing, and managing your markdown notes with real-time preview and syntax highlighting.

![ParchMark Logo](ui/assets/images/parchmark.svg)

## ✨ Features

- **Markdown Editor**: Full-featured markdown editor with live preview
- **GitHub Flavored Markdown**: Support for tables, task lists, strikethrough, and more
- **Secure Authentication**: JWT-based authentication with bcrypt password hashing
- **User Isolation**: Each user has their own private note collection
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Dark Mode Support**: Toggle between light and dark themes
- **Mermaid Diagrams**: Render flowcharts and diagrams in your notes
- **Auto-save**: Changes are automatically saved as you type
- **Search & Organization**: Quickly find and organize your notes

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.13+
- **Docker** and Docker Compose (REQUIRED for PostgreSQL and testing)
- **Git**

**Note:** PostgreSQL runs exclusively in Docker containers. No local PostgreSQL installation is needed.

### Option 1: Local Development

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/parchmark.git
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

#### 4. Default Login Credentials

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
git clone https://github.com/yourusername/parchmark.git
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
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the containers
docker-compose down
```

Access the application at `http://localhost:8080`

## 🛠️ Development Guide

### Project Structure

```
parchmark/
├── ui/                      # Frontend React application
│   ├── src/
│   │   ├── features/        # Feature-based modules
│   │   │   ├── auth/        # Authentication components
│   │   │   ├── notes/       # Notes management
│   │   │   └── ui/          # UI components
│   │   ├── services/        # API and utilities
│   │   ├── styles/          # Global styles and theme
│   │   └── __tests__/       # Test files
│   ├── package.json         # Frontend dependencies
│   └── vite.config.ts       # Vite configuration
│
├── backend/                 # Backend FastAPI application
│   ├── app/
│   │   ├── auth/            # Authentication logic
│   │   ├── database/        # Database configuration
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routers/         # API endpoints
│   │   ├── schemas/         # Pydantic schemas
│   │   └── main.py          # FastAPI app
│   ├── tests/               # Backend tests
│   └── pyproject.toml       # Python dependencies
│
└── docker-compose.yml       # Docker orchestration
```

### Available Scripts

#### Frontend Commands

```bash
cd ui

# Development
npm run dev              # Start dev server with hot reload
npm run build            # Build for production
npm run preview          # Preview production build

# Testing
npm test                 # Run tests
npm run test:watch       # Run tests in watch mode
npm run test:coverage    # Generate coverage report

# Code Quality
npm run lint             # Run ESLint
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
npm test -- --testNamePattern="NoteContent"  # Run specific test
```

#### Backend Tests

```bash
cd backend
uv run pytest                           # Run all tests
uv run pytest -v                        # Verbose output
uv run pytest tests/unit/test_auth.py  # Specific file
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

#### Create Admin User

```bash
cd backend
uv run python scripts/manage_users.py create-admin
```

#### Reset Database

```bash
cd backend
# Drop and recreate PostgreSQL tables (data will be lost)
uv run python -m app.database.init_db  # Recreate
```

## 🏗️ Architecture

### Frontend Architecture

- **React 18** with TypeScript for type safety
- **Vite** for fast development and optimized builds
- **Chakra UI v2** for consistent, accessible components
- **Zustand** for state management with persistence
- **React Router v7** for navigation
- **React Markdown** with GFM for rendering

### Backend Architecture

- **FastAPI** for high-performance async API
- **SQLAlchemy** ORM with PostgreSQL (via Docker)
- **Pydantic** for data validation
- **JWT** for stateless authentication
- **Bcrypt** for password hashing
- **uvicorn** ASGI server

### Key Design Patterns

1. **Feature-First Organization**: Code organized by features rather than file types
2. **Store Pattern**: Centralized state management with Zustand
3. **Repository Pattern**: Database operations abstracted in models
4. **Dependency Injection**: FastAPI's dependency system for clean code
5. **Type Safety**: Full TypeScript and Python type hints

## 📦 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User login, returns JWT token |
| POST | `/api/auth/logout` | User logout |
| GET | `/api/auth/me` | Get current user info |

### Notes Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notes/` | List all user's notes |
| POST | `/api/notes/` | Create a new note |
| GET | `/api/notes/{id}` | Get specific note |
| PUT | `/api/notes/{id}` | Update a note |
| DELETE | `/api/notes/{id}` | Delete a note |

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
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f frontend
docker-compose logs -f backend

# Stop services
docker-compose down

# Remove volumes (reset data)
docker-compose down -v
```

### Production Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# With custom domain
DOMAIN=notes.example.com docker-compose -f docker-compose.prod.yml up -d
```

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

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `/api` |

#### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `postgresql://username:password@localhost:5432/parchmark` |
| `SECRET_KEY` | JWT signing key | (must be set) |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |
| `ALLOWED_ORIGINS` | CORS origins | `http://localhost:5173` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `ENVIRONMENT` | Environment mode | `development` |

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
docker-compose build --no-cache
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

- Built with React and FastAPI
- UI components from Chakra UI
- Markdown rendering by react-markdown
- Icons from FontAwesome
- Package management by uv

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review the [CLAUDE.md](CLAUDE.md) file for detailed technical information

---

**Happy Note Taking! 📝**