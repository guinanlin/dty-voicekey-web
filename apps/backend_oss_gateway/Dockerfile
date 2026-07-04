# 传声筒 - OSS Gateway（生产）
#
# 阿里云 ACR：
#   构建上下文目录: /apps/backend_oss_gateway
#   Dockerfile 文件名: Dockerfile
#
# 本地：docker build -t dty-oss:local .

FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY requirements.txt pyproject.toml ./
RUN uv venv .venv \
  && uv pip install --python .venv/bin/python -r requirements.txt alembic

COPY . .

ENV PATH="/app/.venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  PORT=8000

RUN chmod +x docker-entrypoint.sh \
  && mkdir -p storage

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
