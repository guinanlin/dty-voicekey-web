import uuid
from datetime import datetime, timezone

import pytest
from fastapi import status

from app.core.redis import redis_setex
from app.model.sms_model import SmsMessage


class TestSms:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_upload_and_list_sms(self, test_client, authenticated_user):
        payload = {
            "phone": "10086",
            "content": "您的话费余额为 50.00 元",
            "received_at": "2026-07-04T10:30:00+08:00",
        }
        upload_response = await test_client.post(
            "/sms/upload", json=payload, headers=authenticated_user["headers"]
        )
        assert upload_response.status_code == status.HTTP_200_OK
        sms_id = upload_response.json()["id"]

        list_response = await test_client.get(
            "/sms/", headers=authenticated_user["headers"]
        )
        assert list_response.status_code == status.HTTP_200_OK
        data = list_response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == sms_id
        assert data["items"][0]["phone"] == "10086"

    @pytest.mark.asyncio(loop_scope="function")
    async def test_search_sms(self, test_client, db_session, authenticated_user):
        sms = SmsMessage(
            user_id=authenticated_user["user"].id,
            phone="95588",
            content="消费 100.00 元",
            received_at=datetime.now(timezone.utc),
        )
        db_session.add(sms)
        await db_session.commit()

        response = await test_client.get(
            "/sms/?search=消费", headers=authenticated_user["headers"]
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 1

    @pytest.mark.asyncio(loop_scope="function")
    async def test_star_and_delete_sms(
        self, test_client, db_session, authenticated_user
    ):
        sms = SmsMessage(
            user_id=authenticated_user["user"].id,
            phone="10010",
            content="验证码 123456",
            received_at=datetime.now(timezone.utc),
        )
        db_session.add(sms)
        await db_session.commit()
        await db_session.refresh(sms)

        star_response = await test_client.patch(
            f"/sms/{sms.id}/star",
            json={"starred": True},
            headers=authenticated_user["headers"],
        )
        assert star_response.status_code == status.HTTP_200_OK

        delete_response = await test_client.delete(
            f"/sms/{sms.id}", headers=authenticated_user["headers"]
        )
        assert delete_response.status_code == status.HTTP_200_OK

        list_response = await test_client.get(
            "/sms/", headers=authenticated_user["headers"]
        )
        assert list_response.json()["total"] == 0

    @pytest.mark.asyncio(loop_scope="function")
    async def test_user_isolation(self, test_client, db_session, authenticated_user):
        from app.model.base_model import User
        from fastapi_users.password import PasswordHelper

        other_user = User(
            id=uuid.uuid4(),
            email="other@example.com",
            hashed_password=PasswordHelper().hash("TestPassword123#"),
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )
        db_session.add(other_user)
        await db_session.commit()

        sms = SmsMessage(
            user_id=other_user.id,
            phone="10086",
            content="other user message",
            received_at=datetime.now(timezone.utc),
        )
        db_session.add(sms)
        await db_session.commit()
        await db_session.refresh(sms)

        response = await test_client.get(
            f"/sms/{sms.id}", headers=authenticated_user["headers"]
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio(loop_scope="function")
    async def test_unauthorized_sms(self, test_client):
        response = await test_client.get("/sms/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio(loop_scope="function")
    async def test_phone_login(self, test_client):
        phone = "13800138000"
        await redis_setex(f"phone_code:{phone}", 300, "123456")

        response = await test_client.post(
            "/auth/login/phone",
            json={"phone": phone, "code": "123456"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
