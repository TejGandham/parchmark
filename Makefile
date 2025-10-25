# Makefile for ParchMark - Mirrors CI/CD pipeline tests
# Run 'make help' to see all available targets

# Color output for better readability
BLUE := \033[1;34m
GREEN := \033[1;32m
YELLOW := \033[1;33m
RED := \033[1;31m
NC := \033[0m # No Color

# Python version for backend
PYTHON_VERSION := 3.13

.PHONY: help
help: ## Display this help message
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║         ParchMark - All Available Make Commands               ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)📋 Quick Start:$(NC)"
	@echo "  make test               - Run ALL tests (UI + Backend, mirrors CI)"
	@echo "  make install-all        - Install all dependencies (UI + Backend)"
	@echo "  make dev-ui             - Start UI development server"
	@echo "  make dev-backend        - Start backend development server"
	@echo "  make docker-dev         - Start PostgreSQL for local development"
	@echo ""
	@echo "$(GREEN)🧪 UI Tests (Frontend):$(NC)"
	@echo "  make test-ui-install    - Install UI dependencies (npm ci)"
	@echo "  make test-ui-lint       - Run ESLint on frontend code"
	@echo "  make test-ui-test       - Run Vitest tests with coverage"
	@echo "  make test-ui-all        - Run all UI tests (lint + tests)"
	@echo ""
	@echo "$(GREEN)🐍 Backend Tests (Python):$(NC)"
	@echo "  make test-backend-install  - Install backend dependencies (uv sync)"
	@echo "  make test-backend-lint     - Run ruff linting check (no auto-fix)"
	@echo "  make test-backend-format   - Run ruff formatting check (no auto-format)"
	@echo "  make test-backend-types    - Run mypy type checking"
	@echo "  make test-backend-pytest   - Run pytest with coverage (parallel with auto workers)"
	@echo "  make test-backend-pytest-limited - Run pytest with 4 workers (resource-constrained)"
	@echo "  make test-backend-all      - Run all backend tests (lint + format + types + pytest)"
	@echo ""
	@echo "$(GREEN)🔧 Combined Test Targets:$(NC)"
	@echo "  make test-all           - Run ALL tests (UI + Backend)"
	@echo "  make test               - Alias for 'test-all'"
	@echo ""
	@echo "$(GREEN)🚀 Development Servers:$(NC)"
	@echo "  make dev-ui             - Start UI development server (Vite at :5173)"
	@echo "  make dev-backend        - Start backend development server (FastAPI at :8000)"
	@echo "  make docker-dev         - Start PostgreSQL container for local development"
	@echo "  make docker-dev-down    - Stop PostgreSQL development container"
	@echo ""
	@echo "$(GREEN)🐳 Docker Commands:$(NC)"
	@echo "  make docker-build       - Build Docker images (full stack)"
	@echo "  make docker-up          - Start all services in Docker"
	@echo "  make docker-down        - Stop all Docker services"
	@echo "  make docker-build-prod  - Build production Docker images"
	@echo "  make docker-up-prod     - Start production services"
	@echo "  make docker-down-prod   - Stop production services"
	@echo ""
	@echo "$(GREEN)📦 Installation & Cleanup:$(NC)"
	@echo "  make install-all        - Install all dependencies (UI + Backend)"
	@echo "  make clean              - Clean test artifacts and cache files"
	@echo ""
	@echo "$(GREEN)👤 User Management - Local Development:$(NC)"
	@echo "  $(YELLOW)Usage: make user-create USERNAME=myuser PASSWORD=mypass$(NC)"
	@echo ""
	@echo "  make user-create USERNAME=x PASSWORD=y           - Create new user"
	@echo "  make user-update-password USERNAME=x PASSWORD=y  - Update user password"
	@echo "  make user-delete USERNAME=x                      - Delete user"
	@echo "  make user-list                                   - List all users"
	@echo ""
	@echo "$(GREEN)👤 User Management - Docker Development:$(NC)"
	@echo "  $(YELLOW)Usage: make user-create-docker USERNAME=myuser PASSWORD=mypass$(NC)"
	@echo ""
	@echo "  make user-create-docker USERNAME=x PASSWORD=y           - Create user"
	@echo "  make user-update-password-docker USERNAME=x PASSWORD=y  - Update password"
	@echo "  make user-delete-docker USERNAME=x                      - Delete user"
	@echo "  make user-list-docker                                   - List all users"
	@echo ""
	@echo "$(GREEN)👤 User Management - Production:$(NC)"
	@echo "  $(YELLOW)Usage: make user-create-prod USERNAME=myuser PASSWORD=mypass$(NC)"
	@echo ""
	@echo "  make user-create-prod USERNAME=x PASSWORD=y           - Create user"
	@echo "  make user-update-password-prod USERNAME=x PASSWORD=y  - Update password"
	@echo "  make user-delete-prod USERNAME=x                      - Delete user"
	@echo "  make user-list-prod                                   - List all users"
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(YELLOW)Total Commands Available: 38$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo ""

# ============================================================================
# UI TESTS (Frontend)
# ============================================================================

.PHONY: test-ui-install
test-ui-install: ## Install UI dependencies
	@echo "$(BLUE)Installing UI dependencies...$(NC)"
	cd ui && npm ci
	@echo "$(GREEN)✓ UI dependencies installed$(NC)"

.PHONY: test-ui-lint
test-ui-lint: ## Run ESLint on frontend code
	@echo "$(BLUE)Running UI linting...$(NC)"
	cd ui && npm run lint
	@echo "$(GREEN)✓ UI linting passed$(NC)"

.PHONY: test-ui-test
test-ui-test: ## Run Vitest tests with coverage
	@echo "$(BLUE)Running UI tests...$(NC)"
	cd ui && npm run test:coverage
	@echo "$(GREEN)✓ UI tests passed$(NC)"

.PHONY: test-ui-all
test-ui-all: test-ui-lint test-ui-test ## Run all UI tests
	@echo "$(GREEN)✓ All UI tests passed$(NC)"

# ============================================================================
# BACKEND TESTS (Python)
# ============================================================================

.PHONY: test-backend-install
test-backend-install: ## Install backend dependencies
	@echo "$(BLUE)Installing backend dependencies with uv...$(NC)"
	cd backend && uv sync --dev
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

.PHONY: test-backend-lint
test-backend-lint: ## Run ruff linting check (no auto-fix)
	@echo "$(BLUE)Running backend linting check...$(NC)"
	cd backend && uv run ruff check app tests --no-fix
	@echo "$(GREEN)✓ Backend linting passed$(NC)"

.PHONY: test-backend-format
test-backend-format: ## Run ruff formatting check (no auto-format)
	@echo "$(BLUE)Running backend formatting check...$(NC)"
	cd backend && uv run ruff format --check app tests
	@echo "$(GREEN)✓ Backend formatting passed$(NC)"

.PHONY: test-backend-types
test-backend-types: ## Run mypy type checking
	@echo "$(BLUE)Running backend type checking...$(NC)"
	cd backend && uv run mypy app
	@echo "$(GREEN)✓ Backend type checking passed$(NC)"

.PHONY: test-backend-pytest
test-backend-pytest: ## Run pytest with coverage (parallel execution with auto workers)
	@echo "$(BLUE)Running backend tests with coverage (parallel execution)...$(NC)"
	cd backend && uv run pytest -v -n auto --dist worksteal --cov=app --cov-report=xml --cov-report=term
	@echo "$(GREEN)✓ Backend tests passed$(NC)"

.PHONY: test-backend-pytest-limited
test-backend-pytest-limited: ## Run pytest with limited workers (n=4, for resource-constrained environments)
	@echo "$(BLUE)Running backend tests with coverage (4 workers)...$(NC)"
	cd backend && uv run pytest -v -n 4 --dist worksteal --cov=app --cov-report=xml --cov-report=term
	@echo "$(GREEN)✓ Backend tests passed$(NC)"

.PHONY: test-backend-all
test-backend-all: test-backend-lint test-backend-format test-backend-types test-backend-pytest ## Run all backend tests
	@echo "$(GREEN)✓ All backend tests passed$(NC)"

# ============================================================================
# COMBINED TARGETS
# ============================================================================

.PHONY: install-all
install-all: test-ui-install test-backend-install ## Install all dependencies
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

.PHONY: test-all
test-all: test-ui-all test-backend-all ## Run ALL tests (UI + Backend)
	@echo ""
	@echo "$(GREEN)════════════════════════════════════════$(NC)"
	@echo "$(GREEN)✓ ALL TESTS PASSED$(NC)"
	@echo "$(GREEN)════════════════════════════════════════$(NC)"

.PHONY: test
test: test-all ## Alias for test-all

# ============================================================================
# CLEANUP
# ============================================================================

.PHONY: clean
clean: ## Clean test artifacts and cache files
	@echo "$(BLUE)Cleaning test artifacts...$(NC)"
	# UI cleanup
	rm -rf ui/node_modules/.cache
	rm -rf ui/coverage
	rm -rf ui/coverage_html
	# Backend cleanup
	rm -rf backend/.pytest_cache
	rm -rf backend/.ruff_cache
	rm -rf backend/.mypy_cache
	rm -rf backend/htmlcov
	rm -rf backend/coverage.xml
	rm -rf backend/.coverage
	# Root cleanup
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# ============================================================================
# DEVELOPER CONVENIENCE TARGETS
# ============================================================================

.PHONY: dev-ui
dev-ui: ## Start UI development server
	@echo "$(BLUE)Starting UI development server...$(NC)"
	cd ui && npm run dev

.PHONY: dev-backend
dev-backend: ## Start backend development server
	@echo "$(BLUE)Starting backend development server...$(NC)"
	cd backend && uv run uvicorn app.main:app --reload

.PHONY: docker-dev
docker-dev: ## Start PostgreSQL for local development
	@echo "$(BLUE)Starting PostgreSQL container for development...$(NC)"
	docker compose -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✓ PostgreSQL running$(NC)"

.PHONY: docker-dev-down
docker-dev-down: ## Stop PostgreSQL development container
	@echo "$(BLUE)Stopping PostgreSQL container...$(NC)"
	docker compose -f docker-compose.dev.yml down
	@echo "$(GREEN)✓ PostgreSQL stopped$(NC)"

.PHONY: docker-build
docker-build: ## Build Docker images (full stack)
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker compose build
	@echo "$(GREEN)✓ Docker images built$(NC)"

.PHONY: docker-build-prod
docker-build-prod: ## Build Docker images for production
	@echo "$(BLUE)Building production Docker images...$(NC)"
	docker compose -f docker-compose.prod.yml build
	@echo "$(GREEN)✓ Production Docker images built$(NC)"

.PHONY: docker-up
docker-up: ## Start all services in Docker (full stack)
	@echo "$(BLUE)Starting all Docker services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✓ All services running$(NC)"

.PHONY: docker-down
docker-down: ## Stop all Docker services (full stack)
	@echo "$(BLUE)Stopping all Docker services...$(NC)"
	docker compose down
	@echo "$(GREEN)✓ All services stopped$(NC)"

.PHONY: docker-up-prod
docker-up-prod: ## Start production Docker services
	@echo "$(BLUE)Starting production Docker services...$(NC)"
	docker compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✓ Production services running$(NC)"

.PHONY: docker-down-prod
docker-down-prod: ## Stop production Docker services
	@echo "$(BLUE)Stopping production Docker services...$(NC)"
	docker compose -f docker-compose.prod.yml down
	@echo "$(GREEN)✓ Production services stopped$(NC)"

# ============================================================================
# USER MANAGEMENT
# ============================================================================

# Local development (backend on host, PostgreSQL in Docker)
.PHONY: user-create
user-create: ## Create user (local dev) - Usage: make user-create USERNAME=admin PASSWORD=pass123
	@if [ -z "$(USERNAME)" ] || [ -z "$(PASSWORD)" ]; then \
		echo "$(RED)Error: USERNAME and PASSWORD are required$(NC)"; \
		echo "Usage: make user-create USERNAME=admin PASSWORD=pass123"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating user '$(USERNAME)' in local development...$(NC)"
	cd backend && uv run python scripts/manage_users.py create $(USERNAME) $(PASSWORD)

.PHONY: user-update-password
user-update-password: ## Update user password (local dev) - Usage: make user-update-password USERNAME=admin PASSWORD=newpass
	@if [ -z "$(USERNAME)" ] || [ -z "$(PASSWORD)" ]; then \
		echo "$(RED)Error: USERNAME and PASSWORD are required$(NC)"; \
		echo "Usage: make user-update-password USERNAME=admin PASSWORD=newpass"; \
		exit 1; \
	fi
	@echo "$(BLUE)Updating password for user '$(USERNAME)' in local development...$(NC)"
	cd backend && uv run python scripts/manage_users.py update-password $(USERNAME) $(PASSWORD)

.PHONY: user-delete
user-delete: ## Delete user (local dev) - Usage: make user-delete USERNAME=admin
	@if [ -z "$(USERNAME)" ]; then \
		echo "$(RED)Error: USERNAME is required$(NC)"; \
		echo "Usage: make user-delete USERNAME=admin"; \
		exit 1; \
	fi
	@echo "$(BLUE)Deleting user '$(USERNAME)' from local development...$(NC)"
	cd backend && uv run python scripts/manage_users.py delete $(USERNAME)

.PHONY: user-list
user-list: ## List all users (local dev)
	@echo "$(BLUE)Listing users in local development...$(NC)"
	cd backend && uv run python scripts/manage_users.py list

# Docker development (all services in containers)
.PHONY: user-create-docker
user-create-docker: ## Create user (docker dev) - Usage: make user-create-docker USERNAME=admin PASSWORD=pass123
	@if [ -z "$(USERNAME)" ] || [ -z "$(PASSWORD)" ]; then \
		echo "$(RED)Error: USERNAME and PASSWORD are required$(NC)"; \
		echo "Usage: make user-create-docker USERNAME=admin PASSWORD=pass123"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating user '$(USERNAME)' in Docker development...$(NC)"
	docker compose exec backend python scripts/manage_users.py create $(USERNAME) $(PASSWORD)

.PHONY: user-update-password-docker
user-update-password-docker: ## Update user password (docker dev) - Usage: make user-update-password-docker USERNAME=admin PASSWORD=newpass
	@if [ -z "$(USERNAME)" ] || [ -z "$(PASSWORD)" ]; then \
		echo "$(RED)Error: USERNAME and PASSWORD are required$(NC)"; \
		echo "Usage: make user-update-password-docker USERNAME=admin PASSWORD=newpass"; \
		exit 1; \
	fi
	@echo "$(BLUE)Updating password for user '$(USERNAME)' in Docker development...$(NC)"
	docker compose exec backend python scripts/manage_users.py update-password $(USERNAME) $(PASSWORD)

.PHONY: user-delete-docker
user-delete-docker: ## Delete user (docker dev) - Usage: make user-delete-docker USERNAME=admin
	@if [ -z "$(USERNAME)" ]; then \
		echo "$(RED)Error: USERNAME is required$(NC)"; \
		echo "Usage: make user-delete-docker USERNAME=admin"; \
		exit 1; \
	fi
	@echo "$(BLUE)Deleting user '$(USERNAME)' from Docker development...$(NC)"
	docker compose exec backend python scripts/manage_users.py delete $(USERNAME)

.PHONY: user-list-docker
user-list-docker: ## List all users (docker dev)
	@echo "$(BLUE)Listing users in Docker development...$(NC)"
	docker compose exec backend python scripts/manage_users.py list

# Production (Docker with production config)
.PHONY: user-create-prod
user-create-prod: ## Create user (production) - Usage: make user-create-prod USERNAME=admin PASSWORD=pass123
	@if [ -z "$(USERNAME)" ] || [ -z "$(PASSWORD)" ]; then \
		echo "$(RED)Error: USERNAME and PASSWORD are required$(NC)"; \
		echo "Usage: make user-create-prod USERNAME=admin PASSWORD=pass123"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating user '$(USERNAME)' in production...$(NC)"
	docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py create $(USERNAME) $(PASSWORD)

.PHONY: user-update-password-prod
user-update-password-prod: ## Update user password (production) - Usage: make user-update-password-prod USERNAME=admin PASSWORD=newpass
	@if [ -z "$(USERNAME)" ] || [ -z "$(PASSWORD)" ]; then \
		echo "$(RED)Error: USERNAME and PASSWORD are required$(NC)"; \
		echo "Usage: make user-update-password-prod USERNAME=admin PASSWORD=newpass"; \
		exit 1; \
	fi
	@echo "$(BLUE)Updating password for user '$(USERNAME)' in production...$(NC)"
	docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py update-password $(USERNAME) $(PASSWORD)

.PHONY: user-delete-prod
user-delete-prod: ## Delete user (production) - Usage: make user-delete-prod USERNAME=admin
	@if [ -z "$(USERNAME)" ]; then \
		echo "$(RED)Error: USERNAME is required$(NC)"; \
		echo "Usage: make user-delete-prod USERNAME=admin"; \
		exit 1; \
	fi
	@echo "$(BLUE)Deleting user '$(USERNAME)' from production...$(NC)"
	docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py delete $(USERNAME)

.PHONY: user-list-prod
user-list-prod: ## List all users (production)
	@echo "$(BLUE)Listing users in production...$(NC)"
	docker compose -f docker-compose.prod.yml exec backend python scripts/manage_users.py list

# Default target
.DEFAULT_GOAL := help
