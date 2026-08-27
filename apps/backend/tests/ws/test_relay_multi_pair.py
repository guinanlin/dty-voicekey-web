import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from starlette.websockets import WebSocketDisconnect, WebSocketState

from app.ws import relay_hub
from app.ws.connection_manager import relay_manager


class FakeWebSocket:
    def __init__(self, frames=None):
        self.frames = list(frames or [])
        self.sent = []
        self.client_state = WebSocketState.CONNECTED
        self.url = SimpleNamespace(scheme="wss")
        self.client = SimpleNamespace(host="127.0.0.1")

    async def accept(self):
        return None

    async def receive_text(self):
        if self.frames:
            return json.dumps(self.frames.pop(0), ensure_ascii=False)
        raise WebSocketDisconnect()

    async def send_text(self, text):
        self.sent.append(json.loads(text))

    async def close(self, **_kwargs):
        self.client_state = WebSocketState.DISCONNECTED


class FakeSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *_args):
        return None


@pytest.fixture(autouse=True)
def clear_relay_channels():
    relay_manager._channels.clear()
    yield
    relay_manager._channels.clear()


async def run_transmit(monkeypatch, payload, *, online_pairs=(), allowed_pairs=None):
    user_id = uuid4()
    default_pair_id = "pair_default"
    allowed = set(allowed_pairs or {default_pair_id, "pair_A", "pair_B"})
    default_pair = SimpleNamespace(pair_id=default_pair_id, user_id=user_id)
    created = []

    async def load_pair_by_token(_db, _token):
        return default_pair

    async def load_target(_db, pair_id, requested_user_id):
        if pair_id not in allowed or requested_user_id != user_id:
            return None
        return SimpleNamespace(pair_id=pair_id, user_id=user_id)

    async def create_message(_db, **kwargs):
        message = SimpleNamespace(id=uuid4(), **kwargs)
        created.append(message)
        return message

    async def noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr(relay_hub, "async_session_maker", FakeSessionContext)
    monkeypatch.setattr(relay_hub, "_load_pair_by_token", load_pair_by_token)
    monkeypatch.setattr(relay_hub, "_load_valid_target_pair", load_target)
    monkeypatch.setattr(relay_hub, "_pair_is_valid", lambda _pair: True)
    monkeypatch.setattr(relay_hub, "check_rate_limit", noop)
    monkeypatch.setattr(relay_hub, "create_relay_message", create_message)
    monkeypatch.setattr(relay_hub, "notify_message_created", noop)
    monkeypatch.setattr(relay_hub, "notify_message_updated_by_id", noop)
    monkeypatch.setattr(relay_hub, "update_relay_message_ack", noop)
    monkeypatch.setattr(relay_hub.settings, "RELAY_REQUIRE_WSS", False)

    agents = {}
    for pair_id in online_pairs:
        agent = FakeWebSocket()
        agents[pair_id] = agent
        await relay_manager.bind_agent(pair_id, user_id, agent)

    phone = FakeWebSocket([payload])
    await relay_hub.phone_ws(phone, pair="pt_default")
    return phone, agents, created


@pytest.mark.asyncio
async def test_target_pair_a_only_reaches_pc_a(monkeypatch):
    phone, agents, created = await run_transmit(
        monkeypatch,
        {"type": "transmit", "text": "to A", "target_pair_id": "pair_A"},
        online_pairs={"pair_A", "pair_B"},
    )
    assert len(agents["pair_A"].sent) == 1
    assert agents["pair_B"].sent == []
    assert agents["pair_A"].sent[0]["message_id"] == str(created[0].id)
    assert created[0].pair_id == "pair_A"


@pytest.mark.asyncio
async def test_target_pair_b_only_reaches_pc_b(monkeypatch):
    _, agents, created = await run_transmit(
        monkeypatch,
        {"type": "transmit", "text": "to B", "pair_id": "pair_B"},
        online_pairs={"pair_A", "pair_B"},
    )
    assert agents["pair_A"].sent == []
    assert len(agents["pair_B"].sent) == 1
    assert created[0].pair_id == "pair_B"


@pytest.mark.asyncio
async def test_missing_target_uses_connection_pair(monkeypatch):
    _, agents, created = await run_transmit(
        monkeypatch,
        {"type": "transmit", "text": "legacy"},
        online_pairs={"pair_default", "pair_A"},
    )
    assert len(agents["pair_default"].sent) == 1
    assert agents["pair_A"].sent == []
    assert created[0].pair_id == "pair_default"


@pytest.mark.asyncio
async def test_foreign_target_is_rejected_without_persist_or_forward(monkeypatch):
    phone, agents, created = await run_transmit(
        monkeypatch,
        {"type": "transmit", "text": "blocked", "target": "pair_foreign"},
        online_pairs={"pair_A"},
        allowed_pairs={"pair_default", "pair_A"},
    )
    assert created == []
    assert agents["pair_A"].sent == []
    assert phone.sent[-1] == {
        "type": "ack",
        "ok": False,
        "error": "目标配对不存在或不属于当前账号",
    }


@pytest.mark.asyncio
async def test_offline_target_is_persisted_and_acked(monkeypatch):
    phone, _, created = await run_transmit(
        monkeypatch,
        {"type": "transmit", "text": "offline", "target_pair_id": "pair_B"},
    )
    assert created[0].pair_id == "pair_B"
    assert created[0].delivery_status == "pc_offline"
    assert created[0].ack_ok is False
    assert created[0].ack_error == "PC 离线"
    assert phone.sent[-1] == {"type": "ack", "ok": False, "error": "PC 离线"}


@pytest.mark.asyncio
async def test_ack_with_message_id_pops_exact_pending_message():
    user_id = uuid4()
    channel = await relay_manager.get_or_create_channel("pair_A", user_id)
    phone_one = FakeWebSocket()
    phone_two = FakeWebSocket()
    first_id = uuid4()
    second_id = uuid4()
    relay_manager.set_pending_message(channel, first_id, phone_one)
    relay_manager.set_pending_message(channel, second_id, phone_two)

    assert relay_manager.pop_pending_message(channel, second_id) == (
        second_id,
        phone_two,
    )
    assert relay_manager.pop_pending_message(channel) == (first_id, phone_one)
