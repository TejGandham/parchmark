# ParchMark

ParchMark is a modern, full-stack markdown note-taking application inspired by ancient papyrus and modern markdown. This monorepo contains both the frontend React application and the backend FastAPI service, providing a complete solution for creating, editing, and organizing your notes with markdown formatting.

## 🏗️ Monorepo Structure

```
parchmark/
├── frontend/           # React TypeScript SPA
│   ├── src/           # React application source
│   ├── public/        # Static assets
│   ├── tests/         # Frontend tests
│   ├── Dockerfile     # Frontend container
│   └── package.json   # Frontend dependencies
├── backend/           # Python FastAPI API
│   ├── app/          # FastAPI application
│   ├── tests/        # Backend tests
│   ├── Dockerfile    # Backend container
│   └── pyproject.toml # Backend dependencies
├── Makefile          # Development commands
├── docker-compose.yml # Full stack orchestration
└── README.md         # This file
```

## ✨ Features

### Frontend Features
- 📝 Create, edit, and delete notes
- 🔄 Switch between edit and preview modes
- 🌙 Dark/light mode toggle
- 📱 Responsive layout with collapsible sidebar
- 🎨 Elegant styling with refined color scheme
- 📊 Beautiful markdown rendering
- 🔒 User authentication with protected routes

### Backend Features
- 🚀 FastAPI REST API with automatic OpenAPI documentation
- 🔐 JWT-based authentication system
- 📊 PostgreSQL database with SQLAlchemy ORM
- 🔄 CRUD operations for notes and user management
- 🛡️ Input validation with Pydantic models
- 🧪 Comprehensive test coverage

## 🛠️ Technologies

### Frontend Stack
- **React 18** with TypeScript
- **Vite** for build system and development server
- **Chakra UI** for component library
- **Zustand** for state management
- **React Router** for client-side routing
- **React Markdown** with RemarkGFM for rendering
- **Jest** and React Testing Library for testing

### Backend Stack
- **FastAPI** for REST API framework
- **SQLAlchemy** for database ORM
- **PostgreSQL** for data persistence
- **Pydantic** for data validation
- **JWT** for authentication
- **UV** for package management
- **Pytest** for testing

### DevOps & Tools
- **Docker** and Docker Compose for containerization
- **GitHub Actions** for CI/CD
- **Ruff** and **MyPy** for Python code quality
- **ESLint** and **Prettier** for JavaScript/TypeScript code quality

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.12+**
- **Docker** and Docker Compose
- **UV** (for Python package management)

### Option 1: Docker Compose (Recommended)

Start the entire stack with one command:

```bash
# Clone the repository
git clone https://github.com/yourusername/parchmark.git
cd parchmark

# Start all services (frontend, backend, database)
make docker-up
```

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 2: Local Development

#### Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at http://localhost:5173

#### Backend Development

```bash
# Navigate to backend directory
cd backend

# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Start development server
uv run uvicorn app.main:app --reload
```

Backend API will be available at http://localhost:8000

## 📋 Makefile Commands

The root-level Makefile provides convenient commands for development:

### Development
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

## 🐳 Docker Deployment

### Development Environment

```bash
# Start all services in development mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Build and start production containers
docker-compose -f docker-compose.yml up -d --build

# Scale services if needed
docker-compose up -d --scale backend=3
```

### Service URLs
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (PostgreSQL)

## 🧪 Testing

### Frontend Testing
```bash
cd frontend

# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Backend Testing
```bash
cd backend

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_main.py
```

## 🔧 Development Setup

For detailed development setup instructions, see [DEVELOPMENT.md](./DEVELOPMENT.md).

## 📚 API Documentation

The backend provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🚦 CI/CD

GitHub Actions workflows are configured for:

### Frontend CI (`tmp-workflows/frontend-ci.yml`)
- ESLint code quality checks
- Prettier formatting validation
- TypeScript type checking
- Jest test execution with coverage
- Production build verification

### Backend CI (`tmp-workflows/backend-ci.yml`)
- Ruff linting and formatting
- MyPy type checking
- Pytest execution with coverage
- Security scanning with Bandit
- Docker build and health checks

**Note**: Workflow files are in `tmp-workflows/` and need to be manually moved to `.github/workflows/` for activation.

## 🔮 Future Enhancements

### Frontend
- Enhanced markdown editor with toolbar
- Real-time collaborative editing
- Advanced search and filtering
- Mobile-optimized PWA experience
- Offline support with service workers

### Backend
- Real-time WebSocket connections
- Advanced user roles and permissions
- Note sharing and collaboration features
- Full-text search with Elasticsearch
- File attachment support
- API rate limiting and caching

### Infrastructure
- Kubernetes deployment manifests
- Monitoring with Prometheus and Grafana
- Automated database migrations
- Multi-environment configuration
- CDN integration for static assets

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgements

### Frontend
- [React](https://reactjs.org/) - UI library
- [Chakra UI](https://chakra-ui.com/) - Component library
- [Vite](https://vitejs.dev/) - Build tool
- [Zustand](https://github.com/pmndrs/zustand) - State management

### Backend
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [UV](https://github.com/astral-sh/uv) - Package manager
- [PostgreSQL](https://www.postgresql.org/) - Database

### DevOps
- [Docker](https://www.docker.com/) - Containerization
- [GitHub Actions](https://github.com/features/actions) - CI/CD
- [Ruff](https://github.com/astral-sh/ruff) - Python linting

