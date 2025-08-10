# ParchMark Monorepo Makefile
# Provides convenient commands for development, building, testing, and deployment

.PHONY: help dev-frontend dev-backend build-frontend build-backend docker-up docker-down test-frontend test-backend lint-frontend lint-backend install-frontend install-backend clean setup

# Default target
help:
	@echo "ParchMark Monorepo - Available Commands:"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev-frontend     Start frontend development server"
	@echo "  dev-backend      Start backend development server"
	@echo "  install-frontend Install frontend dependencies"
	@echo "  install-backend  Install backend dependencies"
	@echo ""
	@echo "Build Commands:"
	@echo "  build-frontend   Build frontend for production"
	@echo "  build-backend    Build backend Docker image"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-up        Start all services with docker-compose"
	@echo "  docker-down      Stop all services"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test-frontend    Run frontend tests"
	@echo "  test-backend     Run backend tests"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  lint-frontend    Run frontend linting"
	@echo "  lint-backend     Run backend linting"
	@echo ""
	@echo "Utility Commands:"
	@echo "  setup            Install all dependencies"
	@echo "  clean            Clean build artifacts"

# Development Commands
dev-frontend:
	@echo "Starting frontend development server..."
	cd ui && npm run dev

dev-backend:
	@echo "Starting backend development server..."
	cd backend && uv run uvicorn app.main:app --reload

# Installation Commands
install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && uv sync

# Build Commands
build-frontend:
	@echo "Building frontend for production..."
	cd frontend && npm run build

build-backend:
	@echo "Building backend Docker image..."
	cd backend && docker build -t parchmark-backend .

# Docker Commands
docker-up:
	@echo "Starting all services with docker-compose..."
	docker-compose up -d

docker-down:
	@echo "Stopping all services..."
	docker-compose down

# Testing Commands
test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

test-backend:
	@echo "Running backend tests..."
	cd backend && uv run pytest

# Code Quality Commands
lint-frontend:
	@echo "Running frontend linting..."
	cd frontend && npm run lint

lint-backend:
	@echo "Running backend linting..."
	cd backend && uv run ruff check .

# Utility Commands
setup: install-frontend install-backend
	@echo "All dependencies installed successfully!"

clean:
	@echo "Cleaning build artifacts..."
	cd frontend && rm -rf dist node_modules/.cache
	cd backend && rm -rf .pytest_cache __pycache__ .coverage htmlcov
	docker system prune -f

