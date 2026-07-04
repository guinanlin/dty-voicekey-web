#!/usr/bin/env bash
# 从后端生成 OpenAPI schema，并同步前端 TypeScript client。
# pre-commit 与本地开发在改 backend schema 后应运行此脚本并提交产物。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${OPENAPI_OUTPUT_FILE:=../frontend/openapi.json}"
: "${DATABASE_URL:=sqlite+aiosqlite:///:memory:}"
: "${TEST_DATABASE_URL:=sqlite+aiosqlite:///:memory:}"
: "${ACCESS_SECRET_KEY:=dev-access-secret}"
: "${RESET_PASSWORD_SECRET_KEY:=dev-reset-secret}"
: "${VERIFICATION_SECRET_KEY:=dev-verification-secret}"
: "${CORS_ORIGINS:=[\"*\"]}"

export OPENAPI_OUTPUT_FILE DATABASE_URL TEST_DATABASE_URL
export ACCESS_SECRET_KEY RESET_PASSWORD_SECRET_KEY VERIFICATION_SECRET_KEY CORS_ORIGINS

echo ">>> Generating OpenAPI schema -> apps/frontend/openapi.json"
(
  cd apps/backend
  uv run python -m commands.generate_openapi_schema
)

echo ">>> Generating frontend client -> apps/frontend/app/openapi-client"
(
  cd apps/frontend
  bun run generate-client
)

echo ">>> Done. Commit apps/frontend/openapi.json and app/openapi-client/ if changed."
