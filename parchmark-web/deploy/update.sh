#!/bin/bash
# =============================================================================
# ParchMark Production Update Script
# =============================================================================
#
# This script updates ParchMark to the latest version by pulling new Docker
# images from GHCR and recreating containers.
#
# Usage:
#   ./deploy/update.sh           # Run from project root
#   ./update.sh                  # Run from deploy directory
#
# Prerequisites:
#   - Docker and Docker Compose installed
#   - .env.deploy file with GHCR credentials
#   - docker-compose.prod.yml configured
#
# =============================================================================

set -euo pipefail

# Determine script and project directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# If script is run from project root via ./deploy/update.sh
if [[ ! -f "${PROJECT_DIR}/docker-compose.prod.yml" ]]; then
    PROJECT_DIR="$SCRIPT_DIR"
fi

LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/update.log"
ENV_FILE="${PROJECT_DIR}/.env.deploy"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"

# =============================================================================
# Helper Functions
# =============================================================================

log() {
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${timestamp}] $1" | tee -a "$LOG_FILE"
}

log_error() {
    log "ERROR: $1" >&2
}

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Update failed with exit code ${exit_code}"
    fi
    # Always try to logout from GHCR
    docker logout ghcr.io 2>/dev/null || true
    exit $exit_code
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

preflight_checks() {
    # Check for compose file
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "docker-compose.prod.yml not found at ${COMPOSE_FILE}"
        exit 1
    fi

    # Check for Docker
    if ! command -v docker &>/dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    # Check Docker is running
    if ! docker info &>/dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
}

# =============================================================================
# Main Update Logic
# =============================================================================

main() {
    # Set up cleanup trap
    trap cleanup EXIT

    # Create logs directory first so we can log
    mkdir -p "$LOG_DIR"

    log "=========================================="
    log "Starting ParchMark update"
    log "=========================================="

    # Run pre-flight checks
    preflight_checks

    cd "$PROJECT_DIR"

    # Authenticate with GHCR if credentials are provided
    # For public images, authentication is optional
    if [[ -f "$ENV_FILE" ]]; then
        # shellcheck source=/dev/null
        source "$ENV_FILE"
        if [[ -n "${GHCR_TOKEN:-}" ]]; then
            GHCR_USER="${GHCR_USER:-tejgandham}"
            log "Authenticating with GHCR..."
            echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
        else
            log "No GHCR_TOKEN in .env.deploy, pulling public images without auth"
        fi
    else
        log "No .env.deploy file, pulling public images without auth"
    fi

    # Pull latest images
    log "Pulling latest images..."
    docker compose -f "$COMPOSE_FILE" pull postgres backend frontend

    # Get current image digests before update (for logging)
    log "Recreating containers with new images..."
    docker compose -f "$COMPOSE_FILE" up -d postgres backend frontend

    # Wait for backend to be healthy
    # Note: Migrations run automatically on container startup via entrypoint
    log "Waiting for backend to be healthy (migrations run on startup)..."
    local max_attempts=30
    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if docker compose -f "$COMPOSE_FILE" exec -T backend curl -sf http://localhost:8000/api/health &>/dev/null; then
            log "Backend is healthy"
            break
        fi
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "Backend failed to become healthy after ${max_attempts} attempts"
            log_error "Check container logs: docker logs parchmark-backend"
            exit 1
        fi
        sleep 2
        ((attempt++))
    done

    # Verify frontend is healthy
    log "Verifying frontend health..."
    local frontend_attempts=1
    local frontend_max_attempts=15
    while [[ $frontend_attempts -le $frontend_max_attempts ]]; do
        if docker compose -f "$COMPOSE_FILE" exec -T frontend wget --no-verbose --tries=1 --spider http://127.0.0.1:80/ 2>/dev/null; then
            log "Frontend is healthy"
            break
        fi
        if [[ $frontend_attempts -eq $frontend_max_attempts ]]; then
            log_error "Frontend failed to become healthy after ${frontend_max_attempts} attempts"
            exit 1
        fi
        sleep 2
        ((frontend_attempts++))
    done

    # Cleanup old images (older than 7 days)
    log "Pruning old images..."
    docker image prune -f --filter "until=168h" || true

    # Logout from GHCR (if we logged in)
    docker logout ghcr.io 2>/dev/null || true

    log "=========================================="
    log "Update complete!"
    log "=========================================="

    # Show running containers
    log "Current container status:"
    docker compose -f "$COMPOSE_FILE" ps
}

# Run main function
main "$@"
