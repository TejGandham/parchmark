#!/bin/bash
# ParchMark Database Admin Entrypoint
# Interactive shell for database migrations and management tasks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Parse DATABASE_URL to extract components for display and psql
parse_db_url() {
    # DATABASE_URL format: postgresql://user:password@host:port/dbname
    local url="${DATABASE_URL:-postgresql://parchmark_user:parchmark_password@localhost:5432/parchmark_db}"

    # Extract components using bash parameter expansion
    local without_proto="${url#*://}"
    DB_USER="${without_proto%%:*}"
    local rest="${without_proto#*:}"
    DB_PASS="${rest%%@*}"
    rest="${rest#*@}"
    DB_HOST="${rest%%:*}"
    rest="${rest#*:}"
    DB_PORT="${rest%%/*}"
    DB_NAME="${rest#*/}"
}

# Print header
print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}       ParchMark Database Admin${NC}"
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════════${NC}"
    echo ""
}

# Print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print error message
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Print info message
info() {
    echo -e "${CYAN}→ $1${NC}"
}

# Print warning message
warn() {
    echo -e "${YELLOW}! $1${NC}"
}

# Wait for database connectivity
wait_for_db() {
    parse_db_url

    info "Checking database connectivity..."
    echo -e "  Host: ${BOLD}${DB_HOST}:${DB_PORT}${NC}"
    echo -e "  Database: ${BOLD}${DB_NAME}${NC}"
    echo -e "  User: ${BOLD}${DB_USER}${NC}"
    echo ""

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if uv run python -c "
import sys
from sqlalchemy import create_engine, text
try:
    engine = create_engine('${DATABASE_URL}')
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
            success "Connected to database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
            return 0
        fi

        if [ $attempt -eq 1 ]; then
            warn "Waiting for database to be ready..."
        fi

        echo -ne "\r  Attempt $attempt/$max_attempts..."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo ""
    error "Could not connect to database after ${max_attempts} seconds"
    echo ""
    echo "Please ensure PostgreSQL is running:"
    echo "  make docker-dev"
    echo "  # or"
    echo "  docker compose -f docker-compose.dev.yml up -d"
    echo ""
    exit 1
}

# Install dependencies using uv
install_deps() {
    if [ ! -d ".venv" ] || [ ! -f ".venv/bin/python" ]; then
        info "Installing dependencies..."
        uv sync --frozen --quiet
        success "Dependencies installed"
    else
        # Check if deps are up to date
        if ! uv sync --frozen --quiet 2>/dev/null; then
            info "Updating dependencies..."
            uv sync --frozen --quiet
        fi
        success "Dependencies ready"
    fi
}

# Run migrations
run_migrations() {
    echo ""
    echo -e "${YELLOW}This will run: ${BOLD}alembic upgrade head${NC}"
    echo ""
    local confirm=""
    read -p "Continue? [y/N]: " confirm || true

    if [[ "${confirm:-}" =~ ^[Yy]$ ]]; then
        echo ""
        info "Running migrations..."
        echo ""
        if uv run alembic upgrade head; then
            echo ""
            success "Migrations complete"
        else
            echo ""
            error "Migration failed"
        fi
    else
        warn "Cancelled"
    fi
}

# Show migration status
show_status() {
    echo ""
    info "Current migration status:"
    echo ""
    uv run alembic current || error "Failed to get migration status"
    echo ""
}

# Show migration history
show_history() {
    echo ""
    info "Migration history:"
    echo ""
    uv run alembic history --verbose || error "Failed to get migration history"
    echo ""
}

