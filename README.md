[![CI](https://github.com/vintasoftware/nextjs-fastapi-template/actions/workflows/ci.yml/badge.svg)](https://github.com/vintasoftware/nextjs-fastapi-template/actions/workflows/ci.yml)

# nextjs-fastapi-template

基于 **Monorepo** 的全栈模板：FastAPI 后端 + Next.js 前端 + **OSS Gateway 对象存储网关**，OpenAPI 驱动类型安全客户端，内置认证与基础仪表板。

| 层级 | 技术 | 工具 |
|------|------|------|
| 前端 | Next.js、React、Tailwind、shadcn/ui | Bun |
| 后端 | FastAPI、SQLAlchemy、Pydantic、fastapi-users | uv |
| 存储网关 | FastAPI、Provider 插件（Local / S3 / 阿里云 OSS） | uv |
| 数据 | PostgreSQL（`oss_*` 表由网关维护） | Docker |
| 契约 | OpenAPI → `@hey-api/openapi-ts` | 热重载 watcher |

## 项目结构

```
nextjs-fastapi-template/
├── apps/
│   ├── backend/              # FastAPI 业务后端
│   ├── backend_oss_gateway/  # 统一对象存储网关（oss_* 表归属此服务）
│   └── frontend/             # Next.js
├── packages/          # 共享库（ts / py / contracts）
├── shared-data/       # 共享产物（如 openapi.json）
├── .devcontainer/     # Dev Container 编排（推荐）
├── docker/            # 独立 Docker Compose（数据库等）
├── docs/dev/          # 详细开发指南
├── pyproject.toml     # uv workspace 根
├── package.json       # Bun workspace 根
└── Makefile           # 常用命令（make help）
```

共享包说明见 [packages/README.md](packages/README.md)。

## 快速开始

### 方式一：Dev Container（推荐）

需要 Docker、Docker Compose，以及 Cursor / VS Code 的 Dev Containers 扩展。

```bash
make dc              # 启动 DB + MailHog + backend + oss gateway + frontend
make dc-migrate      # 主 backend 数据库迁移
make dc-migrate-oss  # OSS Gateway 数据库迁移（oss_* 表）
make dc-seed         # 种子管理员 admin@dty.com / admin123
# 浏览器打开 http://localhost:3600/dashboard 可体验文件上传 Demo
```

宿主机默认端口见 `.devcontainer/.env`（一般为 Next.js `3600`、FastAPI `8600`、OSS Gateway `8610`、MailHog UI `8650`）。

### 方式二：本地开发

**环境**：Python 3.12、[uv](https://docs.astral.sh/uv/getting-started/installation/)、[Bun](https://bun.sh/docs/installation)、Docker（用于数据库）。

```bash
# 1. 依赖（仓库根目录）
make sync-deps

# 2. 环境变量
cp apps/backend/.env.example apps/backend/.env
cp apps/backend_oss_gateway/.env.example apps/backend_oss_gateway/.env
cp apps/frontend/.env.example apps/frontend/.env.local
# 至少替换 backend/.env 中的三个 SECRET_KEY
# backend 与 oss gateway 的 SERVICE_TOKEN 需一致（见下方 OSS Gateway 章节）

# 3. 数据库（任选其一）
make dc                    # 用 Dev Container 自带 DB
# 或 docker compose -f docker/docker-compose.yml up -d db

# 4. 迁移与种子（本地需已配置 DATABASE_URL）
cd apps/backend && uv run alembic upgrade head
cd ../backend_oss_gateway && uv run alembic upgrade head
make seed-admin

# 5. 启动（三个终端）
make start-backend
make start-backend-oss-gateway
make start-frontend
```

本地端口以后端 `start.sh` 与 Next.js 输出为准；前端 `API_BASE_URL` 需与后端一致。

## 常用命令

```bash
make help            # 全部命令
make sync-deps       # uv sync + bun install（根目录）
make start-backend            # FastAPI + 热重载
make start-backend-oss-gateway # OSS Gateway + 热重载
make start-frontend           # Next.js + OpenAPI 客户端 watcher
make test-backend             # pytest
make test-backend-oss-gateway # OSS Gateway pytest
make test-frontend            # jest
make seed-admin      # 本地创建管理员

# Dev Container
make dc / make dcd   # 启动 / 停止并清理
make dc-status       # 查看各服务状态与端口映射（含 OSS Gateway）
make dc-migrate      # 容器内主 backend 迁移
make dc-migrate-oss  # 容器内 OSS Gateway 迁移
make dc-seed         # 容器内种子用户
make dc-logs s=backend
make dc-sh           # 进入 workspace shell
```

## OSS Gateway（对象存储网关）

`apps/backend_oss_gateway` 是统一对象存储网关模板，屏蔽 Local / S3 / MinIO / 阿里云 OSS 等差异。主 `backend` **只通过 HTTP 调用网关**，禁止在业务代码中直接 import 云厂商 SDK 或写入 `oss_*` 表。

详细网关文档见 [apps/backend_oss_gateway/README.md](apps/backend_oss_gateway/README.md)。

### 架构：模式 C（BFF / 编排）

前端**只请求 Core Backend**；文件上传的 presign、落库、complete 由 Core 内部编排 OSS Gateway 完成：

```
浏览器 → Core Backend (/files/upload)
           ├─ presign  → OSS Gateway
           ├─ 内网上传  → OSS Gateway（Local Provider 等）
           ├─ complete → OSS Gateway → PostgreSQL (oss_*)
           └─ 返回 file_id + download_url → 浏览器
```

| 服务 | 职责 | 默认端口（Dev Container） |
|------|------|---------------------------|
| `apps/frontend` | UI、Server Action，只调 Core | 3600 |
| `apps/backend` | 认证、业务 API、存储编排 | 8600 |
| `apps/backend_oss_gateway` | 对象存储 API、Provider、`oss_*` 元数据 | 8610 |

### 双后端数据库边界

Core 与 Gateway **共用同一 PostgreSQL 实例**，但迁移与表归属分离：

| 项目 | Core Backend | OSS Gateway |
|------|--------------|-------------|
| 业务表 | `user`、`item` 等 | — |
| 存储元数据 | 禁止直写 | `oss_files`、`oss_file_references` |
| Alembic 版本表 | `alembic_version` | `alembic_version_oss` |
| 迁移目录 | `apps/backend/alembic_migrations` | `apps/backend_oss_gateway/alembic_migrations` |

首次启动后务必执行：

```bash
make dc-migrate      # Core 表
make dc-migrate-oss  # oss_* 表
```

### 文件上传 Demo

登录 Dashboard（`http://localhost:3600/dashboard`，种子用户 `admin@dty.com` / `admin123`）后，页面内有 **「文件上传 Demo」** 区块，可走通完整链路。

Dev Container 默认使用 **Local Provider**（文件落在 `apps/backend_oss_gateway/storage/`），无需配置云密钥。

### 关键代码位置

| 路径 | 说明 |
|------|------|
| `apps/backend/app/integrations/storage_gateway_client.py` | Core → Gateway HTTP 客户端 |
| `apps/backend/app/service/file_service.py` | 上传编排（presign / 代理上传 / complete） |
| `apps/backend/app/routes/files.py` | `POST /files/upload`、`GET /files/{id}/download` |
| `apps/frontend/app/dashboard/fileUploadDemo.tsx` | Dashboard 上传 Demo UI |
| `apps/frontend/components/actions/files-action.ts` | Server Action（只调 Core） |
| `apps/backend_oss_gateway/app/providers/` | Local / S3 / OSS Provider 实现 |

### 环境变量

**Core Backend**（`apps/backend/.env`）：

```env
OSS_GATEWAY_BASE_URL=http://localhost:8610
OSS_GATEWAY_SERVICE_TOKEN=dev-service-token-change-in-production
```

**OSS Gateway**（`apps/backend_oss_gateway/.env`）：

```env
SERVICE_TOKENS=dev-service-token-change-in-production   # 与 Core 的 TOKEN 一致
DEFAULT_PROVIDER=local                                  # 本地开发默认 local
LOCAL_STORAGE_PATH=./storage
LOCAL_PUBLIC_BASE_URL=http://localhost:8610             # 浏览器下载链接前缀
```

生产环境将 `DEFAULT_PROVIDER` 改为 `s3` 或 `oss`，并填写对应云厂商密钥（见 `apps/backend_oss_gateway/.env.example`）。

### MIME 类型

multipart 上传时，部分客户端会把 Excel 等文件标成 `text/plain`。Core 在 `app/utils.py` 的 `resolve_mime_type()` 中会根据**文件扩展名**校正（如 `.xlsx` → `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`），再写入 `oss_files.mime_type`。

## 功能概览

- JWT 认证、邮箱找回密码、预置仪表板
- **OSS Gateway 模板**：模式 C 文件上传 Demo（Dashboard）
- 后端/前端热重载；OpenAPI schema 变更自动同步 TS 客户端
- MailHog 本地邮件（Dev Container 内已集成）
- CI：`.github/workflows/`（测试、pre-commit、生产部署 workflow）

更细的流程（迁移、测试、pre-commit、排错）见 **[docs/dev/development-guide.md](docs/dev/development-guide.md)**。

## 从模板创建项目

1. 使用 GitHub **Use this template** 创建新仓库并克隆
2. 修改本 README 标题与项目名
3. 按上文完成 `make sync-deps` 与环境配置

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

基于 [Vinta Software nextjs-fastapi-template](https://github.com/vintasoftware/nextjs-fastapi-template) 演进；Monorepo 与 Dev Container 工作流已按当前仓库结构调整。
