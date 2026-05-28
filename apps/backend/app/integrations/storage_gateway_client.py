"""HTTP client for backend -> OSS Gateway integration.

Business code should only use this facade; do not import cloud vendor SDKs
or write to oss_* tables directly from apps/backend.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageGatewayError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class StorageGatewayClient:
    def __init__(
        self,
        base_url: str | None = None,
        service_token: str | None = None,
        tenant_id: str = "default",
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        self.base_url = (base_url or settings.OSS_GATEWAY_BASE_URL).rstrip("/")
        self.service_token = service_token or settings.OSS_GATEWAY_SERVICE_TOKEN
        self.tenant_id = tenant_id
        self.timeout = timeout
        self.max_retries = max_retries

    def _headers(self, trace_id: str | None = None) -> dict[str, str]:
        headers = {
            "X-Service-Token": self.service_token,
            "X-Tenant-Id": self.tenant_id,
        }
        if trace_id:
            headers["X-Request-Id"] = trace_id
        else:
            headers["X-Request-Id"] = str(uuid.uuid4())
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method,
                        url,
                        json=json,
                        headers=self._headers(trace_id),
                    )
                if response.status_code >= 500 and attempt < self.max_retries:
                    continue
                if response.status_code >= 400:
                    raise StorageGatewayError(
                        response.text, status_code=response.status_code
                    )
                return response.json()
            except httpx.RequestError as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise StorageGatewayError(str(exc)) from exc
        raise StorageGatewayError(str(last_error or "Unknown gateway error"))

    async def create_upload_url(
        self,
        *,
        filename: str,
        size: int,
        mime_type: str,
        provider: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "filename": filename,
            "size": size,
            "mime_type": mime_type,
        }
        if provider:
            payload["provider"] = provider
        return await self._request(
            "POST", "/api/v1/upload/presign", json=payload, trace_id=trace_id
        )

    async def complete_upload(
        self,
        *,
        file_id: str,
        object_key: str,
        file_hash: str | None = None,
        size: int | None = None,
        mime_type: str | None = None,
        idempotency_key: str | None = None,
        biz_type: str | None = None,
        biz_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "file_id": file_id,
            "object_key": object_key,
        }
        if file_hash:
            payload["hash"] = file_hash
        if size is not None:
            payload["size"] = size
        if mime_type:
            payload["mime_type"] = mime_type
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        if biz_type and biz_id:
            payload["biz_type"] = biz_type
            payload["biz_id"] = biz_id
        return await self._request(
            "POST", "/api/v1/upload/complete", json=payload, trace_id=trace_id
        )

    async def get_download_url(
        self, file_id: str, *, trace_id: str | None = None
    ) -> dict[str, Any]:
        return await self._request(
            "GET", f"/api/v1/files/{file_id}/download", trace_id=trace_id
        )

    async def delete_file(
        self, file_id: str, *, trace_id: str | None = None
    ) -> dict[str, Any]:
        return await self._request(
            "DELETE", f"/api/v1/files/{file_id}", trace_id=trace_id
        )


def get_storage_gateway_client(tenant_id: str = "default") -> StorageGatewayClient:
    return StorageGatewayClient(tenant_id=tenant_id)
