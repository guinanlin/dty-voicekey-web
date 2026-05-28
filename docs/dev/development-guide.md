# 开发指南

本文档面向日常开发：环境搭建、本地运行、常见工作流与排错。部署与 CI 说明见仓库根目录 [README.md](../../README.md)。

## 技术栈

| 层级 | 技术 | 包管理 |
|------|------|--------|
| 前端 | Next.js、React、Tailwind CSS | Bun |
| 后端 | Python、FastAPI、SQLAlchemy | uv |
| 数据库 | PostgreSQL | Docker / Dev Container |
| API 契约 | OpenAPI → 自动生成 TS 客户端 | `@hey-api/openapi-ts` |

## 仓库结构（Monorepo）

```
nextjs-fastapi-template/
├── apps/
│   ├── backend/          # FastAPI 应用
│   ├── backend_oss_gateway/  # OSS 存储网关（oss_* 表归属此服务）
│   └── frontend/         # Next.js 应用
├── packages/             # 共享库（ts / py / contracts）
├── shared-data/          # 运行时共享产物（如 openapi.json）
├── docker/               # 生产/本地 Docker Compose
├── .devcontainer/        # VS Code / Cursor Dev Container
├── docs/dev/             # 开发文档（本目录）
├── pyproject.toml        # uv workspace 根
├── package.json          # Bun workspace 根
├── uv.lock / bun.lock    # 锁文件（在根目录维护）
└── Makefile              # 常用开发命令
```

扩展共享代码时，优先阅读 [packages/README.md](../../packages/README.md)。

## 环境要求

