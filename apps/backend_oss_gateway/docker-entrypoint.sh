#!/bin/sh
set -e

cd "$(dirname "$0")"
mkdir -p logs

if [ "${RUN_DB_MIGRATIONS:-1}" = "1" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --log-config=app/core/log_config.yml \
  --workers "${WEB_CONCURRENCY:-1}"
