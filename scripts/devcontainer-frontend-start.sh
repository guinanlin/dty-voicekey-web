#!/bin/sh
# DevContainer frontend 容器内启动脚本
set -eu

ROOT="/workspaces/nextjs-fastapi-template"
cd "$ROOT/apps/frontend"

# 共享 volume 上可能残留宿主机 lock，容器启动时必须清除
rm -f .next/dev/lock

bun install --frozen-lockfile

# 固定监听容器内 3000，并通过 -H 0.0.0.0 暴露给端口映射
bun --bun run dev -- -p 3000 -H 0.0.0.0 &
bun watcher.js &
wait
