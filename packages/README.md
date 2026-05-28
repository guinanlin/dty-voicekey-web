# packages/

可复用库与跨应用契约，按语言/用途分子目录。

| 目录 | 用途 |
|------|------|
| `ts/` | TypeScript 共享包（Bun workspace） |
| `py/` | Python 共享包（uv workspace） |
| `contracts/` | 跨语言契约（OpenAPI 等），与 `shared-data/` 互补 |

## 使用

依赖锁文件在**仓库根目录**：`uv.lock`、`bun.lock`（已从 `apps/*` 收口，请在根目录安装）。

```bash
make sync-deps   # 或分别执行 uv sync && bun install
```

也可在任意 workspace 成员目录执行 `uv sync`；`bun install` 请在根目录执行。

## 何时往这里加代码

- 第二个 Next 应用需要共用 UI → `packages/ts/ui`
- 第二个 FastAPI/Worker 需要共用 DB/工具 → `packages/py/common` 或 `packages/py/db`
- 需要锁定 API 契约版本 → `packages/contracts/openapi`

业务逻辑仍优先放在 `apps/*`，确认有第二个消费者后再抽取到 `packages/`。
