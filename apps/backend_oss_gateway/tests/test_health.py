import pytest


@pytest.mark.asyncio
async def test_health(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_presign_requires_service_token(async_client):
    response = await async_client.post(
        "/api/v1/upload/presign",
        json={"filename": "test.pdf", "size": 1024, "mime_type": "application/pdf"},
    )
    assert response.status_code == 401
