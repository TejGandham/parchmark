# Makefile for the ParchMark meta repository.
#
# Projects live in their own subdirectories; this Makefile delegates to their
# Makefiles so the familiar targets keep working from the repository root:
#
#   make test          ==  make -C parchmark-web test
#   make dev           ==  make -C parchmark-web dev
#   make <anything>    ==  make -C parchmark-web <anything>
#
# Run 'make help' for the full target list.

WEB_DIR := parchmark-web

.DEFAULT_GOAL := help

# ============================================================================
# META TARGETS
# ============================================================================

.PHONY: help
help: ## List the web project's targets (forwarded from parchmark-web/Makefile)
	@echo "ParchMark meta repository — project: $(WEB_DIR)/"
	@echo "Targets below are served by $(WEB_DIR)/Makefile; every target is forwarded."
	@echo ""
	@$(MAKE) --no-print-directory -C $(WEB_DIR) help

# ============================================================================
# DELEGATION
# ============================================================================

# Forward every other target to the web project (test, dev, user-create, deploy-*, ...).
%:
	@$(MAKE) --no-print-directory -C $(WEB_DIR) $@
