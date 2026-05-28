#!/usr/bin/env bash
# 确保 DevContainer compose 所需镜像在本地存在（支持 alias 到 compose 中使用的镜像名）。
set -euo pipefail

ensure_image() {
  local canonical=$1
  shift
  if docker image inspect "$canonical" >/dev/null 2>&1; then
    return 0
  fi
  for alt in "$@"; do
    if docker image inspect "$alt" >/dev/null 2>&1; then
      echo "📦 镜像别名: ${alt} -> ${canonical}"
      docker tag "$alt" "$canonical"
      return 0
    fi
  done
  echo "⬇️  拉取镜像: ${canonical}"
  docker pull "$canonical"
}

# 与 .devcontainer/docker-compose.yml 中 image / pull_policy: never 保持一致
ensure_image docker.m.daocloud.io/library/python:3.12-slim \
  python:3.12-slim \
  docker.io/library/python:3.12-slim

ensure_image oven/bun:1-alpine \
  oven/bun:1.2-alpine \
  oven/bun:1-alpine

ensure_image postgres:16-alpine \
  docker.m.daocloud.io/library/postgres:16-alpine \
  docker.m.daocloud.io/library/postgres:17-alpine \
  postgres:17-alpine

if ! docker image inspect mailhog/mailhog >/dev/null 2>&1; then
  echo "⬇️  拉取镜像: mailhog/mailhog"
  docker pull mailhog/mailhog
fi

echo "✅ DevContainer 基础镜像已就绪"
