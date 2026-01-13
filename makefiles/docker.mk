# Docker targets for ParchMark

# ============================================================================
# COMBINED DEVELOPMENT TARGETS
# ============================================================================

.PHONY: dev
dev: docker-dev dev-wait-db ## Start all dev services (PostgreSQL + Backend + Frontend)
	$(call info_msg,Starting backend and frontend in parallel...)
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  ParchMark Development Environment$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(BLUE)Access points:$(NC)"
	@echo "  Frontend:  http://localhost:5173"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo ""
	@echo "$(BLUE)Test user:$(NC)"
	@echo "  Username:  qauser"
	@echo "  Password:  QaPass123!"
	@echo ""
	@echo "$(YELLOW)Press Ctrl+C to stop all services$(NC)"
	@echo ""
	@trap 'echo ""; echo "$(BLUE)Stopping services...$(NC)"; kill 0' EXIT; \
	(cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd ui && npm run dev -- --host 0.0.0.0) & \
	wait

.PHONY: dev-wait-db
dev-wait-db: ## Wait for PostgreSQL to be ready
	@echo "$(BLUE)Waiting for PostgreSQL to be ready...$(NC)"
	@for i in 1 2 3 4 5; do \
		docker compose -f docker-compose.dev.yml exec -T postgres pg_isready -U parchmark_user -d parchmark_db > /dev/null 2>&1 && break || sleep 1; \
	done
	$(call success_msg,PostgreSQL is ready)

.PHONY: dev-stop
dev-stop: docker-dev-down ## Stop all development services
	$(call success_msg,All development services stopped)

# ============================================================================
# POSTGRESQL TARGETS
# ============================================================================

.PHONY: docker-dev
docker-dev: ## Start PostgreSQL for local development
	$(call check_docker)
	$(call info_msg,Starting PostgreSQL container for development...)
	docker compose -f docker-compose.dev.yml up -d
	$(call success_msg,PostgreSQL running)

.PHONY: docker-dev-down
docker-dev-down: ## Stop PostgreSQL development container
	$(call check_docker)
	$(call info_msg,Stopping PostgreSQL container...)
	docker compose -f docker-compose.dev.yml down
	$(call success_msg,PostgreSQL stopped)

.PHONY: docker-build
docker-build: ## Build Docker images (full stack)
	$(call check_docker)
	$(call info_msg,Building Docker images...)
	docker compose build
	$(call success_msg,Docker images built)

.PHONY: docker-build-prod
docker-build-prod: ## Build production Docker images
	$(call check_docker)
	$(call info_msg,Building production Docker images...)
	docker compose -f docker-compose.prod.yml build
	$(call success_msg,Production Docker images built)

.PHONY: docker-up
docker-up: ## Start all services in Docker (full stack)
	$(call check_docker)
	$(call info_msg,Starting all Docker services...)
	docker compose up -d
	$(call success_msg,All services running)

.PHONY: docker-down
docker-down: ## Stop all Docker services (full stack)
	$(call check_docker)
	$(call info_msg,Stopping all Docker services...)
	docker compose down
	$(call success_msg,All services stopped)

.PHONY: docker-up-prod
docker-up-prod: ## Start production Docker services
	$(call check_docker)
	$(call info_msg,Starting production Docker services...)
	docker compose -f docker-compose.prod.yml up -d
	$(call success_msg,Production services running)

.PHONY: docker-down-prod
docker-down-prod: ## Stop production Docker services
	$(call check_docker)
	$(call info_msg,Stopping production Docker services...)
	docker compose -f docker-compose.prod.yml down
	$(call success_msg,Production services stopped)

# ============================================================================
# OIDC Testing Targets (Local Testing with Authelia)
# ============================================================================

