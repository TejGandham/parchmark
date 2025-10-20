# Stage 1: Builder stage using official uv image with Python 3.13 on Debian Trixie
FROM ghcr.io/astral-sh/uv:python3.13-trixie as builder

WORKDIR /app

# Copy dependency files and lockfile first for better caching
COPY pyproject.toml ./
COPY uv.lock ./

# First sync: Install dependencies only (without the project itself)
# This layer is cached when only app code changes
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code and scripts
COPY app ./app
COPY scripts ./scripts

# Second sync: Install the project itself in non-editable mode
# --no-editable ensures files are copied to site-packages instead of using .pth file
RUN uv sync --frozen --no-dev --no-editable

# Stage 2: Final stage using matching Python version
FROM python:3.13-slim-trixie

WORKDIR /app

# Copy the complete virtual environment with app and all dependencies
COPY --from=builder /app/.venv /app/.venv

# Copy scripts directory for user management and other utilities
COPY --from=builder /app/scripts /app/scripts

# Don't copy env files in production - they should be mounted or provided via env_file
# For development, you can mount .env.docker or .env.production at runtime

# Activate the virtual environment by adding it to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application as a Python module
# The app is installed in the venv and can be run as a module
CMD ["python", "-m", "app"]
