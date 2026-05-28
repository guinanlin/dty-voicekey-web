FROM oven/bun:1.2-debian

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .
RUN bun --bun run build

RUN chmod +x ./start.prod.sh

USER bun

EXPOSE 3000

CMD ["sh", "-c", "bun --bun run start & bun watcher.js & wait"]
