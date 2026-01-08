# Backend (Python) targets for ParchMark

.PHONY: test-backend-install
test-backend-install: ## Install backend dependencies
	$(call info_msg,Installing backend dependencies with uv...)
	cd backend && uv sync --dev
	$(call success_msg,Backend dependencies installed)

.PHONY: test-backend-lint
test-backend-lint: ## Run ruff linting check (no auto-fix)
	$(call info_msg,Running backend linting check...)
	cd backend && uv run ruff check app tests --no-fix
	$(call success_msg,Backend linting passed)

.PHONY: test-backend-format
test-backend-format: ## Run ruff formatting check (no auto-format)
	$(call info_msg,Running backend formatting check...)
	cd backend && uv run ruff format --check app tests
	$(call success_msg,Backend formatting passed)

.PHONY: test-backend-types
test-backend-types: ## Run mypy type checking
	$(call info_msg,Running backend type checking...)
	cd backend && uv run mypy app
	$(call success_msg,Backend type checking passed)

.PHONY: test-backend-pytest
test-backend-pytest: ## Run pytest with coverage (parallel with auto workers)
	$(call info_msg,Running backend tests with coverage (parallel execution)...)
	cd backend && uv run pytest -v -n auto --dist worksteal --cov=app --cov-report=xml --cov-report=term
	$(call success_msg,Backend tests passed)

.PHONY: test-backend-pytest-limited
test-backend-pytest-limited: ## Run pytest with 4 workers (resource-constrained)
	$(call info_msg,Running backend tests with coverage (4 workers)...)
	cd backend && uv run pytest -v -n 4 --dist worksteal --cov=app --cov-report=xml --cov-report=term
	$(call success_msg,Backend tests passed)

.PHONY: test-backend-all
test-backend-all: test-backend-lint test-backend-format test-backend-types test-backend-pytest ## Run all backend tests
	$(call success_msg,All backend tests passed)

.PHONY: test-backend-oidc
test-backend-oidc: ## Run OIDC-specific tests
	$(call info_msg,Running OIDC validator and hybrid auth tests...)
	cd backend && uv run pytest tests/unit/auth/test_oidc_validator.py tests/unit/auth/test_oidc_error_handling.py tests/integration/auth/test_oidc_hybrid_auth.py -v --cov=app.auth.oidc_validator --cov-report=term
	$(call success_msg,OIDC tests passed)

.PHONY: test-backend-auth
test-backend-auth: ## Run all authentication tests (local + OIDC)
	$(call info_msg,Running all authentication tests...)
	cd backend && uv run pytest tests/unit/auth/ tests/integration/auth/ -v --cov=app.auth --cov-report=term
	$(call success_msg,Authentication tests passed)

.PHONY: dev-backend
dev-backend: ## Start backend development server
	$(call info_msg,Starting backend development server...)
	cd backend && uv run uvicorn app.main:app --reload
