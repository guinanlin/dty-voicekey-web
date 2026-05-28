"""Orchestrate file upload through OSS Gateway (Mode C: core proxies storage)."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx
from fastapi import UploadFile

from app.integrations.storage_gateway_client import (
    StorageGatewayClient,
    StorageGatewayError,
    get_storage_gateway_client,
)
from app.utils import resolve_mime_type

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB demo limit


class FileService:
    def __init__(self, client: StorageGatewayClient | None = None) -> None:
        self.client = client or get_storage_gateway_client()

    def _internal_upload_url(self, upload_url: str) -> str:
        """Use internal gateway base URL for server-side upload proxy."""
        path = urlparse(upload_url).path
        return f"{self.client.base_url}{path}"

    async def upload_file(
        self,
        *,
        file: UploadFile,
        user_id: str,
        tenant_id: str = "default",
    ) -> dict:
        if not file.filename:
            raise ValueError("Filename is required")

        content = await file.read()
        size = len(content)
        if size == 0:
            raise ValueError("File is empty")
        if size > MAX_UPLOAD_SIZE:
            raise ValueError(f"File exceeds {MAX_UPLOAD_SIZE // (1024 * 1024)} MB limit")

        mime_type = resolve_mime_type(file.filename, file.content_type)
        gateway = StorageGatewayClient(
            base_url=self.client.base_url,
            service_token=self.client.service_token,
            tenant_id=tenant_id,
        )

        presign = await gateway.create_upload_url(
            filename=file.filename,
            size=size,
            mime_type=mime_type,
        )

        upload_url = self._internal_upload_url(presign["upload_url"])
        headers = presign.get("headers") or {}

        async with httpx.AsyncClient(timeout=gateway.timeout) as http:
            response = await http.put(upload_url, content=content, headers=headers)
            if response.status_code >= 400:
                raise StorageGatewayError(
                    f"Upload to gateway failed: {response.text}",
                    status_code=response.status_code,
                )

        complete = await gateway.complete_upload(
            file_id=presign["file_id"],
            object_key=presign["object_key"],
            size=size,
            mime_type=mime_type,
            biz_type="user",
            biz_id=user_id,
        )

        download = await gateway.get_download_url(presign["file_id"])

        return {
            "file_id": complete["file_id"],
            "filename": file.filename,
            "size": size,
            "mime_type": mime_type,
            "status": complete["status"],
            "download_url": download["download_url"],
        }

    async def get_download_url(self, file_id: str) -> dict:
        return await self.client.get_download_url(file_id)


def get_file_service() -> FileService:
    return FileService()
