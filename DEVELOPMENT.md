# Development Setup Guide

This guide provides detailed instructions for setting up the ParchMark monorepo for local development. The repository contains both a React frontend and a FastAPI backend that can be developed independently or together.

## 📋 Prerequisites

Before starting development, ensure you have the following installed:

### Required Software
- **Node.js 18+** and **npm** (for frontend development)
- **Python 3.12+** (for backend development)
- **Docker** and **Docker Compose** (for containerized development)
- **Git** (for version control)

### Optional but Recommended
- **UV** (Python package manager - faster than pip)
- **Make** (for using Makefile commands)
- **PostgreSQL client** (for direct database access)

## 🚀 Quick Start

### Option 1: Full Stack with Docker (Recommended)

The fastest way to get both frontend and backend running:

```bash
# Clone the repository
git clone <repository-url>
cd parchmark

# Start all services (frontend, backend, database)
make docker-up

# Or without Make
docker-compose up -d
```

**Service URLs:**
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Database: localhost:5432

### Option 2: Local Development

For active development with hot reloading:

```bash
# Terminal 1: Start backend
make dev-backend

# Terminal 2: Start frontend
make dev-frontend
```

## 🎯 Frontend Development Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
# Install all npm dependencies
npm install

# Verify installation
npm list --depth=0
```

### 3. Environment Configuration

Create a `.env.local` file in the `frontend/` directory (optional):

```env
# Frontend environment variables
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=ParchMark
```

### 4. Start Development Server

```bash
# Start Vite development server
npm run dev

# Or using Make from root directory
make dev-frontend
```

The frontend will be available at http://localhost:5173 with hot reloading enabled.

### 5. Frontend Development Commands

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code with Prettier
npm run format

# Type check
npm run type-check
```

## 🐍 Backend Development Setup

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Install UV (Python Package Manager)

UV is a fast Python package manager. Install it if you haven't already:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (restart terminal or source your shell config)
source ~/.bashrc  # or ~/.zshrc

# Verify installation
uv --version
```

### 3. Install Dependencies

```bash
# Install all dependencies including dev dependencies
uv sync

# Or install only production dependencies
uv sync --no-dev
```

### 4. Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# Database configuration
DATABASE_URL=postgresql://parchmark:parchmark@localhost:5432/parchmark

# JWT configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application settings
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

### 5. Database Setup

#### Option A: Using Docker PostgreSQL

```bash
# Start PostgreSQL container
docker run -d \
  --name parchmark-postgres \
  -e POSTGRES_USER=parchmark \
  -e POSTGRES_PASSWORD=parchmark \
  -e POSTGRES_DB=parchmark \
  -p 5432:5432 \
  postgres:15-alpine

# Initialize database (if init.sql exists)
docker exec -i parchmark-postgres psql -U parchmark -d parchmark < init.sql
```

#### Option B: Local PostgreSQL Installation

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE USER parchmark WITH PASSWORD 'parchmark';
CREATE DATABASE parchmark OWNER parchmark;
GRANT ALL PRIVILEGES ON DATABASE parchmark TO parchmark;
\q
```

### 6. Start Development Server

```bash
# Start FastAPI development server with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Make from root directory
make dev-backend
```

The backend API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### 7. Backend Development Commands

```bash
# Start development server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_main.py

# Lint code with Ruff
uv run ruff check .

# Fix linting issues
uv run ruff check . --fix

# Format code with Ruff
uv run ruff format .

# Type check with MyPy
uv run mypy .

# Security check with Bandit
uv run bandit -r app/
```

## 🐳 Docker Development

### Full Stack Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f parchmark-backend

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Remove volumes (reset database)
docker-compose down -v
```

### Individual Service Development

```bash
# Start only database
docker-compose up -d postgres

# Start backend with local database
docker-compose up -d postgres
make dev-backend

# Start frontend with containerized backend
docker-compose up -d parchmark-backend postgres
make dev-frontend
```

## 🛠️ Makefile Commands

The root-level Makefile provides convenient commands for common development tasks:

### Development Servers
```bash
make dev-frontend    # Start frontend development server
make dev-backend     # Start backend development server
```

### Building
```bash
make build-frontend  # Build frontend for production
make build-backend   # Build backend Docker image
```

### Testing
```bash
make test-frontend   # Run frontend tests
make test-backend    # Run backend tests
```

### Code Quality
```bash
make lint-frontend   # Run ESLint on frontend
make lint-backend    # Run Ruff linting on backend
```

### Docker Management
```bash
make docker-up       # Start all services with Docker Compose
make docker-down     # Stop all Docker services
```

## 🧪 Testing

### Frontend Testing

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run tests for specific file
npm test -- --testPathPattern=Auth
```

### Backend Testing

```bash
cd backend

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app

# Run tests in verbose mode
uv run pytest -v

# Run specific test file
uv run pytest tests/test_auth.py

# Run tests matching pattern
uv run pytest -k "test_create"
```

## 🔧 Development Workflow

### 1. Daily Development Routine

```bash
# Start your development session
git pull origin main
make docker-up        # Start all services
make dev-frontend     # In separate terminal
make dev-backend      # In separate terminal

# Before committing
make test-frontend
make test-backend
make lint-frontend
make lint-backend
```

### 2. Working on Frontend Only

```bash
# Start backend services
docker-compose up -d parchmark-backend postgres

# Develop frontend locally
cd frontend
npm run dev
```

### 3. Working on Backend Only

```bash
# Start database
docker-compose up -d postgres

# Develop backend locally
cd backend
uv run uvicorn app.main:app --reload
```

### 4. Full Stack Development

```bash
# Option 1: All local
make dev-backend     # Terminal 1
make dev-frontend    # Terminal 2

# Option 2: Mixed (database in Docker)
docker-compose up -d postgres
make dev-backend     # Terminal 1
make dev-frontend    # Terminal 2
```

## 🐛 Troubleshooting

### Common Issues

#### Frontend Issues

**Port 5173 already in use:**
```bash
# Kill process using port
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

**Node modules issues:**
```bash
# Clear npm cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### Backend Issues

**UV not found:**
```bash
# Reinstall UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

**Database connection issues:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

**Port 8000 already in use:**
```bash
# Kill process using port
lsof -ti:8000 | xargs kill -9

# Or use different port
uv run uvicorn app.main:app --reload --port 8001
```

#### Docker Issues

**Permission denied:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

**Out of disk space:**
```bash
# Clean up Docker
docker system prune -a
docker volume prune
```

### Getting Help

1. Check the logs:
   ```bash
   docker-compose logs -f [service-name]
   ```

2. Verify service health:
   ```bash
   curl http://localhost:8000/health
   ```

3. Check database connection:
   ```bash
   docker exec -it parchmark-postgres psql -U parchmark -d parchmark -c "SELECT 1;"
   ```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)
- [Vite Documentation](https://vitejs.dev/guide/)
- [UV Documentation](https://github.com/astral-sh/uv)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `make test-frontend && make test-backend`
5. Run linting: `make lint-frontend && make lint-backend`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📝 Development Notes

- The frontend runs on port 5173 in development, 8080 in production
- The backend runs on port 8000 in both development and production
- PostgreSQL runs on port 5432
- Hot reloading is enabled for both frontend and backend in development mode
- The backend automatically generates API documentation at `/docs`
- All services are configured to restart automatically in Docker
- Volume mounts are used for development to enable live code reloading