- **Python** 3.12（后端）
- **uv**：[安装说明](https://docs.astral.sh/uv/getting-started/installation/)
- **Bun**：[安装说明](https://bun.sh/docs/installation)
- **Docker & Docker Compose**（推荐，用于数据库 / MailHog / 可选的全栈容器）
- **Node 相关**：由 Bun 处理，无需单独安装 npm

## 首次搭建

### 1. 克隆并安装依赖

在**仓库根目录**执行：

```bash
make sync-deps
```

等价于 `uv sync` + `bun install`。锁文件为根目录的 `uv.lock`、`bun.lock`。

### 2. 配置环境变量

**后端** `apps/backend/.env`：

```bash
cp apps/backend/.env.example apps/backend/.env
```

至少替换三个密钥（可用 `python3 -c "import secrets; print(secrets.token_hex(32))"` 生成）：

- `ACCESS_SECRET_KEY`
- `RESET_PASSWORD_SECRET_KEY`
- `VERIFICATION_SECRET_KEY`

本地数据库、邮件、CORS 等默认值见 `.env.example`。

**前端** `apps/frontend/.env.local`：

```bash
cp apps/frontend/.env.example apps/frontend/.env.local
```

通常保持 `API_BASE_URL=http://localhost:8000` 即可。

### 3. 启动数据库并迁移

```bash
docker compose -f docker/docker-compose.yml up -d db
make docker-migrate-db
```

可选：创建开发管理员账号：

```bash
make seed-admin
# 默认：admin@dty.com / admin123（可在 .env 中覆盖）
```

### 4. 启动应用

两个终端分别执行：

```bash
make start-backend   # http://localhost:8000 ，API 文档 /docs
make start-frontend  # http://localhost:3000
```

## 日常开发

### 热重载

- **后端**：`watcher.py` 监视 `app/` 下路由与 schema 变更，并触发 OpenAPI 生成。
- **前端**：`watcher.js` 监视 `openapi.json`，自动执行 `bun run generate-client`。

手动同步 API 客户端：

```bash
cd apps/backend && uv run python -m commands.generate_openapi_schema
cd apps/frontend && bun run generate-client
```

或使用脚本：

```bash
bash apps/backend/scripts/generate-frontapi.sh
```

生成后的类型与 SDK：

- `apps/frontend/app/openapi-client/sdk.gen.ts`
- `apps/frontend/app/openapi-client/types.gen.ts`

业务侧通过 `@/app/clientService` 调用，示例见 `.cursor/rules/600-how-call-api-from-frontend.mdc`。

### 后端常见路径

| 路径 | 说明 |
|------|------|
| `apps/backend/app/main.py` | FastAPI 入口 |
| `apps/backend/app/routes/` | 路由 |
| `apps/backend/app/model/` | SQLAlchemy 模型 |
| `apps/backend/app/service/` | 业务逻辑（按需新增） |
| `apps/backend/alembic_migrations/versions/` | 数据库迁移 |

### 前端常见路径

| 路径 | 说明 |
|------|------|
| `apps/frontend/app/` | Next.js App Router 页面 |
| `apps/frontend/components/` | UI 与 Server Actions |
| `apps/frontend/lib/` | 工具与校验（如 zod schema） |

TypeScript 基础配置继承自 workspace 包 `@dty/tsconfig`（`packages/ts/tsconfig/`）。

## Dev Container（推荐）

使用 Cursor / VS Code 的 **Reopen in Container** 或：

```bash
make dc          # 一键启动：DB + MailHog + backend + frontend
make dc-migrate  # 容器内迁移
make dc-seed     # 容器内种子管理员
make dc-logs     # 查看日志，如 make dc-logs s=backend
make dc-sh       # 进入 workspace shell
make dcd         # 停止并清理
```

默认端口（见 `.devcontainer/.env`，可由 `make dc-env` 自动分配）：

| 服务 | 默认端口 |
|------|----------|
| Next.js | 3010 |
| FastAPI | 8010 |
| OSS Gateway | 8020 |
| Postgres（主库） | 5442 |
| Postgres（测试库） | 5443 |
| MailHog UI | 8025 |

容器内前端访问后端使用 `http://backend:8000`；浏览器访问使用转发后的 localhost 端口。

## 数据库迁移（Alembic）

本地（需数据库已运行）：

```bash
cd apps/backend
uv run alembic current
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

Docker：

```bash
make docker-migrate-db
make docker-db-schema migration_name="add users table"
```

## 测试

先启动测试库：

```bash
make docker-up-test-db
```

本地执行：

```bash
make test-backend
make test-frontend
```

Docker 内执行：

```bash
make docker-test-backend
make docker-test-frontend
```

## 代码质量

安装 pre-commit（在已 `uv sync` 的后端环境中）：

```bash
pre-commit install -c .pre-commit-config.yaml
pre-commit run --all-files -c .pre-commit-config.yaml
```

钩子包括：Ruff（Python）、ESLint / Prettier / tsc（前端）、OpenAPI 与客户端生成等。

## Makefile 速查

```bash
make help              # 列出所有命令
make sync-deps         # 根目录安装 uv + bun 依赖
make start-backend     # 本地启动 FastAPI
make start-frontend    # 本地启动 Next.js
make test-backend      # pytest
make test-frontend     # jest
make docker-migrate-db # Docker 内迁移
make dc                # Dev Container 全栈
make dc-migrate-oss    # OSS Gateway 迁移
```

完整列表以 `Makefile` 为准。

## OSS Gateway

主 `backend` 通过 `app/integrations/storage_gateway_client.py` 调用网关，禁止直写 `oss_*` 表或直接 import 云厂商 SDK。详见 [apps/backend_oss_gateway/README.md](../../apps/backend_oss_gateway/README.md)。

## 常见问题

### 根目录出现空的 `frontend/` 文件夹

多为迁移前在旧路径运行过 `next dev`，遗留未纳入 Git 的 `.next` 缓存。删除该目录即可；请在 `apps/frontend` 下开发。

### `bun install` 应该在哪执行？

在**仓库根目录**。不要在 `apps/frontend` 单独维护 `bun.lock`。

### Python 虚拟环境用哪个？

- 本地开发：`apps/backend` 下 `uv run ...` 即可（workspace 会解析依赖）。
- Dev Container：compose 挂载 `apps/backend/.venv`。
- 根目录 `.venv` 为 uv workspace 根环境，属正常现象。

### OpenAPI 未更新导致前端类型报错

按顺序执行：生成 schema → `bun run generate-client`，或重启带 watcher 的开发服务。

### 端口被占用（Dev Container）

```bash
make dc-env    # 重新分配端口到 .devcontainer/.env
make dc-rebuild
```

## 相关文档

- [README.md](../../README.md) — 项目总览、部署、CI
- [packages/README.md](../../packages/README.md) — 共享包与 workspace
- `.cursor/rules/` — AI / 团队编码约定（结构、Service、迁移、前端 API 等）
