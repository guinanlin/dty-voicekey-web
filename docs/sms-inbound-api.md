# 传声筒 · 短信转发 Webhook 对接文档

**版本**：1.0.0  
**协议代号**：SmsForward-Webhook-v1  
**服务端实现版本**：2026-07-04  
**状态**：已实现

---

## 1. 概述

Android 设备（传声筒 App）收到短信后，向本服务配置的 **Webhook URL** 发起 HTTP POST，上报完整短信正文及元数据。服务端完成鉴权、幂等入库后，用户可在 Web 端 `/sms` 查看与管理。

### 1.1 与设备规范的对应关系

| 设备规范要求 | 本服务实现 | 说明 |
|-------------|-----------|------|
| POST Webhook URL | `POST /v1/sms/inbound` | App 配置完整 URL，如 `https://your-domain/v1/sms/inbound` |
| `x-api-key` 鉴权 | 支持 | 与用户账号 `webhook_api_key` 绑定 |
| 幂等键 `id` | 支持 | 存入 `forward_id`，重复投递返回 `DUPLICATE` |
| 完整 `message.body` | 支持 | 原样存储，不做截断或提取 |
| 约定 JSON 响应 | 支持 | `{ok, code, message, serverTime, duplicate}` |
| 健康检查 | `GET /v1/sms/health` | 可选，供 App「测试连接」使用 |
| 批量上报 | 不支持 | 仍保留 JWT 接口 `POST /sms/upload/batch` 供其他客户端 |

### 1.2 双通道说明

| 通道 | 路径 | 鉴权 | 适用场景 |
|------|------|------|----------|
| **设备 Webhook** | `POST /v1/sms/inbound` | `x-api-key` | Android 短信转发（本文档） |
| **Web / APP JWT** | `POST /sms/upload` | `Authorization: Bearer` | Web 管理端、已登录 APP |

---

## 2. 接入准备

### 2.1 获取 API Key

每个用户拥有独立的 Webhook API Key，短信入库到该用户账号下。

**开发环境默认 Key**（执行 `make dc-seed` 后生效）：

```
dev-sms-forward-key-change-in-production
```

绑定账号：`admin@dty.com`

**生产环境**：在环境变量或数据库中为用户设置 `webhook_api_key` 字段，并配置：

```env
SMS_FORWARD_REQUIRE_API_KEY=true
SMS_FORWARD_DEFAULT_API_KEY=your-production-key   # seed_admin 写入 admin 用户
```

### 2.2 App 端 Webhook URL 配置

在 App「短信端定义」中填写完整 URL，例如：

| 环境 | URL |
|------|-----|
| 本地开发 | `http://192.168.x.x:8600/v1/sms/inbound` |
| 生产 | `https://api.your-domain.com/v1/sms/inbound` |

> 客户端不会自动拼接路径，请包含 `/v1/sms/inbound`。

### 2.3 健康检查（可选）

```
GET /v1/sms/health
```

响应：

```json
{"ok": true, "service": "sms-forward-inbound"}
```

---

## 3. 接收短信 — POST /v1/sms/inbound

### 3.1 请求

```
POST /v1/sms/inbound
Content-Type: application/json; charset=utf-8
Accept: application/json
x-api-key: {your-api-key}
X-Sms-Forward-Version: 1.0.0
X-Sms-Forward-Message-Id: {与 body.id 相同}
X-Sms-Forward-Device-Id: {与 body.device.id 相同}
X-Sms-Forward-Rule-Id: {与 body.rule.id 相同，字符串}
User-Agent: MeetingTranscription-Android/{version} SmsForward/1.0.0
```

### 3.2 请求体

