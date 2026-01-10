#!/bin/bash
# Simple migration script for production deployments
# Used by deploy.yml GitHub Actions workflow
#
# This script is idempotent - running it multiple times is safe.
# Alembic only applies migrations that haven't been applied yet.
#
# Prerequisites: Dependencies must be pre-installed in the container.
# Production containers have deps installed via Dockerfile.

set -euo pipefail

# Change to the app directory (where alembic.ini lives)
cd /app

# Verify alembic is available (deps should be pre-installed in production)
if ! command -v alembic &> /dev/null; then
    echo "Error: alembic not found. Dependencies may not be installed."
    exit 1
fi

echo "Running database migrations..."

# Run migrations
alembic upgrade head

echo "Migrations complete."
