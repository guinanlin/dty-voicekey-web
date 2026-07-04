#!/usr/bin/env bash
# 本地复现 GitHub CI + pre-commit 检查（与 .github/workflows 对齐）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# 测试库：Dev Container 内用 db_test:5432；宿主机用 localhost:5610
if getent hosts db_test >/dev/null 2>&1; then
  DB_HOST="db_test"
  DB_PORT="5432"
else
  DB_HOST="localhost"
  DB_PORT="${POSTGRES_TEST_PORT:-5610}"
fi
DB_URL="postgresql+asyncpg://postgres:password@${DB_HOST}:${DB_PORT}/testdatabase"

echo "=============================================="
echo "  CI 本地验证"
echo "  测试库: ${DB_HOST}:${DB_PORT}"
echo "=============================================="
echo ""

step() {
  echo ""
  echo ">>> $1"
  echo "----------------------------------------------"
}

# --- 1. 后端（FastAPI CI）---
step "Backend: uv sync + pytest"
export DATABASE_URL="$DB_URL"
export TEST_DATABASE_URL="$DB_URL"
export ACCESS_SECRET_KEY="ci-access-secret"
export RESET_PASSWORD_SECRET_KEY="ci-reset-secret"
export VERIFICATION_SECRET_KEY="ci-verification-secret"
export CORS_ORIGINS='["*"]'
export REDIS_URL="${REDIS_URL:-memory}"

(
  cd apps/backend
  uv sync --all-extras --dev
  uv run coverage run -m pytest
  uv run coverage xml -o coverage.xml
)

# --- 2. 前端（Next.js CI）---
step "Frontend: install + tsc + lint + test + build"
(
  cd apps/frontend
  bun install --frozen-lockfile
  bun run tsc
  bun run lint
  bun run coverage
  bun run build
)

# --- 3. pre-commit ---
step "pre-commit: all hooks"
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export TEST_DATABASE_URL="sqlite+aiosqlite:///:memory:"
export ACCESS_SECRET_KEY="pre-commit-access-secret"
export RESET_PASSWORD_SECRET_KEY="pre-commit-reset-secret"
export VERIFICATION_SECRET_KEY="pre-commit-verification-secret"
export OPENAPI_OUTPUT_FILE="../frontend/openapi.json"
export CORS_ORIGINS='["*"]'

if ! command -v pre-commit >/dev/null 2>&1; then
  echo "未找到 pre-commit，正在安装..."
  uv tool install pre-commit
fi

pre-commit run --all-files

echo ""
echo "=============================================="
echo "  全部通过"
echo "=============================================="
