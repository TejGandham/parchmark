# Docker targets for ParchMark

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
