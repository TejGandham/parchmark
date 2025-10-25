# User management targets for ParchMark
# Uses templates to eliminate repetition across local/docker/prod environments

# Template for creating user management targets
# Arguments: $(1)=suffix (empty, -docker, -prod), $(2)=command prefix, $(3)=env description
define user-targets

.PHONY: user-create$(1)
user-create$(1): ## Create user ($(3))
	@if [ -z "$$(USERNAME)" ] || [ -z "$$(PASSWORD)" ]; then \
		echo "$(RED)Error: USERNAME and PASSWORD are required$(NC)"; \
		echo "Usage: make user-create$(1) USERNAME=admin PASSWORD=pass123"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating user '$$(USERNAME)' in $(3)...$(NC)"
	$(2) python scripts/manage_users.py create $$(USERNAME) $$(PASSWORD)

.PHONY: user-update-password$(1)
user-update-password$(1): ## Update user password ($(3))
	@if [ -z "$$(USERNAME)" ] || [ -z "$$(PASSWORD)" ]; then \
		echo "$(RED)Error: USERNAME and PASSWORD are required$(NC)"; \
		echo "Usage: make user-update-password$(1) USERNAME=admin PASSWORD=newpass"; \
		exit 1; \
	fi
	@echo "$(BLUE)Updating password for user '$$(USERNAME)' in $(3)...$(NC)"
	$(2) python scripts/manage_users.py update-password $$(USERNAME) $$(PASSWORD)

.PHONY: user-delete$(1)
user-delete$(1): ## Delete user ($(3))
	@if [ -z "$$(USERNAME)" ]; then \
		echo "$(RED)Error: USERNAME is required$(NC)"; \
		echo "Usage: make user-delete$(1) USERNAME=admin"; \
		exit 1; \
	fi
	@echo "$(BLUE)Deleting user '$$(USERNAME)' from $(3)...$(NC)"
	$(2) python scripts/manage_users.py delete $$(USERNAME)

.PHONY: user-list$(1)
user-list$(1): ## List all users ($(3))
	@echo "$(BLUE)Listing users in $(3)...$(NC)"
	$(2) python scripts/manage_users.py list

endef

# Generate targets for each environment
$(eval $(call user-targets,,cd backend && uv run,local dev))
$(eval $(call user-targets,-docker,docker compose exec backend,docker dev))
$(eval $(call user-targets,-prod,docker compose -f docker-compose.prod.yml exec backend,production))
