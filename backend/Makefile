# Backend Makefile for ParchMark
# Links to modular makefiles in ../makefiles/
#
# This Makefile can be run from the backend/ directory and includes
# all modular makefiles for full feature parity with the root Makefile.

# Include all modular makefiles (relative to backend/)
include ../makefiles/common.mk
include ../makefiles/ui.mk
include ../makefiles/backend.mk
include ../makefiles/docker.mk
include ../makefiles/users.mk
include ../makefiles/deploy.mk
include ../makefiles/help.mk

# ============================================================================
# BACKEND-SPECIFIC TARGETS (legacy compatibility)
# ============================================================================

.PHONY: install
install:  ## Install production dependencies
	uv sync

.PHONY: dev-install
dev-install:  ## Install all dependencies including dev
	uv sync --dev
	uv run pre-commit install

.PHONY: test
test:  ## Run tests with coverage (parallel)
	uv run pytest -v

.PHONY: test-fast
test-fast:  ## Run tests without coverage (faster)
	uv run pytest -v --no-cov

.PHONY: test-cov
test-cov:  ## Run tests and generate HTML coverage report
	uv run pytest -v --cov-report=html
	@echo "Coverage report generated at coverage_html/index.html"

.PHONY: lint
lint:  ## Run ruff linting
	uv run ruff check app tests

.PHONY: format
format:  ## Format code with ruff
	uv run ruff format app tests

.PHONY: format-check
format-check:  ## Check code formatting without changes
	uv run ruff format --check app tests

.PHONY: typecheck
typecheck:  ## Run mypy type checking
	uv run mypy app --ignore-missing-imports

.PHONY: pre-commit
pre-commit:  ## Run all pre-commit hooks
	uv run pre-commit run --all-files

.PHONY: clean
clean:  ## Clean up cache and build files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf coverage_html .coverage coverage.xml
	rm -rf build dist *.egg-info

.PHONY: run
run:  ## Run the development server
	uv run python -m app

.PHONY: migrate
migrate:  ## Initialize database
	uv run python -c "from app.database.init_db import init_db; init_db()"

# Default target
.DEFAULT_GOAL := help
