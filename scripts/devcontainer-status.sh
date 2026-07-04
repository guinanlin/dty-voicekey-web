#!/usr/bin/env bash
# 查看 Dev Container 各服务运行状态与宿主机端口映射
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.devcontainer/.env"

FRONTEND_PORT="${FRONTEND_PORT:-3600}"
BACKEND_PORT="${BACKEND_PORT:-8600}"
BACKEND_OSS_GATEWAY_PORT="${BACKEND_OSS_GATEWAY_PORT:-8610}"
POSTGRES_PORT="${POSTGRES_PORT:-5600}"
POSTGRES_TEST_PORT="${POSTGRES_TEST_PORT:-5610}"
MAILHOG_SMTP_PORT="${MAILHOG_SMTP_PORT:-8630}"
MAILHOG_UI_PORT="${MAILHOG_UI_PORT:-8650}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$ENV_FILE"
fi

COMPOSE_ENV=()
if [[ -f "$ENV_FILE" ]]; then
  COMPOSE_ENV=(--env-file "$ENV_FILE")
fi
COMPOSE=(docker compose "${COMPOSE_ENV[@]}" -f "$ROOT/.devcontainer/docker-compose.yml")

service_state() {
  local svc=$1
  local line
  line="$("${COMPOSE[@]}" ps "$svc" --format '{{.State}}' 2>/dev/null | head -1 || true)"
  if [[ -z "$line" ]]; then
    echo "未创建"
  else
    echo "$line"
  fi
}

port_listen() {
  local port=$1
  if ss -tln 2>/dev/null | grep -q ":${port} "; then
    echo "监听"
  else
    echo "未监听"
  fi
}

http_probe() {
  local url=$1
  local code
  if ! code="$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --connect-timeout 1 --max-time 2 "$url" 2>/dev/null)"; then
    echo "不可达"
    return
  fi
  if [[ "$code" == "000" || -z "$code" ]]; then
    echo "不可达"
  else
    echo "HTTP ${code}"
  fi
}

echo ""
echo "Dev Container 状态"
echo "  配置: ${ENV_FILE}"
echo "  命令: docker compose -f .devcontainer/docker-compose.yml"
echo ""

printf "%-12s %-14s %-22s %-26s %s\n" "服务" "容器状态" "端口 (宿主机→容器)" "宿主机监听" "快捷访问"
printf "%-12s %-14s %-22s %-26s %s\n" "------------" "--------------" "----------------------" "--------------------------" "----------"

declare -a rows=(
  "frontend|${FRONTEND_PORT}→3000|$(port_listen "$FRONTEND_PORT")|http://localhost:${FRONTEND_PORT}"
  "backend|${BACKEND_PORT}→8000|$(port_listen "$BACKEND_PORT")|http://localhost:${BACKEND_PORT}/docs"
  "oss|${BACKEND_OSS_GATEWAY_PORT}→8000|$(port_listen "$BACKEND_OSS_GATEWAY_PORT")|http://localhost:${BACKEND_OSS_GATEWAY_PORT}/docs"
  "db|${POSTGRES_PORT}→5432|$(port_listen "$POSTGRES_PORT")|postgresql://postgres:***@localhost:${POSTGRES_PORT}/mydatabase"
  "db_test|${POSTGRES_TEST_PORT}→5432|$(port_listen "$POSTGRES_TEST_PORT")|postgresql://postgres:***@localhost:${POSTGRES_TEST_PORT}/testdatabase"
  "mailhog|${MAILHOG_SMTP_PORT}→1025, ${MAILHOG_UI_PORT}→8025|$(port_listen "$MAILHOG_UI_PORT")|http://localhost:${MAILHOG_UI_PORT} (UI)"
  "workspace|—|—|make dc-sh"
)

for row in "${rows[@]}"; do
  IFS='|' read -r svc ports listen url <<< "$row"
  state="$(service_state "$svc")"
  printf "%-12s %-14s %-22s %-26s %s\n" "$svc" "$state" "$ports" "$listen" "$url"
done

echo ""
echo "HTTP 探测（仅 Web 服务）"
printf "  frontend  %s  →  %s\n" "http://localhost:${FRONTEND_PORT}/" "$(http_probe "http://127.0.0.1:${FRONTEND_PORT}/")"
printf "  backend   %s  →  %s\n" "http://localhost:${BACKEND_PORT}/docs" "$(http_probe "http://127.0.0.1:${BACKEND_PORT}/docs")"
printf "  oss_gw    %s  →  %s\n" "http://localhost:${BACKEND_OSS_GATEWAY_PORT}/api/v1/health" "$(http_probe "http://127.0.0.1:${BACKEND_OSS_GATEWAY_PORT}/api/v1/health")"
printf "  mailhog   %s  →  %s\n" "http://localhost:${MAILHOG_UI_PORT}/" "$(http_probe "http://127.0.0.1:${MAILHOG_UI_PORT}/")"

echo ""
echo "docker compose ps"
"${COMPOSE[@]}" ps 2>/dev/null || echo "  (无运行中的 compose 栈，可先执行 make dc)"
echo ""
