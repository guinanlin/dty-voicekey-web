import hashlib
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import status


def _build_payload(forward_id: str, body: str, api_key: str = "test-webhook-key"):
    content_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    content_len = len(body.encode("utf-8"))
    ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    payload = {
        "id": forward_id,
        "event": "sms.received",
        "version": "1.0.0",
        "device": {
            "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "model": "Test",
            "manufacturer": "Test",
            "androidSdk": 34,
            "appVersion": "1.2.0",
        },
        "rule": {"id": 3, "name": "测试", "senderFilter": "10086"},
        "message": {
            "from": "10086",
            "body": body,
            "timestamp": ts,
            "subscriptionId": 1,
            "simSlot": 0,
            "partCount": 1,
        },
        "meta": {
            "receivedAt": ts,
            "sentAt": ts,
            "attempt": 1,
            "contentLength": content_len,
            "contentSha256": content_sha,
        },
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "User-Agent": "MeetingTranscription-Android/1.2.0 SmsForward/1.0.0",
        "X-Sms-Forward-Version": "1.0.0",
        "X-Sms-Forward-Message-Id": forward_id,
        "X-Sms-Forward-Device-Id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "X-Sms-Forward-Rule-Id": "3",
        "x-api-key": api_key,
    }
    return payload, headers


class TestSmsInbound:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_inbound_success(self, test_client, db_session, authenticated_user):
        user = authenticated_user["user"]
        user.webhook_api_key = "test-webhook-key"
        await db_session.commit()

        forward_id = str(uuid4())
        payload, headers = _build_payload(forward_id, "【测试】完整短信正文")

        response = await test_client.post(
            "/v1/sms/inbound", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ok"] is True
        assert data["code"] == "ACCEPTED"
        assert data["duplicate"] is False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_inbound_duplicate(self, test_client, db_session, authenticated_user):
        user = authenticated_user["user"]
        user.webhook_api_key = "test-webhook-key"
        await db_session.commit()

        forward_id = str(uuid4())
        payload, headers = _build_payload(forward_id, "幂等测试短信")

        r1 = await test_client.post("/v1/sms/inbound", json=payload, headers=headers)
        r2 = await test_client.post("/v1/sms/inbound", json=payload, headers=headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r2.json()["code"] == "DUPLICATE"
        assert r2.json()["duplicate"] is True

    @pytest.mark.asyncio(loop_scope="function")
    async def test_inbound_unauthorized(self, test_client):
        forward_id = str(uuid4())
        payload, headers = _build_payload(forward_id, "test")
        headers["x-api-key"] = "wrong-key"

        response = await test_client.post(
            "/v1/sms/inbound", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_inbound_health(self, test_client):
        response = await test_client.get("/v1/sms/health")
        assert response.status_code == 200
        assert response.json()["ok"] is True

    @pytest.mark.asyncio(loop_scope="function")
    async def test_inbound_empty_body(
        self, test_client, db_session, authenticated_user
    ):
        user = authenticated_user["user"]
        user.webhook_api_key = "test-webhook-key"
        await db_session.commit()

        forward_id = str(uuid4())
        payload, headers = _build_payload(forward_id, "   ")
        response = await test_client.post(
            "/v1/sms/inbound", json=payload, headers=headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["code"] == "UNPROCESSABLE"
