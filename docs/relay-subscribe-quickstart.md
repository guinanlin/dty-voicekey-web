# 中继消息客户端订阅（简要）

发送走配对 WebSocket；订阅走登录 JWT。两条通道不要混用。

| | 发送 | 订阅 |
|---|---|---|
| 地址 | `/api/ws?pair={pair_token}` | `/api/relay/ws?token={jwt}` |
| 鉴权 | 工匠页二维码里的 `pair` | 登录拿到的 `access_token` |
| 方向 | 客户端发 `transmit` | 只收事件，不要发业务帧 |

以下用生产域名。本地把主机换成前端地址即可（如 `http://127.0.0.1:3601`，`ws://`）。

---

## 1. 登录拿 JWT

```http
POST https://voicekey.datangyuan.cn/auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=你的邮箱&password=你的密码
```

成功（200）：

```json
{
  "access_token": "eyJhbGciOiJI...",
  "token_type": "bearer"
}
```

失败示例：`400` `{"detail":"LOGIN_BAD_CREDENTIALS"}`。

curl：

```bash
curl -sS -X POST 'https://voicekey.datangyuan.cn/auth/jwt/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=你的邮箱' \
  --data-urlencode 'password=你的密码'
```

---

## 2. 连接订阅

```text
wss://voicekey.datangyuan.cn/api/relay/ws?token={access_token}
```

`token` 必须 `encodeURIComponent`。握手成功后**不用发任何消息**，等服务端推送。没有欢迎帧。

JWT 无效或过期会断开，关闭码 **4001**，重新登录再连。

```bash
TOKEN='上一步的 access_token'
npx -y wscat -c "wss://voicekey.datangyuan.cn/api/relay/ws?token=${TOKEN}"
```

浏览器：

```javascript
const token = "上一步的 access_token";
const ws = new WebSocket(
  `wss://voicekey.datangyuan.cn/api/relay/ws?token=${encodeURIComponent(token)}`,
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.message);
};

ws.onclose = (event) => {
  if (event.code === 4001) {
    console.error("JWT 无效或过期，请重新登录");
    return;
  }
  setTimeout(() => location.reload(), 3000); // 或自行重连
};
```

---

## 3. 推送事件

均为 JSON 文本帧：

```json
{ "type": "message_new", "message": { } }
{ "type": "message_updated", "message": { } }
```

| type | 何时 |
|------|------|
| `message_new` | 手机/发送端 `transmit` 入库后 |
| `message_updated` | 投递状态变更（PC ack / 离线等） |

`message` 主要字段：

| 字段 | 说明 |
|------|------|
| `id` | 消息 UUID，用它做 upsert |
| `pair_id` | 所属配对 |
| `text` | 正文 |
| `delivery_status` | `pending` / `delivered` / `failed` / `pc_offline` |
| `ack_ok` / `ack_error` | Agent 结果；未 ack 前多为 `null` |
| `created_at` | UTC 入库时间 |

只推送 **当前 JWT 对应用户** 名下的配对消息。

---

## 4. 建议

1. 历史列表目前走后端 REST（网页工匠页由 Server Action 代拉）。外部客户端若只要实时，连 WS 即可；需要全量可再对接 `GET /relay/messages`（Bearer JWT）。
2. WebSocket 只收增量；按 `message.id` 更新列表。
3. 软删除 **不会** 推事件。
4. 不必发心跳、不必发 `transmit`。
5. HTTPS 站点用 `wss://`；TLS 在网关终止即可。

发送端仍用配对地址，例如：

```text
wss://voicekey.datangyuan.cn/api/ws?pair=pt_xxx
```

```json
{ "type": "transmit", "text": "hello", "mode": "type" }
```

完整协议见 [relay-client-subscription.md](./relay-client-subscription.md)、[relay-api.md](./relay-api.md)。