遵循设备端 **SmsForward-Webhook-v1** 规范，UTF-8 JSON 对象：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "sms.received",
  "version": "1.0.0",
  "device": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "model": "MI 13",
    "manufacturer": "Xiaomi",
    "androidSdk": 34,
    "appVersion": "1.2.0"
  },
  "rule": {
    "id": 3,
    "name": "工行通知",
    "senderFilter": "95588"
  },
  "message": {
    "from": "95588",
    "body": "【工商银行】您尾号1234的卡于07月04日收入人民币5,000.00元。",
    "timestamp": 1720051200000,
    "subscriptionId": 1,
    "simSlot": 0,
    "partCount": 1
  },
  "meta": {
    "receivedAt": 1720051200450,
    "sentAt": 1720051201080,
    "attempt": 1,
    "contentLength": 92,
    "contentSha256": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
  }
}
```

**字段映射（入库）**：

| 设备字段 | 服务端存储 |
|---------|-----------|
| `id` | `forward_id`（幂等键，唯一） |
| `message.from` | `phone` |
| `message.body` | `content`（完整正文） |
| `message.timestamp` | `received_at`（Unix 毫秒 → UTC） |
| `device.id` | `device_id` |
| `rule.id` | `rule_id` |
| `meta.contentSha256` | `content_sha256` |
| — | `source = "webhook"` |

### 3.3 服务端校验

| 校验项 | 失败响应 |
|--------|----------|
| 缺少/错误 `x-api-key` | `401 UNAUTHORIZED` |
| Header 与 Body ID 不一致 | `400 BAD_REQUEST` |
| `event` ≠ `sms.received` | `400 BAD_REQUEST` |
| `version` ≠ `1.0.0` | `400 BAD_REQUEST` |
| `message.body` 为空 | `422 UNPROCESSABLE` |
| `message.body` > 4000 字符 | `413 PAYLOAD_TOO_LARGE` |
| `contentSha256` / `contentLength` 不匹配 | `422 UNPROCESSABLE` |
| 超过限流（100 次/分钟/用户） | `429 RATE_LIMITED` |

---

## 4. 响应规范

### 4.1 首次成功 — HTTP 200

```json
{
  "ok": true,
  "code": "ACCEPTED",
  "message": "SMS received",
  "serverTime": 1720051202000,
  "duplicate": false
}
```

响应头（可选）：`X-Request-Id: {uuid}`

### 4.2 幂等重复 — HTTP 200

同一 `id` 再次 POST：

```json
{
  "ok": true,
  "code": "DUPLICATE",
  "message": "Message already processed",
  "serverTime": 1720051202000,
  "duplicate": true
}
```

### 4.3 错误响应

```json
{
  "ok": false,
  "code": "UNAUTHORIZED",
  "message": "Invalid x-api-key"
}
```

限流时额外字段：

```json
{
  "ok": false,
  "code": "RATE_LIMITED",
  "message": "Too many requests, retry later",
  "retryAfterMs": 60000
}
```

响应头：`Retry-After: 60`（秒）

### 4.4 错误码与 HTTP 状态

| code | HTTP | 客户端是否重试 |
|------|------|----------------|
| `ACCEPTED` | 200 | 否 |
| `DUPLICATE` | 200 | 否 |
| `BAD_REQUEST` | 400 | 否 |
| `UNAUTHORIZED` | 401 | 否 |
| `FORBIDDEN` | 403 | 否 |
| `PAYLOAD_TOO_LARGE` | 413 | 否 |
| `UNPROCESSABLE` | 422 | 否 |
| `RATE_LIMITED` | 429 | 是 |
| `INTERNAL_ERROR` | 500 | 是 |

---

## 5. curl 联调示例

```bash
API_KEY="dev-sms-forward-key-change-in-production"
MSG_ID="550e8400-e29b-41d4-a716-446655440000"
BODY="【测试】这是一条完整短信，不是提取后的验证码。"
SHA=$(echo -n "$BODY" | sha256sum | awk '{print $1}')
LEN=$(echo -n "$BODY" | wc -c | tr -d ' ')
TS=$(($(date +%s)*1000))

curl -X POST "http://localhost:8600/v1/sms/inbound" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "Accept: application/json" \
  -H "User-Agent: MeetingTranscription-Android/1.2.0 SmsForward/1.0.0" \
  -H "X-Sms-Forward-Version: 1.0.0" \
  -H "X-Sms-Forward-Message-Id: $MSG_ID" \
  -H "X-Sms-Forward-Device-Id: 7c9e6679-7425-40de-944b-e07fc1f90ae7" \
  -H "X-Sms-Forward-Rule-Id: 3" \
  -H "x-api-key: $API_KEY" \
  -d "{
    \"id\": \"$MSG_ID\",
    \"event\": \"sms.received\",
    \"version\": \"1.0.0\",
    \"device\": {
      \"id\": \"7c9e6679-7425-40de-944b-e07fc1f90ae7\",
      \"model\": \"Test\",
      \"manufacturer\": \"Test\",
      \"androidSdk\": 34,
      \"appVersion\": \"1.2.0\"
    },
    \"rule\": {\"id\": 3, \"name\": \"测试规则\", \"senderFilter\": \"10086\"},
    \"message\": {
      \"from\": \"10086\",
      \"body\": \"$BODY\",
      \"timestamp\": $TS,
      \"subscriptionId\": 1,
      \"simSlot\": 0,
      \"partCount\": 1
    },
    \"meta\": {
      \"receivedAt\": $TS,
      \"sentAt\": $TS,
      \"attempt\": 1,
      \"contentLength\": $LEN,
      \"contentSha256\": \"$SHA\"
    }
  }"
```

**验收**：登录 Web `http://localhost:3600/sms`，应能看到来自 `10086` 的测试短信。

---

## 6. 联调检查清单

- [ ] `GET /v1/sms/health` 返回 200
- [ ] 正确 API Key + 合法 Payload → `200 ACCEPTED`
- [ ] 相同 `id` POST 两次 → 第二次 `200 DUPLICATE`
- [ ] 错误 API Key → `401 UNAUTHORIZED`
- [ ] Web 端 `/sms` 可查看入库短信，正文与手机一致
- [ ] 生产环境使用 HTTPS

---

## 7. 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SMS_FORWARD_REQUIRE_API_KEY` | `true` | 是否强制要求 `x-api-key` |
| `SMS_FORWARD_DEFAULT_USER_EMAIL` | `admin@dty.com` | 未配 Key 时的兜底用户（仅 REQUIRE=false） |
| `SMS_FORWARD_DEFAULT_API_KEY` | `dev-sms-forward-key-...` | seed_admin 写入 admin 的 Key |

---

## 8. 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-04 | 1.0.0 | 初版：实现 SmsForward-Webhook-v1 接收端点 |
