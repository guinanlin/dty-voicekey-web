#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$(cd "$BACKEND_DIR/../frontend" && pwd)"

# 步骤 1: 进入后端项目目录并生成 OpenAPI
cd "$BACKEND_DIR"
uv run python -m commands.generate_openapi_schema

# 步骤 2: 进入前端项目目录并生成 API 客户端
cd "$FRONTEND_DIR"
bun run generate-client

echo "前端 API 客户端已生成，请检查使用。"
