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
	@echo "$(BLUE)ParchMark Test Targets (mirrors GitHub Actions CI)$(NC)"
	@echo ""
	@echo "$(GREEN)UI Tests:$(NC)"
	@echo "  make test-ui-install    - Install UI dependencies (npm ci)"
	@echo "  make test-ui-lint       - Run ESLint on frontend code"
	@echo "  make test-ui-test       - Run Jest tests with coverage"
	@echo "  make test-ui-all        - Run all UI tests (lint + tests)"
	@echo ""
	@echo "$(GREEN)Backend Tests:$(NC)"
	@echo "  make test-backend-install  - Install backend dependencies (uv sync)"
	@echo "  make test-backend-lint     - Run ruff linting check (no auto-fix)"
	@echo "  make test-backend-format   - Run ruff formatting check (no auto-format)"
	@echo "  make test-backend-types    - Run mypy type checking"
	@echo "  make test-backend-pytest   - Run pytest with coverage"
	@echo "  make test-backend-all      - Run all backend tests (lint + format + types + pytest)"
	@echo ""
	@echo "$(GREEN)Combined Targets:$(NC)"
	@echo "  make test-all           - Run ALL tests (UI + Backend)"
	@echo "  make install-all        - Install all dependencies (UI + Backend)"
	@echo "  make clean              - Clean test artifacts and cache files"
	@echo ""
	@echo "$(YELLOW)Quick Commands:$(NC)"
	@echo "  make test               - Alias for 'make test-all'"
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
test-ui-test: ## Run Jest tests with coverage
	@echo "$(BLUE)Running UI tests...$(NC)"
	cd ui && npm test
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
test-backend-pytest: ## Run pytest with coverage
	@echo "$(BLUE)Running backend tests with coverage...$(NC)"
	cd backend && uv run pytest -v --cov=app --cov-report=xml --cov-report=term
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

# Default target
.DEFAULT_GOAL := help
