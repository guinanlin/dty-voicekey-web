#!/usr/bin/env bash
set -euo pipefail

ROOT="/workspaces/nextjs-fastapi-template"
cd "$ROOT"

mkdir -p shared-data apps/backend/logs apps/backend_oss_gateway/logs apps/backend_oss_gateway/storage

if [[ ! -f apps/backend/.env ]]; then
  cp apps/backend/.env.example apps/backend/.env
  echo ">>> 已创建 apps/backend/.env（来自 .env.example）"
fi

if [[ ! -f apps/backend_oss_gateway/.env ]]; then
  cp apps/backend_oss_gateway/.env.example apps/backend_oss_gateway/.env
  echo ">>> 已创建 apps/backend_oss_gateway/.env（来自 .env.example）"
fi

if [[ ! -f apps/frontend/.env.local ]]; then
  cp apps/frontend/.env.example apps/frontend/.env.local
  echo ">>> 已创建 apps/frontend/.env.local（来自 .env.example）"
fi

echo ">>> 安装 Python workspace 依赖 (uv sync)..."
uv sync --frozen

echo ">>> 安装 TypeScript workspace 依赖 (bun install)..."
bun install --frozen-lockfile

echo ">>> post-create 完成。应用栈已由 compose 启动；迁移可执行: make dc-migrate"
