import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.storage_gateway_client import (
    StorageGatewayClient,
    StorageGatewayError,
)


@pytest.mark.asyncio
async def test_create_upload_url_success():
    client = StorageGatewayClient(
        base_url="http://gateway.test",
        service_token="test-token",
        tenant_id="tenant-1",
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "file_id": "abc",
        "upload_url": "http://upload",
        "headers": {},
        "object_key": "key",
        "provider": "local",
        "expires_in": 3600,
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = await client.create_upload_url(
            filename="a.pdf", size=100, mime_type="application/pdf"
        )

    assert result["file_id"] == "abc"
    mock_client.request.assert_called_once()
    call_kwargs = mock_client.request.call_args.kwargs
    assert call_kwargs["headers"]["X-Service-Token"] == "test-token"
    assert call_kwargs["headers"]["X-Tenant-Id"] == "tenant-1"


@pytest.mark.asyncio
async def test_create_upload_url_error():
    client = StorageGatewayClient(base_url="http://gateway.test", service_token="t")
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "bad request"

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with pytest.raises(StorageGatewayError):
            await client.create_upload_url(
                filename="a.pdf", size=100, mime_type="application/pdf"
            )
