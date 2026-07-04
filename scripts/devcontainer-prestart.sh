#!/usr/bin/env bash
# DevContainer 启动前：停止宿主机上冲突的 Next.js，并清除共享 volume 中的 dev lock。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.devcontainer/.env"
LOCK_FILE="$ROOT/apps/frontend/.next/dev/lock"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$ENV_FILE"
fi
FRONTEND_PORT="${FRONTEND_PORT:-3600}"

echo "🧹 DevContainer 启动前检查（DevContainer 专用，不依赖宿主机 next dev）..."

read_lock_pid() {
  if [[ ! -f "$LOCK_FILE" ]]; then
    return 0
  fi
  grep -o '"pid":[0-9]*' "$LOCK_FILE" 2>/dev/null | head -1 | cut -d: -f2 || true
}

is_frontend_dev_process() {
  local cmd=$1
  [[ "$cmd" == *"${ROOT}"* && "$cmd" == *"next"* ]] \
    || [[ "$cmd" == *"${ROOT}/apps/frontend"* ]] \
    || [[ "$cmd" == *"next/dist/server/lib/start-server"* && "$cmd" == *"${ROOT}"* ]]
}

stop_pid_if_frontend_dev() {
  local pid=$1
  [[ -z "$pid" || "$pid" == "$$" ]] && return 1
  kill -0 "$pid" 2>/dev/null || return 1
  local cmd
  cmd="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  if is_frontend_dev_process "$cmd"; then
    echo "  停止宿主机 Next.js 进程 PID=${pid}"
    kill "$pid" 2>/dev/null || true
    return 0
  fi
  return 1
}

stopped=0

for pattern in \
  "${ROOT}/apps/frontend" \
  "${ROOT}/node_modules/.bun/next" \
  "${ROOT}/node_modules/next/dist/server/lib/start-server"; do
  while IFS= read -r pid; do
    if stop_pid_if_frontend_dev "$pid"; then
      stopped=1
    fi
  done < <(pgrep -f "$pattern" 2>/dev/null || true)
done

lock_pid="$(read_lock_pid)"
if [[ -n "${lock_pid:-}" ]] && stop_pid_if_frontend_dev "$lock_pid"; then
  stopped=1
fi

if [[ "$stopped" == 1 ]]; then
  sleep 1
fi

if [[ -f "$LOCK_FILE" ]]; then
  rm -f "$LOCK_FILE"
  echo "  已清除 Next.js dev lock"
fi

echo "✅ DevContainer 前端环境已就绪（映射端口 ${FRONTEND_PORT} → 容器 3000）"
