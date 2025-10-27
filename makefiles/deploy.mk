# Deployment targets for ParchMark production
# These targets help manage deployment via GitHub Actions and production server

# Production URLs
PROD_BACKEND_URL := https://assets-api.engen.tech
PROD_FRONTEND_URL := https://notes.engen.tech
PROD_HOST := notes.engen.tech
PROD_USER := deploy
PROD_DIR := /home/deploy/parchmark

# GitHub Container Registry
GHCR_REGISTRY := ghcr.io
GHCR_USERNAME := tejgandham
GHCR_BACKEND_IMAGE := $(GHCR_REGISTRY)/$(GHCR_USERNAME)/parchmark-backend
GHCR_FRONTEND_IMAGE := $(GHCR_REGISTRY)/$(GHCR_USERNAME)/parchmark-frontend

# ============================================================================
# DEPLOYMENT VERIFICATION
# ============================================================================

.PHONY: deploy-verify
deploy-verify: ## Verify production deployment health
	$(call info_msg,Checking production health...)
	@echo ""
	@echo "$(BLUE)Backend Health:$(NC)"
	@curl -sf $(PROD_BACKEND_URL)/api/health | python3 -m json.tool || ($(call error_msg,Backend health check failed) && exit 1)
	@echo ""
	@echo "$(BLUE)Frontend Status:$(NC)"
	@curl -sf -o /dev/null -w "HTTP Status: %{http_code}\n" $(PROD_FRONTEND_URL)/ || ($(call error_msg,Frontend health check failed) && exit 1)
	@echo ""
	$(call success_msg,Production deployment is healthy)

.PHONY: deploy-verify-backend
deploy-verify-backend: ## Verify backend health only
	$(call info_msg,Checking backend health...)
	@curl -sf $(PROD_BACKEND_URL)/api/health | python3 -m json.tool

.PHONY: deploy-verify-frontend
deploy-verify-frontend: ## Verify frontend health only
	$(call info_msg,Checking frontend health...)
	@curl -sf -o /dev/null -w "HTTP Status: %{http_code}\n" $(PROD_FRONTEND_URL)/

# ============================================================================
# DEPLOYMENT STATUS & LOGS
# ============================================================================

.PHONY: deploy-status
deploy-status: ## Check recent GitHub Actions deployment runs
	$(call info_msg,Fetching recent deployment runs...)
	@gh run list --workflow=deploy.yml --limit=10 || ($(call warning_msg,Install gh CLI: brew install gh) && exit 1)

.PHONY: deploy-status-latest
deploy-status-latest: ## Show detailed status of latest deployment
	$(call info_msg,Fetching latest deployment run...)
	@gh run view --workflow=deploy.yml || ($(call warning_msg,Install gh CLI: brew install gh) && exit 1)

.PHONY: deploy-logs
deploy-logs: ## View production container logs
	$(call info_msg,Fetching production logs (requires SSH access)...)
	@echo "$(BLUE)Backend logs (last 50 lines):$(NC)"
	@ssh $(PROD_USER)@$(PROD_HOST) "cd $(PROD_DIR) && docker compose -f docker-compose.prod.yml logs --tail=50 backend" || ($(call error_msg,SSH access required) && exit 1)
	@echo ""
	@echo "$(BLUE)Frontend logs (last 50 lines):$(NC)"
	@ssh $(PROD_USER)@$(PROD_HOST) "cd $(PROD_DIR) && docker compose -f docker-compose.prod.yml logs --tail=50 frontend"

.PHONY: deploy-logs-follow
deploy-logs-follow: ## Follow production logs in real-time
	$(call info_msg,Following production logs (Ctrl+C to exit)...)
	@ssh $(PROD_USER)@$(PROD_HOST) "cd $(PROD_DIR) && docker compose -f docker-compose.prod.yml logs -f" || ($(call error_msg,SSH access required) && exit 1)

.PHONY: deploy-logs-backend
deploy-logs-backend: ## View backend logs only
	$(call info_msg,Fetching backend logs...)
	@ssh $(PROD_USER)@$(PROD_HOST) "cd $(PROD_DIR) && docker compose -f docker-compose.prod.yml logs --tail=100 backend"

