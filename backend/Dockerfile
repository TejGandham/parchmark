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

# Copy Alembic configuration and migrations for database migrations
COPY alembic.ini ./
COPY migrations ./migrations

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

# Copy Alembic configuration and migrations
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/migrations /app/migrations

# Copy entrypoint script
COPY --from=builder /app/scripts/docker-entrypoint.sh /docker-entrypoint.sh

# Don't copy env files in production - they should be mounted or provided via env_file
# For development, you can mount .env.docker or .env.production at runtime

# Version info injected at build time
ARG GIT_SHA=dev
ARG BUILD_DATE=unknown
ARG APP_VERSION=dev

# Activate the virtual environment by adding it to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"
ENV GIT_SHA=$GIT_SHA
ENV BUILD_DATE=$BUILD_DATE
ENV APP_VERSION=$APP_VERSION

# Expose the port the app runs on
EXPOSE 8000

# Use entrypoint for migrations, CMD for the app
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "-m", "app"]
