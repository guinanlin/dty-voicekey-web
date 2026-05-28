# China Cloud Storage Gateway (Template)

面向中国云生态的**统一对象存储网关模板**，供 monorepo 内主 `backend`（FastAPI）快速调用，屏蔽阿里云 OSS / 腾讯云 COS / 华为云 OBS / S3 / MinIO 等差异。

## 模板定位

- **是**：可二次开发的基础网关骨架，提供统一 HTTP API、Provider 插件化、PostgreSQL 元数据（`oss_*` 表前缀）
- **不是**：一次性做全功能 File Platform；MVP 不包含完整多租户策略、生命周期编排、OCR/AI Pipeline

## MVP 范围

| 包含 | 不包含（Phase 2+） |
|------|-------------------|
| presign / complete / download / delete | 分片上传、回调 webhook |
| Local + S3-compatible + OSS Provider | COS/OBS/R2 完整适配 |
| `oss_files` / `oss_file_references` | Redis 限流、outbox 事件 |
| 服务间鉴权 + trace_id | 完整 AI metadata |

## 架构原则

1. **Gateway 不做大文件中转**：默认 Browser/Client → 云存储直传
2. **Metadata 是核心**：对象在云，真相在 `oss_*` 表
3. **双后端边界**：仅本服务写 `oss_*`；主 `backend` 只通过 API/SDK 调用

## 快速启动（Dev Container）

```bash
make dc                  # 一键拉起全栈（含 backend_oss_gateway）
make dc-migrate-oss      # OSS 网关数据库迁移
make dc-status           # 查看各服务状态
```

- OSS Gateway: `http://localhost:${BACKEND_OSS_GATEWAY_PORT}/docs`（默认 8020）
- 主 Backend: `http://localhost:${BACKEND_PORT}/docs`

## Phase 路线图

- **Phase 1（当前）**：核心 API + Local/S3/OSS Provider + `oss_*` 表 + backend client
- **Phase 2**：分片上传、COS/OBS/R2、Redis、webhook、多租户增强
- **Phase 3**：OCR/Embedding 状态、AI Pipeline Hook