.PHONY: deploy-logs-frontend
deploy-logs-frontend: ## View frontend logs only
	$(call info_msg,Fetching frontend logs...)
	@ssh $(PROD_USER)@$(PROD_HOST) "cd $(PROD_DIR) && docker compose -f docker-compose.prod.yml logs --tail=100 frontend"

# ============================================================================
# DEPLOYMENT TRIGGER
# ============================================================================

.PHONY: deploy-trigger
deploy-trigger: ## Manually trigger GitHub Actions deployment
	$(call info_msg,Triggering GitHub Actions deployment...)
	@echo "$(YELLOW)This will trigger a production deployment.$(NC)"
	@echo "$(YELLOW)Ensure all changes are committed and pushed to main branch.$(NC)"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || (echo "Cancelled" && exit 1)
	@gh workflow run deploy.yml || ($(call warning_msg,Install gh CLI: brew install gh) && exit 1)
	$(call success_msg,Deployment triggered - check status with 'make deploy-status')

.PHONY: deploy-watch
deploy-watch: ## Watch latest deployment run progress
	$(call info_msg,Watching deployment progress...)
	@gh run watch --workflow=deploy.yml || ($(call warning_msg,Install gh CLI: brew install gh) && exit 1)

# ============================================================================
# ROLLBACK OPERATIONS
# ============================================================================

.PHONY: deploy-rollback
deploy-rollback: ## Rollback to specific SHA (usage: make deploy-rollback SHA=abc123)
ifndef SHA
	$(call error_msg,SHA parameter required. Usage: make deploy-rollback SHA=abc123)
	@exit 1
else
	$(call info_msg,Rolling back to SHA: $(SHA))
	@echo "$(YELLOW)This will update production to use images tagged with SHA $(SHA).$(NC)"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || (echo "Cancelled" && exit 1)
	@ssh $(PROD_USER)@$(PROD_HOST) "\
		cd $(PROD_DIR) && \
		export BACKEND_IMAGE='$(GHCR_BACKEND_IMAGE):sha-$(SHA)' && \
		export FRONTEND_IMAGE='$(GHCR_FRONTEND_IMAGE):sha-$(SHA)' && \
		docker compose -f docker-compose.prod.yml pull backend frontend && \
		docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend && \
		echo 'Waiting for services to start...' && \
		sleep 10" || ($(call error_msg,Rollback failed) && exit 1)
	@echo ""
	$(call info_msg,Verifying rollback...)
	@sleep 5
	@$(MAKE) deploy-verify
	$(call success_msg,Rollback to SHA $(SHA) complete)
endif

.PHONY: deploy-list-images
deploy-list-images: ## List available image versions for rollback
	$(call info_msg,Fetching available images from GHCR...)
	@echo "$(BLUE)Backend images:$(NC)"
	@gh api /users/$(GHCR_USERNAME)/packages/container/parchmark-backend/versions --jq '.[0:10] | .[] | "  sha-" + .metadata.container.tags[0] + " (created: " + .created_at + ")"' || ($(call warning_msg,Install gh CLI: brew install gh) && exit 1)
	@echo ""
	@echo "$(BLUE)Frontend images:$(NC)"
	@gh api /users/$(GHCR_USERNAME)/packages/container/parchmark-frontend/versions --jq '.[0:10] | .[] | "  sha-" + .metadata.container.tags[0] + " (created: " + .created_at + ")"'

# ============================================================================
# LOCAL BUILD & TEST
# ============================================================================

.PHONY: deploy-build-local
deploy-build-local: ## Build production Docker images locally
	$(call info_msg,Building production images locally...)
	@docker build -t $(GHCR_BACKEND_IMAGE):local -f backend/Dockerfile.prod backend/
	@docker build -t $(GHCR_FRONTEND_IMAGE):local -f ui/Dockerfile ui/
	$(call success_msg,Local production images built)

.PHONY: deploy-test-local
deploy-test-local: ## Validate docker-compose.prod.yml configuration
	$(call info_msg,Validating production docker-compose configuration...)
	@docker compose -f docker-compose.prod.yml config > /dev/null
	$(call success_msg,Production docker-compose.yml is valid)

