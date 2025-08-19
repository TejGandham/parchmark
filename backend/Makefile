.PHONY: help install dev-install test test-fast test-cov lint format typecheck pre-commit clean run

help:  ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install production dependencies
	uv sync

dev-install:  ## Install all dependencies including dev
	uv sync --dev
	uv run pre-commit install

test:  ## Run tests with coverage (parallel)
	uv run pytest -v

test-fast:  ## Run tests without coverage (faster)
	uv run pytest -v --no-cov

test-cov:  ## Run tests and generate HTML coverage report
	uv run pytest -v --cov-report=html
	@echo "Coverage report generated at coverage_html/index.html"

lint:  ## Run ruff linting
	uv run ruff check app tests

format:  ## Format code with ruff
	uv run ruff format app tests

format-check:  ## Check code formatting without changes
	uv run ruff format --check app tests

typecheck:  ## Run mypy type checking
	uv run mypy app --ignore-missing-imports

pre-commit:  ## Run all pre-commit hooks
	uv run pre-commit run --all-files

clean:  ## Clean up cache and build files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf coverage_html .coverage coverage.xml
	rm -rf build dist *.egg-info

run:  ## Run the development server
	uv run python run.py

migrate:  ## Initialize database
	uv run python -c "from app.database.init_db import init_db; init_db()"
