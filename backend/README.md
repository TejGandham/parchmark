# ParchMark Backend

FastAPI-based backend for the ParchMark markdown note-taking application.

## Features

- FastAPI REST API
- JWT-based authentication
- PostgreSQL database with SQLAlchemy ORM
- User management and note CRUD operations
- UV package management
- Code quality tools (Ruff, MyPy)
- Comprehensive testing with pytest

## Development Setup

### Prerequisites

- Python 3.12+
- UV package manager
- PostgreSQL database

### Installation

1. Install UV if not already installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up environment variables (create `.env` file):
   ```bash
   DATABASE_URL=postgresql://parchmark:parchmark@localhost:5432/parchmark
   SECRET_KEY=your-secret-key-here
   ```

4. Run the development server:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app
```

## Code Quality

```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy .
```
