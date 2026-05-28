#!/usr/bin/env bash
# 一键拉起 DevContainer 栈（PostgreSQL + MailHog + FastAPI + Next.js），并等待健康检查通过。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.devcontainer/.env"

bash "$ROOT/scripts/devcontainer-ensure-images.sh"
bash "$ROOT/scripts/devcontainer-resolve-ports.sh"
# shellcheck source=/dev/null
source "$ENV_FILE"

COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$ROOT/.devcontainer/docker-compose.yml")

echo "🔨 构建 DevContainer 工作区镜像..."
"${COMPOSE[@]}" build workspace

echo "🚀 启动 DevContainer 服务..."
"${COMPOSE[@]}" up -d workspace db db_test mailhog backend frontend

echo "⏳ 等待 postgres 就绪..."
for _ in $(seq 1 60); do
  if "${COMPOSE[@]}" exec -T db pg_isready -U postgres -d mydatabase >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "🗂️  应用数据库迁移..."
if "${COMPOSE[@]}" exec -T backend uv run alembic upgrade head; then
  echo "✅ 数据库迁移完成"
else
  echo "⚠️  数据库迁移失败（可稍后执行 make dc-migrate）"
fi

echo "👤 创建初始 admin 账号..."
if "${COMPOSE[@]}" exec -T backend uv run python -m commands.seed_admin; then
  echo "✅ 初始 admin: admin@dty.com / admin123"
else
  echo "⚠️  admin 账号创建失败（可稍后执行 make dc-seed）"
fi

echo "⏳ 等待 FastAPI / Next.js 就绪..."
for i in $(seq 1 120); do
  api_code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${BACKEND_PORT}/docs" 2>/dev/null || true)"
  web_code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${FRONTEND_PORT}/" 2>/dev/null || true)"
  if [[ "$api_code" == "200" && "$web_code" =~ ^(200|307|308)$ ]]; then
    echo "✅ DevContainer 已就绪（尝试 ${i}/120）"
    echo ""
    echo "  前端:    http://localhost:${FRONTEND_PORT}"
    echo "  后端:    http://localhost:${BACKEND_PORT}/docs"
    echo "  MailHog: http://localhost:8025"
    echo ""
    echo "  初始 admin: admin@dty.com / admin123"
    echo "  端口配置: ${ENV_FILE}"
    echo "  进入工作区: make dc-sh"
    echo "  查看日志:   make dc-logs"
    echo "  停止栈:     make dcs  或  make dcd"
    exit 0
  fi
  sleep 2
done

echo "❌ 启动超时：FastAPI=${api_code:-unknown} Next.js=${web_code:-unknown}"
echo "---- docker compose ps ----"
"${COMPOSE[@]}" ps || true
echo "---- recent logs ----"
"${COMPOSE[@]}" logs --tail=80 db backend frontend || true
exit 1
