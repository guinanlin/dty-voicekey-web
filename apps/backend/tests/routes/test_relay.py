import pytest
from httpx import AsyncClient

from app.service import relay_message_service, relay_pair_service
from app.ws.connection_manager import relay_manager


@pytest.mark.asyncio
async def test_relay_health(test_client: AsyncClient):
    response = await test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ws_connections" in data


@pytest.mark.asyncio
async def test_create_and_list_pairs(test_client: AsyncClient, authenticated_user):
    headers = authenticated_user["headers"]

    create_resp = await test_client.post(
        "/api/v1/pairs",
        headers=headers,
        json={"device_name": "Test Device"},
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["pair_id"].startswith("pair_")
    assert created["pair_token"].startswith("pt_")
    assert created["agent_token"].startswith("at_")
    assert created["qr_payload"]["mode"] == "relay"
    assert created["qr_payload"]["pair"] == created["pair_token"]

    list_resp = await test_client.get("/api/v1/pairs", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["pair_id"] == created["pair_id"]
    assert items[0]["pc_online"] is False


@pytest.mark.asyncio
async def test_pair_status_and_revoke(test_client: AsyncClient, authenticated_user):
    headers = authenticated_user["headers"]
    create_resp = await test_client.post(
        "/api/v1/pairs", headers=headers, json={"device_name": "Revoke Test"}
    )
    pair_id = create_resp.json()["pair_id"]

    status_resp = await test_client.get(
        f"/api/v1/pairs/{pair_id}/status", headers=headers
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["pc_online"] is False

    delete_resp = await test_client.delete(f"/api/v1/pairs/{pair_id}", headers=headers)
    assert delete_resp.status_code == 204

    list_resp = await test_client.get("/api/v1/pairs", headers=headers)
    assert list_resp.json()["items"] == []


@pytest.mark.asyncio
async def test_relay_message_list_empty(test_client: AsyncClient, authenticated_user):
    headers = authenticated_user["headers"]
    response = await test_client.get("/relay/messages", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_transmit_persisted_when_pc_offline(
    test_client: AsyncClient, authenticated_user, db_session
):
    user = authenticated_user["user"]
    headers = authenticated_user["headers"]

    pair, _, _ = await relay_pair_service.create_pair(
        db_session, user.id, "Offline Persist"
    )

    await relay_message_service.create_relay_message(
        db_session,
        user_id=user.id,
        pair_id=pair.pair_id,
        text="跨网测试消息",
        mode="type",
        after_key="enter",
        smart_mode=False,
        smart_action=None,
        client_ip="127.0.0.1",
        delivery_status="pc_offline",
        ack_ok=False,
        ack_error="PC 离线",
    )

    list_resp = await test_client.get("/relay/messages", headers=headers)
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["text"] == "跨网测试消息"
    assert items[0]["delivery_status"] == "pc_offline"


@pytest.mark.asyncio
async def test_transmit_delivered_updates_message(
    test_client: AsyncClient, authenticated_user, db_session
):
    user = authenticated_user["user"]
    headers = authenticated_user["headers"]

    pair, _, _ = await relay_pair_service.create_pair(
        db_session, user.id, "Delivered Test"
    )

    message = await relay_message_service.create_relay_message(
        db_session,
        user_id=user.id,
        pair_id=pair.pair_id,
        text="Agent 在线消息",
        mode="type",
        after_key=None,
        smart_mode=False,
        smart_action=None,
        client_ip="127.0.0.1",
        delivery_status="pending",
    )

    await relay_message_service.update_relay_message_ack(
        db_session, message.id, "delivered", True
    )

    detail_resp = await test_client.get(
        f"/relay/messages/{message.id}", headers=headers
    )
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert data["delivery_status"] == "delivered"
    assert data["ack_ok"] is True


@pytest.mark.asyncio
async def test_relay_manager_routes_status():
    relay_manager._channels.clear()
    pair_id = "pair_test123"
    user_id = "00000000-0000-0000-0000-000000000001"

    channel = await relay_manager.get_or_create_channel(pair_id, user_id)
    assert channel.pair_id == pair_id

    online, phones, _ = relay_manager.get_pair_status(pair_id)
    assert online is False
    assert phones == 0

    await relay_manager.disconnect_pair(pair_id)
    assert await relay_manager.get_channel(pair_id) is None
