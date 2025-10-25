# Auto-generated help system for ParchMark

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
	@$(MAKE) --silent help-ui
	@$(MAKE) --silent help-backend
	@$(MAKE) --silent help-combined
	@$(MAKE) --silent help-dev
	@$(MAKE) --silent help-docker
	@$(MAKE) --silent help-install
	@$(MAKE) --silent help-users
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo -n "$(YELLOW)Total Commands Available: $(NC)"
	@$(MAKE) --silent count-commands
	@echo "$(BLUE)═══════════════════════════════════════════════════════════════$(NC)"
	@echo ""

.PHONY: count-commands
count-commands:
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) 2>/dev/null | wc -l | xargs echo

# Helper targets for each section (called by main help)
.PHONY: help-ui
help-ui:
	@echo "$(GREEN)🧪 UI Tests (Frontend):$(NC)"
	@grep -hE '^test-ui-.*:.*?## ' makefiles/ui.mk Makefile 2>/dev/null | sed -E 's/^([a-zA-Z_-]+):.*## (.*)$$/  make \1 ##PADDING## - \2/' | awk '{printf "  make %-23s - %s\n", $$2, substr($$0, index($$0, $$5))}'
	@echo ""

.PHONY: help-backend
help-backend:
	@echo "$(GREEN)🐍 Backend Tests (Python):$(NC)"
	@grep -hE '^test-backend-.*:.*?## ' makefiles/backend.mk Makefile 2>/dev/null | sed -E 's/^([a-zA-Z_-]+):.*## (.*)$$/  make \1 ##PADDING## - \2/' | awk '{printf "  make %-23s - %s\n", $$2, substr($$0, index($$0, $$5))}'
	@echo ""

.PHONY: help-combined
help-combined:
	@echo "$(GREEN)🔧 Combined Test Targets:$(NC)"
	@grep -hE '^(test-all|test|install-all|clean):.*?## ' Makefile 2>/dev/null | grep -E '^(test-all|test):' | sed -E 's/^([a-zA-Z_-]+):.*## (.*)$$/  make \1 ##PADDING## - \2/' | awk '{printf "  make %-23s - %s\n", $$2, substr($$0, index($$0, $$5))}'
	@echo ""

.PHONY: help-dev
help-dev:
	@echo "$(GREEN)🚀 Development Servers:$(NC)"
	@grep -hE '^(dev-ui|dev-backend|docker-dev|docker-dev-down):.*?## ' makefiles/ui.mk makefiles/backend.mk makefiles/docker.mk Makefile 2>/dev/null | sed -E 's/^([a-zA-Z_-]+):.*## (.*)$$/  make \1 ##PADDING## - \2/' | awk '{printf "  make %-23s - %s\n", $$2, substr($$0, index($$0, $$5))}'
	@echo ""

.PHONY: help-docker
help-docker:
	@echo "$(GREEN)🐳 Docker Commands:$(NC)"
	@grep -hE '^docker-.*:.*?## ' makefiles/docker.mk Makefile 2>/dev/null | grep -v 'docker-dev:' | grep -v 'docker-dev-down:' | sed -E 's/^([a-zA-Z_-]+):.*## (.*)$$/  make \1 ##PADDING## - \2/' | awk '{printf "  make %-23s - %s\n", $$2, substr($$0, index($$0, $$5))}'
	@echo ""

.PHONY: help-install
help-install:
	@echo "$(GREEN)📦 Installation & Cleanup:$(NC)"
	@grep -hE '^(install-all|clean):.*?## ' Makefile 2>/dev/null | sed -E 's/^([a-zA-Z_-]+):.*## (.*)$$/  make \1 ##PADDING## - \2/' | awk '{printf "  make %-23s - %s\n", $$2, substr($$0, index($$0, $$5))}'
	@echo ""

.PHONY: help-users
help-users:
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
