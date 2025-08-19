# Stage 1: Builder stage using official uv image with Python 3.13 on Debian Trixie
FROM ghcr.io/astral-sh/uv:python3.13-trixie as builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies and the project using uv
# This creates a virtual environment with all dependencies
RUN uv sync --frozen --no-dev

# Stage 2: Final stage using matching Python version
FROM python:3.13-slim-trixie

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
COPY . .

# Activate the virtual environment by adding it to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
