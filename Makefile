# Makefile

# Variables
BACKEND_DIR=apps/backend
BACKEND_OSS_GATEWAY_DIR=apps/backend_oss_gateway
FRONTEND_DIR=apps/frontend
ROOT_DIR=.
DEVCONTAINER_ENV=.devcontainer/.env
DEVCONTAINER_COMPOSE=docker compose --env-file $(DEVCONTAINER_ENV) -f .devcontainer/docker-compose.yml

# Help (default when running bare `make`)
.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Dependencies"
	@echo "  sync-deps     Install uv + bun dependencies (repo root)"
	@echo ""
	@echo "Local dev"
	@echo "  start-backend            Start FastAPI with hot reload  (:9210)"
	@echo "  start-backend-oss-gateway Start OSS Gateway with hot reload (:8020)"
	@echo "  start-frontend           Start Next.js with hot reload (:3000)"
	@echo "  test-backend             Run backend tests (pytest)"
	@echo "  test-backend-oss-gateway Run OSS gateway tests (pytest)"
	@echo "  seed-admin               Create admin user locally"
	@echo ""
	@echo "Dev Container (recommended — includes OSS Gateway)"
	@echo "  dc / dcu        Start full stack (DB + MailHog + backend + oss gateway + frontend)"
	@echo "  dc-status       Show Dev Container services, ports, and reachability"
	@echo "  dcd             Stop and remove containers"
	@echo "  dcs             Stop containers (keep volumes)"
	@echo "  dc-sh           Open workspace shell"
	@echo "  dc-logs         Follow logs (e.g. make dc-logs s=backend)"
	@echo "  dc-migrate      Run Alembic migrations (backend)"
	@echo "  dc-migrate-oss  Run Alembic migrations (oss gateway)"
	@echo "  dc-seed         Seed admin user (admin@dty.com / admin123)"
	@echo "  dc-rebuild      Rebuild workspace image and restart"
	@echo "  dc-deps         Install uv + bun inside container"
	@echo ""

# Workspace
.PHONY: sync-deps

sync-deps:
	uv sync
	cd $(ROOT_DIR) && bun install

# Backend
.PHONY: start-backend test-backend seed-admin start-backend-oss-gateway test-backend-oss-gateway

start-backend:
	cd $(BACKEND_DIR) && ./start.sh

start-backend-oss-gateway:
	cd $(BACKEND_OSS_GATEWAY_DIR) && ./start.sh

test-backend:
	cd $(BACKEND_DIR) && uv run pytest

test-backend-oss-gateway:
	cd $(BACKEND_OSS_GATEWAY_DIR) && uv run pytest

seed-admin:
	cd $(BACKEND_DIR) && uv run python -m commands.seed_admin

# Frontend
.PHONY: start-frontend test-frontend

start-frontend:
	cd $(FRONTEND_DIR) && ./start.sh

test-frontend:
	cd $(FRONTEND_DIR) && bun run test

# Dev Container
.PHONY: dc dcu dcd dcs dc-logs dc-sh dc-migrate dc-migrate-oss dc-seed dc-deps dc-rebuild dc-env dc-images dc-status

dc-env:
	bash scripts/devcontainer-resolve-ports.sh

dc-images:
	bash scripts/devcontainer-ensure-images.sh

dc: dc-env
	bash scripts/devcontainer-up.sh

dcu: dc

dc-status:
	bash scripts/devcontainer-status.sh

dcd: dc-env
	$(DEVCONTAINER_COMPOSE) down

dcs: dc-env
	$(DEVCONTAINER_COMPOSE) stop

dc-rebuild:
	bash scripts/devcontainer-ensure-images.sh
	$(DEVCONTAINER_COMPOSE) build --no-cache workspace
	bash scripts/devcontainer-up.sh

dc-logs: dc-env
	$(DEVCONTAINER_COMPOSE) logs -f $(s)

dc-sh: dc-env
	$(DEVCONTAINER_COMPOSE) exec workspace bash

dc-migrate: dc-env
	$(DEVCONTAINER_COMPOSE) exec backend uv run alembic upgrade head

dc-migrate-oss: dc-env
	$(DEVCONTAINER_COMPOSE) exec oss uv run alembic upgrade head

dc-seed: dc-env
	$(DEVCONTAINER_COMPOSE) exec backend uv run python -m commands.seed_admin

dc-deps:
	$(DEVCONTAINER_COMPOSE) run --rm workspace bash .devcontainer/post-create.sh
