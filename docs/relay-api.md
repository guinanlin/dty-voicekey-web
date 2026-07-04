# 传声筒 · 云端中继 API 对接文档

**版本**：1.0.0  
**状态**：已实现  
**关联**：本仓库 FastAPI Relay Hub + Next.js 工匠页

---

## 1. 概述

云端中继（Relay Hub）允许手机或外部客户端通过公网 WebSocket 向 PC Agent 转发 `transmit` 消息，同时将消息入库供 Web 端「工匠」页查看。

**当前阶段传输协议**：允许 `ws://`（`RELAY_REQUIRE_WSS=false`，默认）。待公网 TLS 就绪后切换为 `wss://` 并开启强制校验。

---

## 2. 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RELAY_PUBLIC_WS_URL` | `ws://localhost:8600/ws` | 二维码与文档中的 WS 基址 |
| `RELAY_REQUIRE_WSS` | `false` | 为 `true` 时拒绝非 wss 连接（延后启用） |
| `RELAY_PAIR_TOKEN_TTL_DAYS` | `0`（不过期） | `0` 表示长期有效；大于 0 时按天数过期 |
| `RELAY_MAX_PHONES_PER_PAIR` | `3` | 单配对允许的手机连接数（预留） |
| `RELAY_TRANSMIT_RATE_LIMIT` | `10` | 每分钟每 pair 转发上限 |

---

## 3. REST API（JWT 鉴权）

Base URL 示例：`http://localhost:8600`

### 3.1 健康检查

```
GET /api/v1/health
```

响应：

```json
{ "status": "ok", "ws_connections": 0 }
```

### 3.2 创建配对

```
POST /api/v1/pairs
Authorization: Bearer {jwt}
Content-Type: application/json

{ "device_name": "MacBook-Pro" }
```

响应：

```json
{
  "pair_id": "pair_abc123",
  "pair_token": "pt_xxx",
  "agent_token": "at_xxx",
  "relay_ws_url": "ws://localhost:8600/ws",
  "relay_agent_url": "ws://localhost:8600/agent",
  "expires_at": "2026-07-11T12:00:00Z",
  "qr_payload": {
    "v": 1,
    "mode": "relay",
    "ws": "ws://localhost:8600/ws",
    "pair": "pt_xxx"
  }
}
```

### 3.3 其他配对接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/pairs` | 列表 |
| GET | `/api/v1/pairs/{pair_id}/status` | 在线状态 |
| POST | `/api/v1/pairs/{pair_id}/refresh-token` | 刷新 pair_token |
| DELETE | `/api/v1/pairs/{pair_id}` | 吊销并断开 WS |

### 3.4 中继消息管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/relay/messages?page=1&page_size=20&search=&sort=newest` | 分页列表 |
| GET | `/relay/messages/stats` | 统计 |
| GET | `/relay/messages/{id}` | 详情 |
| DELETE | `/relay/messages/{id}` | 软删除 |

---

## 4. WebSocket 协议

### 4.1 端点

| 端点 | 连接方 | 示例 |
|------|--------|------|
| `/ws?pair={pair_token}` | 手机 / 发送端 | `ws://host:8600/ws?pair=pt_xxx` |
| `/agent?pair_id={id}&agent_token={token}` | PC Agent | `ws://host:8600/agent?pair_id=pair_xxx&agent_token=at_xxx` |
| `/relay/ws?token={jwt}` | Client 订阅端 | `ws://host:8600/relay/ws?token=eyJ...` |

> Client 订阅端完整对接说明见 **[relay-client-subscription.md](./relay-client-subscription.md)**（事件协议、消息结构、示例代码）。

Web 端连接后无需发送心跳帧；服务端在消息入库或 ack 更新时推送：

```json
{ "type": "message_new", "message": { /* RelayMessageRead */ } }
{ "type": "message_updated", "message": { /* RelayMessageRead */ } }
```

`token` 为登录 JWT（与 REST `Authorization: Bearer` 相同）。

### 4.2 应用层消息（与 PC 直连协议一致）

**手机 → 中继 → PC（透传）**

```json
{
  "type": "transmit",
  "text": "用户输入的内容",
  "mode": "type",
  "after_key": "enter",
  "smart_mode": false,
  "smart_action": null
}
```

**PC / 中继 → 手机**

```json
{ "type": "connected" }
```

```json
{ "type": "ack", "ok": true }
```

```json
{ "type": "ack", "ok": false, "error": "PC 离线" }
```

```json
{ "type": "pc_status", "online": false }
```

### 4.3 行为说明

- 手机连接后，若 PC Agent 在线则收到 `connected`；否则收到 `pc_status: offline`
- 每条 `transmit` **先入库**再转发；PC 离线时仍可在 Web「工匠」页查看
- PC 离线时手机立即收到 `ack: false, error: "PC 离线"`

---

## 5. 二维码格式

Web 工匠页生成的二维码内容为 JSON 字符串：

```json
{
  "v": 1,
  "mode": "relay",
  "ws": "ws://your-host:8600/ws",
  "pair": "pt_xxx"
}
```

安卓解析后连接：`{ws}?pair={pair}`

---

## 6. 联调示例（wscat）

```bash
# 1. 登录 Web 创建配对，获得 pair_token / agent_token / pair_id

# 2. 模拟 PC Agent
wscat -c "ws://localhost:8600/agent?pair_id=pair_xxx&agent_token=at_xxx"

# 3. 模拟手机
wscat -c "ws://localhost:8600/ws?pair=pt_xxx"
> {"type":"transmit","text":"hello relay","mode":"type"}

# 4. Web 工匠页 /craftsman 查看入库消息
```

---

## 7. 生产部署（ws 直连，暂不含 WSS）

### 7.1 约束

- **Vercel Serverless 不支持 WebSocket 长连接**；Relay 需容器常驻部署（Docker / Dokploy）
- REST API 可暂留 Vercel；WS 与 REST 建议同域反代或统一容器

### 7.2 Docker Compose 示例

后端容器已包含 Relay Hub，确保：

```yaml
environment:
  RELAY_PUBLIC_WS_URL: ws://your-public-host:8600/ws
  RELAY_REQUIRE_WSS: "false"
```

### 7.3 Dokploy 部署要点

1. 部署 `apps/backend` 为常驻服务（非 serverless）
2. 暴露 `8600` 或经 Caddy/Nginx 反代 HTTP Upgrade
3. 设置 `RELAY_PUBLIC_WS_URL` 为手机可访问的 `ws://` 地址
4. 执行 `alembic upgrade head` 创建 `relay_pairs` / `relay_messages` 表

### 7.4 WSS 升级（延后）

公网证书就绪后：

1. 配置 TLS 终止（Caddy / Nginx）
2. `RELAY_PUBLIC_WS_URL` 改为 `wss://...`
3. `RELAY_REQUIRE_WSS=true`

---

## 8. 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-04 | 1.0.0 | 初版：Relay Hub + 工匠页 + ws 明文阶段 |
| 2026-07-04 | 1.0.1 | 新增 Client 订阅端 `/relay/ws`；详见 relay-client-subscription.md |
