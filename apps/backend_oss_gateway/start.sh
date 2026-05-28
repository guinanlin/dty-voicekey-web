#!/bin/bash
set -euo pipefail

echo "Current working directory: $(pwd)"
mkdir -p logs storage

if [ -f /.dockerenv ]; then
  echo "Running in Docker"
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-config=app/core/log_config.yml --reload
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running locally with uv"
  uv run uvicorn app.main:app --host 0.0.0.0 --port 8020 --log-config=app/core/log_config.yml --reload
fi
