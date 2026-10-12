#!/bin/bash
# =============================================================================
# ParchMark Backend Docker Entrypoint
# =============================================================================
#
# This entrypoint script handles database migrations before starting the app.
# Migrations run automatically when APPLY_MIGRATIONS=true (default: false).
#
# Usage:
#   APPLY_MIGRATIONS=true  - Run migrations on startup (for deployments)
#   APPLY_MIGRATIONS=false - Skip migrations (for scaling/replicas)
#
# =============================================================================

set -e

# Run migrations if APPLY_MIGRATIONS is set to true
if [ "${APPLY_MIGRATIONS:-false}" = "true" ]; then
    echo "========================================"
    echo "Running database migrations..."
    echo "========================================"
    
    # Run alembic migrations
    # Alembic is idempotent - safe to run multiple times
    alembic upgrade head
    
    echo "========================================"
    echo "Migrations complete."
    echo "========================================"
fi

# Execute the main command (e.g., python -m app)
exec "$@"
