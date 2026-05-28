# Makefile

# Variables
BACKEND_DIR=apps/backend
FRONTEND_DIR=apps/frontend
ROOT_DIR=.
DOCKER_COMPOSE=docker compose -f docker/docker-compose.yml
DEVCONTAINER_ENV=.devcontainer/.env
DEVCONTAINER_COMPOSE=docker compose --env-file $(DEVCONTAINER_ENV) -f .devcontainer/docker-compose.yml

# Workspace
.PHONY: sync-deps

sync-deps: ## Install all workspace dependencies (uv + bun at repo root)
	uv sync
	cd $(ROOT_DIR) && bun install

# Help
.PHONY: help
help:
	@echo "Available commands:"
	@awk '/^[a-zA-Z_-]+:/{split($$1, target, ":"); print "  " target[1] "\t" substr($$0, index($$0,$$2))}' $(MAKEFILE_LIST)

# Backend commands
.PHONY: start-backend test-backend

start-backend: ## Start the backend server with FastAPI and hot reload
	cd $(BACKEND_DIR) && ./start.sh

test-backend: ## Run backend tests using pytest
	cd $(BACKEND_DIR) && uv run pytest


# Frontend commands
.PHONY: start-frontend test-frontend

start-frontend: ## Start the frontend server with Bun and hot reload
	cd $(FRONTEND_DIR) && ./start.sh

test-frontend: ## Run frontend tests using bun
	cd $(FRONTEND_DIR) && bun run test


# Docker commands
.PHONY: docker-backend-shell docker-frontend-shell docker-build docker-build-backend \
        docker-build-frontend docker-start-backend docker-start-frontend docker-up-test-db \
        docker-migrate-db docker-db-schema docker-test-backend docker-test-frontend


docker-backend-shell: ## Access the backend container shell
	$(DOCKER_COMPOSE) run --rm backend sh

docker-frontend-shell: ## Access the frontend container shell
	$(DOCKER_COMPOSE) run --rm frontend sh

docker-build: ## Build all the services
	$(DOCKER_COMPOSE) build --no-cache

docker-build-backend: ## Build the backend container with no cache
	$(DOCKER_COMPOSE) build backend --no-cache

docker-build-frontend: ## Build the frontend container with no cache
	$(DOCKER_COMPOSE) build frontend --no-cache

docker-start-backend: ## Start the backend container
	$(DOCKER_COMPOSE) up backend

docker-start-frontend: ## Start the frontend container
	$(DOCKER_COMPOSE) up frontend

docker-up-test-db: ## Start the test database container
	$(DOCKER_COMPOSE) up db_test

docker-migrate-db: ## Run database migrations using Alembic
	$(DOCKER_COMPOSE) run --rm backend alembic upgrade head

docker-db-schema: ## Generate a new migration schema. Usage: make docker-db-schema migration_name="add users"
	$(DOCKER_COMPOSE) run --rm backend alembic revision --autogenerate -m "$(migration_name)"

docker-test-backend: ## Run tests for the backend
	$(DOCKER_COMPOSE) run --rm backend pytest

docker-test-frontend: ## Run tests for the frontend
	$(DOCKER_COMPOSE) run --rm frontend bun run test


# Dev Container commands
.PHONY: dc dcu dcd dcs dc-logs dc-sh dc-migrate dc-seed dc-deps dc-images dc-rebuild dc-env

dc-env: ## Resolve free host ports into .devcontainer/.env
	bash scripts/devcontainer-resolve-ports.sh

dc-images: ## Ensure devcontainer base images exist locally
	bash scripts/devcontainer-ensure-images.sh

dc: dc-env ## One-click devcontainer up (build + postgres + mailhog + backend + frontend)
	bash scripts/devcontainer-up.sh

dcu: dc ## Alias for dc

dcd: dc-env ## Stop and remove devcontainer containers/networks
	$(DEVCONTAINER_COMPOSE) down

dcs: dc-env ## Stop devcontainer without removing containers
	$(DEVCONTAINER_COMPOSE) stop

dc-rebuild: ## Rebuild devcontainer workspace image and restart stack
	bash scripts/devcontainer-ensure-images.sh
	$(DEVCONTAINER_COMPOSE) build --no-cache workspace
	bash scripts/devcontainer-up.sh

dc-logs: dc-env ## Follow devcontainer logs (optional: make dc-logs s=backend)
	$(DEVCONTAINER_COMPOSE) logs -f $(s)

dc-sh: dc-env ## Open a shell in the devcontainer workspace
	$(DEVCONTAINER_COMPOSE) exec workspace bash

dc-migrate: dc-env ## Run Alembic migrations in devcontainer backend
	$(DEVCONTAINER_COMPOSE) exec backend uv run alembic upgrade head

dc-seed: dc-env ## Create initial admin user (admin@dty.com / admin123)
	$(DEVCONTAINER_COMPOSE) exec backend uv run python -m commands.seed_admin

seed-admin: ## Create initial admin user locally (requires apps/backend/.env + running DB)
	cd $(BACKEND_DIR) && uv run python -m commands.seed_admin

dc-deps: ## Install workspace dependencies only (uv + bun)
	$(DEVCONTAINER_COMPOSE) run --rm workspace bash .devcontainer/post-create.sh