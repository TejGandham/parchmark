# Stage 1: Builder stage using official uv image with Python 3.13 on Debian Trixie
FROM ghcr.io/astral-sh/uv:python3.13-trixie as builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Create a virtual environment and install dependencies
RUN uv venv && uv pip compile pyproject.toml -o requirements.txt

# Build wheels for all dependencies
RUN uv pip wheel -r requirements.txt --wheel-dir /wheels

# Stage 2: Final stage using matching Python version
FROM python:3.13-slim-trixie

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /wheels /wheels

# Install dependencies from wheels (no network needed, no build tools needed)
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
