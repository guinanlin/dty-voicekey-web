# 传声筒 - Next.js 前端（生产）
#
# 阿里云 ACR：
#   构建上下文目录: /apps/frontend
#   Dockerfile 文件名: Dockerfile
#
# 本地：docker build -t dty-frontend:local .
#
# 运行时环境变量：API_BASE_URL, PORT

FROM oven/bun:1.3-debian AS builder

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN bun --bun run build

FROM oven/bun:1.3-debian AS runner

WORKDIR /app

ENV NODE_ENV=production \
  NEXT_TELEMETRY_DISABLED=1 \
  PORT=3000 \
  HOSTNAME=0.0.0.0

COPY --from=builder --chown=bun:bun /app/public ./public
COPY --from=builder --chown=bun:bun /app/.next/standalone ./
COPY --from=builder --chown=bun:bun /app/.next/static ./.next/static
COPY --from=builder --chown=bun:bun /app/server.ts ./server.ts
COPY --from=builder --chown=bun:bun /app/node_modules/http-proxy ./node_modules/http-proxy
COPY --from=builder --chown=bun:bun /app/node_modules/eventemitter3 ./node_modules/eventemitter3
COPY --from=builder --chown=bun:bun /app/node_modules/follow-redirects ./node_modules/follow-redirects
COPY --from=builder --chown=bun:bun /app/node_modules/requires-port ./node_modules/requires-port

USER bun

EXPOSE 3000

CMD ["bun", "server.ts"]
