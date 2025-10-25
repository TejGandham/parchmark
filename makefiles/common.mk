# Common variables and functions for ParchMark Makefiles

# Color codes for terminal output
BLUE := \033[1;34m
GREEN := \033[1;32m
YELLOW := \033[1;33m
RED := \033[1;31m
NC := \033[0m

# Python version for backend
PYTHON_VERSION := 3.13

# Common echo functions
define info_msg
	@echo "$(BLUE)$(1)$(NC)"
endef

define success_msg
	@echo "$(GREEN)✓ $(1)$(NC)"
endef

define error_msg
	@echo "$(RED)Error: $(1)$(NC)"
endef

define warning_msg
	@echo "$(YELLOW)$(1)$(NC)"
endef
