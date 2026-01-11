# Database Admin targets for ParchMark
# These targets provide database migration and management capabilities
# using a temporary uv-based container

# Docker Compose file for db-admin
DB_ADMIN_COMPOSE := docker-compose.db-admin.yml

# ============================================================================
# DATABASE ADMIN - INTERACTIVE
# ============================================================================

.PHONY: db-admin
db-admin: ## Start interactive database admin shell
	$(call check_docker)
	$(call info_msg,Starting database admin shell...)
	@docker compose -f $(DB_ADMIN_COMPOSE) run --rm db-admin

# ============================================================================
# DATABASE ADMIN - NON-INTERACTIVE COMMANDS
# ============================================================================

.PHONY: db-admin-migrate
db-admin-migrate: ## Run database migrations (non-interactive)
	$(call check_docker)
	$(call info_msg,Running database migrations...)
	@docker compose -f $(DB_ADMIN_COMPOSE) run --rm db-admin migrate

.PHONY: db-admin-status
db-admin-status: ## Show current migration status
	$(call check_docker)
	$(call info_msg,Checking migration status...)
	@docker compose -f $(DB_ADMIN_COMPOSE) run --rm db-admin status

.PHONY: db-admin-history
db-admin-history: ## Show migration history
	$(call check_docker)
	$(call info_msg,Fetching migration history...)
	@docker compose -f $(DB_ADMIN_COMPOSE) run --rm db-admin history

# ============================================================================
# DATABASE ADMIN - ALEMBIC COMMANDS
# ============================================================================

.PHONY: db-admin-downgrade
db-admin-downgrade: ## Downgrade one migration (usage: make db-admin-downgrade)
	$(call check_docker)
	$(call warning_msg,This will downgrade the database by one migration!)
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || (echo "Cancelled" && exit 1)
	@docker compose -f $(DB_ADMIN_COMPOSE) run --rm db-admin alembic downgrade -1
	$(call success_msg,Downgrade complete)

.PHONY: db-admin-revision
db-admin-revision: ## Create new migration (usage: make db-admin-revision MSG="description")
ifndef MSG
	$(call error_msg,MSG parameter required. Usage: make db-admin-revision MSG="add user table")
	@exit 1
else
	$(call check_docker)
	$(call info_msg,Creating new migration: $(MSG))
	@docker compose -f $(DB_ADMIN_COMPOSE) run --rm db-admin alembic revision --autogenerate -m "$(MSG)"
	$(call success_msg,Migration created)
endif

# ============================================================================
# DATABASE ADMIN - USER MANAGEMENT
# ============================================================================

.PHONY: db-admin-users
db-admin-users: ## List all users via db-admin container
	$(call check_docker)
	@docker compose -f $(DB_ADMIN_COMPOSE) run --rm db-admin python scripts/manage_users.py list

# ============================================================================
# DATABASE ADMIN - UTILITY
# ============================================================================

.PHONY: db-admin-shell
db-admin-shell: ## Start a bash shell in the db-admin container
	$(call check_docker)
	$(call info_msg,Starting bash shell in db-admin container...)
	@docker compose -f $(DB_ADMIN_COMPOSE) run --rm --entrypoint /bin/bash db-admin

.PHONY: db-admin-help
db-admin-help: ## Show database admin usage guide
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  ParchMark Database Admin Guide$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)PREREQUISITES:$(NC)"
	@echo "  PostgreSQL must be running before using db-admin commands:"
	@echo "    make docker-dev              # Start PostgreSQL container"
	@echo ""
	@echo "$(GREEN)INTERACTIVE MODE:$(NC)"
	@echo "  make db-admin                  # Full interactive menu"
	@echo ""
	@echo "$(GREEN)MIGRATION COMMANDS:$(NC)"
	@echo "  make db-admin-migrate          # Run pending migrations"
	@echo "  make db-admin-status           # Show current migration version"
	@echo "  make db-admin-history          # Show all migration history"
	@echo "  make db-admin-downgrade        # Rollback one migration"
	@echo "  make db-admin-revision MSG=\"desc\"  # Create new migration"
	@echo ""
	@echo "$(GREEN)USER MANAGEMENT:$(NC)"
	@echo "  make db-admin-users            # List all users"
	@echo ""
	@echo "$(GREEN)UTILITY:$(NC)"
	@echo "  make db-admin-shell            # Bash shell in container"
	@echo ""
	@echo "$(GREEN)CUSTOM COMMANDS:$(NC)"
	@echo "  docker compose -f docker-compose.db-admin.yml run --rm db-admin <command>"
	@echo ""
	@echo "  Examples:"
	@echo "    ... run --rm db-admin alembic heads"
	@echo "    ... run --rm db-admin python -c \"from app.models.models import User; print(User)\""
	@echo ""
	@echo "$(GREEN)ENVIRONMENT:$(NC)"
	@echo "  Override DATABASE_URL for different environments:"
	@echo "    DATABASE_URL=postgresql://user:pass@host:5432/db make db-admin-migrate"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