.PHONY: docker-oidc-test
docker-oidc-test: ## Start OIDC testing environment (Authelia + all services)
	$(call check_docker)
	$(call info_msg,Starting OIDC testing environment with Authelia...)
	docker compose -f docker-compose.oidc-test.yml up -d
	$(call info_msg,Waiting for services to be healthy...)
	sleep 3
	@echo "$(COLOR_CYAN)Services started. Checking health...$(COLOR_RESET)"
	docker compose -f docker-compose.oidc-test.yml ps
	@echo ""
	@echo "$(COLOR_GREEN)✓ OIDC Testing Environment Ready!$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_CYAN)Access points:$(COLOR_RESET)"
	@echo "  Frontend:  http://localhost:8080"
	@echo "  Backend:   http://localhost:8000"
	@echo "  Authelia:  http://localhost:9091"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo ""
	@echo "$(COLOR_CYAN)Test users (password: password123):$(COLOR_RESET)"
	@echo "  john  (john@example.com)"
	@echo "  jane  (jane@example.com)"
	@echo "  admin (admin@example.com)"
	@echo ""
	@echo "$(COLOR_CYAN)Useful commands:$(COLOR_RESET)"
	@echo "  make docker-oidc-logs          - View service logs"
	@echo "  make docker-oidc-down          - Stop all services"
	@echo "  make docker-oidc-reset         - Reset and restart"
	@echo "  See docs/AUTHELIA_OIDC_LOCAL_TESTING.md for detailed guide"
	@echo ""

.PHONY: docker-oidc-logs
docker-oidc-logs: ## View OIDC testing environment logs
	docker compose -f docker-compose.oidc-test.yml logs -f

.PHONY: docker-oidc-logs-backend
docker-oidc-logs-backend: ## View backend logs only
	docker compose -f docker-compose.oidc-test.yml logs -f backend

.PHONY: docker-oidc-logs-authelia
docker-oidc-logs-authelia: ## View Authelia logs only
	docker compose -f docker-compose.oidc-test.yml logs -f authelia

.PHONY: docker-oidc-status
docker-oidc-status: ## Check OIDC testing environment status
	docker compose -f docker-compose.oidc-test.yml ps

.PHONY: docker-oidc-down
docker-oidc-down: ## Stop OIDC testing environment
	$(call check_docker)
	$(call info_msg,Stopping OIDC testing environment...)
	docker compose -f docker-compose.oidc-test.yml down
	$(call success_msg,OIDC testing environment stopped)

.PHONY: docker-oidc-reset
docker-oidc-reset: ## Reset OIDC testing environment (stop + remove volumes + restart)
	$(call check_docker)
	$(call info_msg,Resetting OIDC testing environment...)
	docker compose -f docker-compose.oidc-test.yml down -v
	$(call info_msg,Starting fresh OIDC testing environment...)
	docker compose -f docker-compose.oidc-test.yml up -d
	$(call success_msg,OIDC testing environment reset and restarted)

.PHONY: docker-oidc-test-user-create
docker-oidc-test-user-create: ## Create a local user in OIDC test environment (usage: make docker-oidc-test-user-create USERNAME=testuser PASSWORD=testpass)
	@if [ -z "$(USERNAME)" ] || [ -z "$(PASSWORD)" ]; then \
		echo "$(COLOR_RED)Error: USERNAME and PASSWORD required$(COLOR_RESET)"; \
		echo "Usage: make docker-oidc-test-user-create USERNAME=testuser PASSWORD=testpass"; \
		exit 1; \
	fi
	$(call check_docker)
	$(call info_msg,Creating local user in OIDC test environment...)
	docker compose -f docker-compose.oidc-test.yml exec backend \
		python scripts/manage_users.py create $(USERNAME) $(PASSWORD)
	$(call success_msg,User $(USERNAME) created)

.PHONY: docker-oidc-test-db
docker-oidc-test-db: ## Access PostgreSQL database in OIDC test environment
	docker compose -f docker-compose.oidc-test.yml exec postgres psql \
		-U parchmark_user -d parchmark_db
