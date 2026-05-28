#!/usr/bin/env bash
# 为 DevContainer 选择可用宿主机端口，写入 .devcontainer/.env
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.devcontainer/.env"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-dty-app-dev}"
LEGACY_COMPOSE_PROJECT="${LEGACY_COMPOSE_PROJECT:-nextjs-fastapi-template-dev}"

is_port_free() {
  local port=$1
  ! ss -tln 2>/dev/null | grep -q ":${port} "
}

port_used_by_compose() {
  local port=$1
  local project=$2
  docker ps --filter "label=com.docker.compose.project=${project}" \
    --format '{{.Ports}}' 2>/dev/null | grep -qE "0\.0\.0\.0:${port}->|127\.0\.0\.1:${port}->|\[::\]:${port}->"
}

port_available() {
  local port=$1
  is_port_free "$port" || port_used_by_compose "$port" "$COMPOSE_PROJECT"
}

is_reserved() {
  local port=$1
  shift
  local p
  for p in "$@"; do
    [[ "$p" == "$port" ]] && return 0
  done
  return 1
}

find_free_port() {
  local port=$1
  shift
  local reserved=("$@")
  while true; do
    if is_reserved "$port" "${reserved[@]}"; then
      port=$((port + 1))
      continue
    fi
    if port_available "$port"; then
      echo "$port"
      return 0
    fi
    port=$((port + 1))
    if (( port > 65530 )); then
      echo "❌ 无法找到可用端口（起始于 $1）" >&2
      exit 1
    fi
  done
}

load_env() {
  FRONTEND_PORT="${FRONTEND_PORT:-3010}"
  BACKEND_PORT="${BACKEND_PORT:-8010}"
  BACKEND_OSS_GATEWAY_PORT="${BACKEND_OSS_GATEWAY_PORT:-8020}"
  POSTGRES_PORT="${POSTGRES_PORT:-5442}"
  POSTGRES_TEST_PORT="${POSTGRES_TEST_PORT:-5443}"
  if [[ -f "$ENV_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
  fi
}

ports_unique() {
  local ports=("$FRONTEND_PORT" "$BACKEND_PORT" "$BACKEND_OSS_GATEWAY_PORT" "$POSTGRES_PORT" "$POSTGRES_TEST_PORT")
  local i j
  for ((i = 0; i < ${#ports[@]}; i++)); do
    for ((j = i + 1; j < ${#ports[@]}; j++)); do
      [[ "${ports[i]}" == "${ports[j]}" ]] && return 1
    done
  done
  return 0
}

ports_ok() {
  ports_unique \
    && port_available "$FRONTEND_PORT" \
    && port_available "$BACKEND_PORT" \
    && port_available "$BACKEND_OSS_GATEWAY_PORT" \
    && port_available "$POSTGRES_PORT" \
    && port_available "$POSTGRES_TEST_PORT"
}

write_env() {
  mkdir -p "$(dirname "$ENV_FILE")"
  cat >"$ENV_FILE" <<EOF
# 由 scripts/devcontainer-resolve-ports.sh 自动生成；宿主机端口映射
FRONTEND_PORT=${FRONTEND_PORT}
BACKEND_PORT=${BACKEND_PORT}
BACKEND_OSS_GATEWAY_PORT=${BACKEND_OSS_GATEWAY_PORT}
POSTGRES_PORT=${POSTGRES_PORT}
POSTGRES_TEST_PORT=${POSTGRES_TEST_PORT}
EOF
}

cleanup_legacy_stack() {
  if docker ps -a --filter "label=com.docker.compose.project=${LEGACY_COMPOSE_PROJECT}" -q | grep -q .; then
    echo "🧹 清理旧 stack: ${LEGACY_COMPOSE_PROJECT}"
    docker compose -p "$LEGACY_COMPOSE_PROJECT" -f "$ROOT/.devcontainer/docker-compose.yml" down 2>/dev/null || \
      docker ps -aq --filter "label=com.docker.compose.project=${LEGACY_COMPOSE_PROJECT}" | xargs -r docker rm -f
  fi
}

load_env
cleanup_legacy_stack

if [[ -f "$ENV_FILE" ]] && ports_ok; then
  echo "✅ 使用已有端口: frontend=${FRONTEND_PORT} backend=${BACKEND_PORT} oss_gateway=${BACKEND_OSS_GATEWAY_PORT} postgres=${POSTGRES_PORT} test=${POSTGRES_TEST_PORT}"
else
  FRONTEND_PORT="$(find_free_port "${FRONTEND_PORT:-3010}")"
  BACKEND_PORT="$(find_free_port "${BACKEND_PORT:-8010}" "$FRONTEND_PORT")"
  BACKEND_OSS_GATEWAY_PORT="$(find_free_port "${BACKEND_OSS_GATEWAY_PORT:-8020}" "$FRONTEND_PORT" "$BACKEND_PORT")"
  POSTGRES_PORT="$(find_free_port "${POSTGRES_PORT:-5442}" "$FRONTEND_PORT" "$BACKEND_PORT" "$BACKEND_OSS_GATEWAY_PORT")"
  POSTGRES_TEST_PORT="$(find_free_port "${POSTGRES_TEST_PORT:-5443}" "$FRONTEND_PORT" "$BACKEND_PORT" "$BACKEND_OSS_GATEWAY_PORT" "$POSTGRES_PORT")"
  write_env
  echo "✅ 已分配端口: frontend=${FRONTEND_PORT} backend=${BACKEND_PORT} oss_gateway=${BACKEND_OSS_GATEWAY_PORT} postgres=${POSTGRES_PORT} test=${POSTGRES_TEST_PORT}"
fi
