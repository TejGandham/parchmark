# UI (Frontend) targets for ParchMark

.PHONY: test-ui-install
test-ui-install: ## Install UI dependencies
	$(call info_msg,Installing UI dependencies...)
	cd ui && npm ci
	$(call success_msg,UI dependencies installed)

.PHONY: test-ui-lint
test-ui-lint: ## Run ESLint on frontend code
	$(call info_msg,Running UI linting...)
	cd ui && npm run lint
	$(call success_msg,UI linting passed)

.PHONY: test-ui-format
test-ui-format: ## Format frontend code with Prettier
	$(call info_msg,Formatting UI code with Prettier...)
	cd ui && npm run format
	$(call success_msg,UI code formatted)

.PHONY: test-ui-test
test-ui-test: ## Run Vitest tests with coverage
	$(call info_msg,Running UI tests...)
	cd ui && npm run test:coverage
	$(call success_msg,UI tests passed)

.PHONY: test-ui-all
test-ui-all: test-ui-lint test-ui-test ## Run all UI tests
	$(call success_msg,All UI tests passed)

.PHONY: test-ui-oidc
test-ui-oidc: ## Run OIDC-specific frontend tests
	$(call info_msg,Running OIDC component tests...)
	cd ui && npm test -- __tests__/features/auth/components/OIDCCallback.test.tsx __tests__/features/auth/utils/oidcUtils.test.ts __tests__/features/auth/store/auth.oidc.test.ts
	$(call success_msg,OIDC tests passed)

.PHONY: test-ui-auth
test-ui-auth: ## Run all authentication tests (local + OIDC)
	$(call info_msg,Running all authentication tests...)
	cd ui && npm test -- __tests__/features/auth/
	$(call success_msg,Authentication tests passed)

.PHONY: dev-ui
dev-ui: ## Start UI development server
	$(call info_msg,Starting UI development server...)
	cd ui && npm run dev
