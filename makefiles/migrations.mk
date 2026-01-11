# Database Migration targets for ParchMark
# =============================================================================
#
# Migrations run automatically on container startup when APPLY_MIGRATIONS=true.
# These targets are for manual migration management and development tasks.
#
# Prerequisites:
#   - Backend container must be running (docker compose up -d backend)
#   - For production: docker compose -f docker-compose.prod.yml
#
# =============================================================================

# ============================================================================
# MIGRATION COMMANDS
# ============================================================================

.PHONY: migrate
migrate: ## Run database migrations (via backend container)
	$(call check_docker)
	$(call info_msg,Running database migrations...)
	@docker compose exec backend alembic upgrade head
	$(call success_msg,Migrations complete)

.PHONY: migrate-status
migrate-status: ## Show current migration status
	$(call check_docker)
	$(call info_msg,Checking migration status...)
	@docker compose exec backend alembic current

.PHONY: migrate-history
migrate-history: ## Show migration history
	$(call check_docker)
	$(call info_msg,Fetching migration history...)
	@docker compose exec backend alembic history

.PHONY: migrate-heads
migrate-heads: ## Show current head revisions
	$(call check_docker)
	@docker compose exec backend alembic heads

# ============================================================================
# MIGRATION MANAGEMENT
# ============================================================================

.PHONY: migrate-downgrade
migrate-downgrade: ## Downgrade one migration
	$(call check_docker)
	$(call warning_msg,This will downgrade the database by one migration!)
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || (echo "Cancelled" && exit 1)
	@docker compose exec backend alembic downgrade -1
	$(call success_msg,Downgrade complete)

.PHONY: migrate-revision
migrate-revision: ## Create new migration (usage: make migrate-revision MSG="description")
ifndef MSG
	$(call error_msg,MSG parameter required. Usage: make migrate-revision MSG="add user table")
	@exit 1
else
	$(call check_docker)
	$(call info_msg,Creating new migration: $(MSG))
	@docker compose exec backend alembic revision --autogenerate -m "$(MSG)"
	$(call success_msg,Migration created)
endif

# ============================================================================
# PRODUCTION MIGRATION COMMANDS
# ============================================================================

.PHONY: migrate-prod
migrate-prod: ## Run migrations on production (via backend container)
	$(call check_docker)
	$(call info_msg,Running production migrations...)
	@docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
	$(call success_msg,Production migrations complete)

.PHONY: migrate-prod-status
migrate-prod-status: ## Show production migration status
	$(call check_docker)
	$(call info_msg,Checking production migration status...)
	@docker compose -f docker-compose.prod.yml exec backend alembic current

.PHONY: migrate-prod-history
migrate-prod-history: ## Show production migration history
	$(call check_docker)
	@docker compose -f docker-compose.prod.yml exec backend alembic history

# ============================================================================
# HELP
# ============================================================================

.PHONY: migrate-help
migrate-help: ## Show migration usage guide
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  ParchMark Database Migration Guide$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)AUTOMATIC MIGRATIONS:$(NC)"
	@echo "  Migrations run automatically on container startup when"
	@echo "  APPLY_MIGRATIONS=true (set in docker-compose files)."
	@echo ""
	@echo "$(GREEN)DEVELOPMENT COMMANDS:$(NC)"
	@echo "  make migrate                # Run pending migrations"
	@echo "  make migrate-status         # Show current version"
	@echo "  make migrate-history        # Show all migrations"
	@echo "  make migrate-heads          # Show head revisions"
	@echo "  make migrate-downgrade      # Rollback one migration"
	@echo "  make migrate-revision MSG=\"desc\"  # Create new migration"
	@echo ""
	@echo "$(GREEN)PRODUCTION COMMANDS:$(NC)"
	@echo "  make migrate-prod           # Run production migrations"
	@echo "  make migrate-prod-status    # Show production version"
	@echo "  make migrate-prod-history   # Show production history"
	@echo ""
	@echo "$(GREEN)PREREQUISITES:$(NC)"
	@echo "  Development: docker compose up -d backend"
	@echo "  Production:  Backend container running via docker-compose.prod.yml"
	@echo ""
	@echo "$(YELLOW)NOTE:$(NC) Migrations run on container startup. Manual commands are"
	@echo "      only needed for inspection or emergency operations."
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
