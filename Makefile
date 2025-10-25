# Makefile for ParchMark - Mirrors CI/CD pipeline tests
# Run 'make help' to see all available targets
#
# This is the main orchestrator that includes modular makefiles:
# - makefiles/common.mk   - Shared variables and functions
# - makefiles/help.mk     - Auto-generated help system
# - makefiles/ui.mk       - UI test and dev targets
# - makefiles/backend.mk  - Backend test and dev targets
# - makefiles/docker.mk   - Docker-related targets
# - makefiles/users.mk    - User management targets

# Include all modular makefiles
include makefiles/common.mk
include makefiles/ui.mk
include makefiles/backend.mk
include makefiles/docker.mk
include makefiles/users.mk
include makefiles/help.mk

# ============================================================================
# COMBINED TARGETS
# ============================================================================

.PHONY: install-all
install-all: test-ui-install test-backend-install ## Install all dependencies
	$(call success_msg,All dependencies installed)

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
	$(call info_msg,Cleaning test artifacts...)
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
	$(call success_msg,Cleanup complete)

# Default target
.DEFAULT_GOAL := help