.PHONY: deploy-push-check
deploy-push-check: ## Pre-deployment checks before pushing to main
	$(call info_msg,Running pre-deployment checks...)
	@echo ""
	@echo "$(BLUE)1. Checking git status...$(NC)"
	@git status --short
	@echo ""
	@echo "$(BLUE)2. Checking current branch...$(NC)"
	@git branch --show-current
	@echo ""
	@echo "$(BLUE)3. Running all tests...$(NC)"
	@$(MAKE) test-all
	@echo ""
	@echo "$(BLUE)4. Validating docker-compose files...$(NC)"
	@$(MAKE) deploy-test-local
	@echo ""
	$(call success_msg,All pre-deployment checks passed)
	@echo ""
	@echo "$(YELLOW)Ready to deploy:$(NC)"
	@echo "  1. Commit and push to main branch"
	@echo "  2. Wait for GitHub Actions to build images"
	@echo "  3. Approve deployment in GitHub (production environment)"
	@echo "  4. Verify with: make deploy-verify"

# ============================================================================
# SSH OPERATIONS
# ============================================================================

.PHONY: deploy-ssh
deploy-ssh: ## SSH into production server
	$(call info_msg,Connecting to production server...)
	@ssh $(PROD_USER)@$(PROD_HOST)

.PHONY: deploy-ps
deploy-ps: ## Show running containers on production
	$(call info_msg,Fetching container status...)
	@ssh $(PROD_USER)@$(PROD_HOST) "cd $(PROD_DIR) && docker compose -f docker-compose.prod.yml ps"

.PHONY: deploy-disk-usage
deploy-disk-usage: ## Check disk usage on production server
	$(call info_msg,Checking disk usage...)
	@ssh $(PROD_USER)@$(PROD_HOST) "df -h && echo '' && docker system df"

# ============================================================================
# DEPLOYMENT HELP
# ============================================================================

.PHONY: deploy-help
deploy-help: ## Show comprehensive deployment workflow guide
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  ParchMark Deployment Workflow Guide$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)📋 DEPLOYMENT PROCESS:$(NC)"
	@echo "  1. Development & Testing"
	@echo "     make test-all              # Run all tests locally"
	@echo "     make deploy-test-local     # Validate docker-compose files"
	@echo ""
	@echo "  2. Pre-Deployment Checks"
	@echo "     make deploy-push-check     # Run all pre-deployment checks"
	@echo ""
	@echo "  3. Trigger Deployment"
	@echo "     git push origin main       # Push to main (auto-triggers workflow)"
	@echo "     make deploy-trigger        # OR manually trigger via gh CLI"
	@echo ""
	@echo "  4. Monitor Deployment"
	@echo "     make deploy-status         # Check deployment runs"
	@echo "     make deploy-watch          # Watch deployment progress"
	@echo ""
	@echo "  5. Verify Deployment"
	@echo "     make deploy-verify         # Health check backend + frontend"
	@echo "     make deploy-logs           # View container logs"
	@echo ""
	@echo "$(GREEN)🔄 ROLLBACK PROCESS:$(NC)"
	@echo "  make deploy-list-images              # List available SHA tags"
	@echo "  make deploy-rollback SHA=abc123      # Rollback to specific version"
	@echo ""
	@echo "$(GREEN)📊 MONITORING:$(NC)"
	@echo "  make deploy-verify             # Health checks"
	@echo "  make deploy-ps                 # Container status"
	@echo "  make deploy-logs               # View logs"
	@echo "  make deploy-logs-follow        # Follow logs real-time"
	@echo "  make deploy-disk-usage         # Check disk space"
	@echo ""
	@echo "$(GREEN)🔧 TROUBLESHOOTING:$(NC)"
	@echo "  make deploy-ssh                # SSH into production"
	@echo "  make deploy-logs-backend       # Backend logs only"
	@echo "  make deploy-logs-frontend      # Frontend logs only"
	@echo ""
	@echo "$(GREEN)🔗 PRODUCTION URLS:$(NC)"
	@echo "  Frontend: $(PROD_FRONTEND_URL)"
	@echo "  Backend:  $(PROD_BACKEND_URL)"
	@echo "  API Docs: $(PROD_BACKEND_URL)/docs"
	@echo ""
	@echo "$(YELLOW)📚 Documentation:$(NC)"
	@echo "  docs/deployment_upgrade/DEPLOYMENT_VALIDATED.md"
	@echo "  docs/deployment_upgrade/DEPLOYMENT_PROGRESS.md"
	@echo "  docs/deployment_upgrade/FUTURE_IMPROVEMENTS.md"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
