# Stage 1: Builder stage using official uv image with Python 3.13 on Debian Trixie
FROM ghcr.io/astral-sh/uv:python3.13-trixie as builder

WORKDIR /app

# Copy all application files needed to build the wheel
COPY pyproject.toml ./
COPY app ./app
COPY main.py ./

# Build the application wheel (includes the app code itself)
RUN uv build --wheel --out-dir /wheels

# Install the wheel with all dependencies
# uv sync automatically creates .venv if it doesn't exist
RUN uv sync --frozen --no-dev --find-links /wheels

# Stage 2: Final stage using matching Python version
FROM python:3.13-slim-trixie

WORKDIR /app

# Copy the complete virtual environment with app and all dependencies
COPY --from=builder /app/.venv /app/.venv

# Copy only runtime configuration files if needed
COPY .env.docker ./.env

# Activate the virtual environment by adding it to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# The app is installed in the venv, no source code needed
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