# User management submenu
user_management() {
    local choice=""
    local username=""
    local password=""
    local confirm=""

    while true; do
        echo ""
        echo -e "${CYAN}${BOLD}User Management${NC}"
        echo ""
        echo "  1) List users"
        echo "  2) Create user"
        echo "  3) Update password"
        echo "  4) Delete user"
        echo "  5) Back to main menu"
        echo ""
        read -p "Select option: " choice || true

        case "${choice:-}" in
            1)
                echo ""
                uv run python scripts/manage_users.py list || true
                ;;
            2)
                echo ""
                read -p "Username: " username || true
                read -s -p "Password: " password || true
                echo ""
                if [[ -n "${username:-}" && -n "${password:-}" ]]; then
                    uv run python scripts/manage_users.py create "$username" "$password" || true
                else
                    warn "Username and password are required"
                fi
                ;;
            3)
                echo ""
                read -p "Username: " username || true
                read -s -p "New password: " password || true
                echo ""
                if [[ -n "${username:-}" && -n "${password:-}" ]]; then
                    uv run python scripts/manage_users.py update-password "$username" "$password" || true
                else
                    warn "Username and password are required"
                fi
                ;;
            4)
                echo ""
                read -p "Username to delete: " username || true
                read -p "Are you sure? [y/N]: " confirm || true
                if [[ "${confirm:-}" =~ ^[Yy]$ ]]; then
                    uv run python scripts/manage_users.py delete "$username" || true
                else
                    warn "Cancelled"
                fi
                ;;
            5)
                return
                ;;
            *)
                warn "Invalid option"
                ;;
        esac

        echo ""
        read -p "Press Enter to continue..." _ || true
    done
}

# Database shell (psql)
db_shell() {
    parse_db_url

    echo ""
    info "Connecting to PostgreSQL shell..."
    echo -e "  ${YELLOW}Type \\q to exit${NC}"
    echo ""

    # Check if psql is available
    if command -v psql &> /dev/null; then
        PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" || true
    else
        warn "psql not available in this container"
        echo ""
        echo "Alternative: Use Python to run SQL queries:"
        echo "  uv run python -c \"from app.database.database import engine; ...\""
        echo ""
        echo "Or connect from your host machine:"
        echo "  psql postgresql://${DB_USER}:****@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    fi
}

# Custom command
# NOTE: This intentionally allows arbitrary command execution via uv run.
# This is an admin tool requiring container access, so users already have elevated privileges.
custom_command() {
    local cmd=""
    echo ""
    info "Enter command to run (with uv run prefix):"
    echo -e "  ${YELLOW}Examples:${NC}"
    echo "    alembic downgrade -1"
    echo "    python -c \"from app.models.models import User; print(User.__table__.columns.keys())\""
    echo ""
    read -p "Command: " cmd || true

    if [[ -n "${cmd:-}" ]]; then
        echo ""
        # shellcheck disable=SC2086
        # Intentional: allows arbitrary commands for admin flexibility
        uv run $cmd || true
    fi
}

# Main menu
main_menu() {
    local choice=""

    while true; do
        echo ""
        echo -e "${BLUE}${BOLD}Main Menu${NC}"
        echo ""
        echo "  1) Run migrations (alembic upgrade head)"
        echo "  2) Show migration status (alembic current)"
        echo "  3) Show migration history"
        echo "  4) User management"
        echo "  5) Database shell (psql)"
        echo "  6) Run custom command"
        echo "  7) Exit"
        echo ""
        read -p "Select option: " choice || true

        case "${choice:-}" in
            1)
                run_migrations
                ;;
            2)
                show_status
                ;;
            3)
                show_history
                ;;
            4)
                user_management
                ;;
            5)
                db_shell
                ;;
            6)
                custom_command
                ;;
            7)
                echo ""
                success "Goodbye!"
                echo ""
                exit 0
                ;;
            *)
                warn "Invalid option"
                ;;
        esac

        echo ""
        read -p "Press Enter to continue..." _ || true
    done
}

# Handle command-line arguments for non-interactive use
if [ $# -gt 0 ]; then
    # Non-interactive mode: run the provided command
    case "$1" in
        "migrate")
            install_deps
            wait_for_db
            echo ""
            info "Running migrations..."
            uv run alembic upgrade head
            success "Migrations complete"
            ;;
        "status")
            install_deps
            wait_for_db
            uv run alembic current
            ;;
        "history")
            install_deps
            wait_for_db
            uv run alembic history --verbose
            ;;
        *)
            # Pass through to uv run
            install_deps
            wait_for_db
            exec uv run "$@"
            ;;
    esac
    exit 0
fi

# Interactive mode
print_header
install_deps
wait_for_db
main_menu
