import pytest

from tests.conftest import SERVICE_HEADERS


@pytest.mark.asyncio
async def test_local_upload_flow(test_client):
    presign = await test_client.post(
        "/api/v1/upload/presign",
        json={
            "filename": "invoice.pdf",
            "size": 128,
            "mime_type": "application/pdf",
            "provider": "local",
        },
        headers=SERVICE_HEADERS,
    )
    assert presign.status_code == 200, presign.text
    data = presign.json()
    file_id = data["file_id"]
    object_key = data["object_key"]
    upload_url = data["upload_url"]

    token = upload_url.rsplit("/", 1)[-1]
    upload_resp = await test_client.put(
        f"/api/v1/upload/local/{token}",
        content=b"%PDF-1.4 test content",
        headers={"Content-Type": "application/pdf"},
    )
    assert upload_resp.status_code == 200

    complete = await test_client.post(
        "/api/v1/upload/complete",
        json={
            "file_id": file_id,
            "object_key": object_key,
            "hash": "abc123",
            "size": 128,
            "mime_type": "application/pdf",
            "idempotency_key": "idem-001",
        },
        headers=SERVICE_HEADERS,
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "active"

    download = await test_client.get(
        f"/api/v1/files/{file_id}/download",
        headers=SERVICE_HEADERS,
    )
    assert download.status_code == 200
    assert "download_url" in download.json()

    delete = await test_client.delete(
        f"/api/v1/files/{file_id}",
        headers=SERVICE_HEADERS,
    )
    assert delete.status_code == 200
    assert delete.json()["status"] == "deleted"
