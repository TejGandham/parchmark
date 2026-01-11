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
deploy-trigger: ## Show deployment instructions (manual SSH required)
	$(call info_msg,Deployment is now manual via SSH)
	@echo ""
	@echo "$(YELLOW)To deploy to production:$(NC)"
	@echo "  1. Ensure images are built: check GitHub Actions status"
	@echo "  2. SSH into production: make deploy-ssh"
	@echo "  3. Navigate to project: cd $(PROD_DIR)"
	@echo "  4. Pull latest config: git pull origin main"
	@echo "  5. Run update script: ./deploy/update.sh"
	@echo ""
	@echo "$(BLUE)Or use: make deploy-ssh$(NC)"

.PHONY: deploy-watch
deploy-watch: ## Watch GitHub Actions build progress
	$(call info_msg,Watching build progress...)
	@gh run watch || ($(call warning_msg,Install gh CLI: brew install gh) && exit 1)

# ============================================================================
# ROLLBACK OPERATIONS
# ============================================================================

.PHONY: deploy-rollback
deploy-rollback: ## Rollback to specific SHA (usage: make deploy-rollback SHA=abc123)
ifndef SHA
	$(call error_msg,SHA parameter required. Usage: make deploy-rollback SHA=abc123)
	@exit 1
else
	$(call info_msg,Rollback instructions for SHA: $(SHA))
	@echo ""
	@echo "$(YELLOW)To rollback to SHA $(SHA):$(NC)"
	@echo "  1. SSH into production: make deploy-ssh"
	@echo "  2. Navigate to project: cd $(PROD_DIR)"
	@echo "  3. Edit docker-compose.prod.yml to use specific tags:"
	@echo "     image: $(GHCR_BACKEND_IMAGE):sha-$(SHA)"
	@echo "     image: $(GHCR_FRONTEND_IMAGE):sha-$(SHA)"
	@echo "  4. Run update script: ./deploy/update.sh"
	@echo ""
	@echo "$(BLUE)Available images: make deploy-list-images$(NC)"
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
	$(call check_docker)
	$(call info_msg,Building production images locally...)
	@docker build -t $(GHCR_BACKEND_IMAGE):local -f backend/Dockerfile.prod backend/
	@docker build -t $(GHCR_FRONTEND_IMAGE):local -f ui/Dockerfile ui/
	$(call success_msg,Local production images built)

.PHONY: deploy-test-local
deploy-test-local: ## Validate docker-compose.prod.yml configuration
	$(call check_docker)
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
	@echo "  3. SSH to production: make deploy-ssh"
	@echo "  4. Run update script: ./deploy/update.sh"
	@echo "  5. Verify with: make deploy-verify"

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
	@echo "  3. Build Images"
	@echo "     git push origin main       # Push to main (auto-triggers build)"
	@echo "     make deploy-status         # Check build status"
	@echo ""
	@echo "  4. Deploy to Production"
	@echo "     make deploy-ssh            # SSH into production server"
	@echo "     cd /home/deploy/parchmark  # Navigate to project"
	@echo "     git pull origin main       # Pull latest config (if needed)"
	@echo "     ./deploy/update.sh         # Run the update script"
	@echo ""
	@echo "  5. Verify Deployment"
	@echo "     make deploy-verify         # Health check backend + frontend"
	@echo "     make deploy-logs           # View container logs"
	@echo ""
	@echo "$(GREEN)🔄 ROLLBACK PROCESS:$(NC)"
	@echo "  make deploy-list-images              # List available SHA tags"
	@echo "  make deploy-rollback SHA=abc123      # Show rollback instructions"
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
	@echo "  deploy/SERVER_SETUP.md                  # Server setup guide"
	@echo "  deploy/update.sh                        # Update script"
	@echo "  docs/deployment_upgrade/FUTURE_IMPROVEMENTS.md"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
