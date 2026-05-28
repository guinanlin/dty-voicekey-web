# dty-common

Python 共享库占位包。多 FastAPI 服务或 worker 需要复用逻辑时，在此添加模块。

在 `apps/backend/pyproject.toml` 中按需添加依赖：

```toml
dependencies = [
    "dty-common",
]
```

然后于仓库根目录执行 `uv sync`。
