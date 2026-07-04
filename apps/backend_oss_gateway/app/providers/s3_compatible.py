import asyncio

import boto3
from botocore.config import Config

from app.core.config import settings
from app.providers.base import PresignDownloadResult, PresignUploadResult, ProviderError
from app.providers.protocol import StorageProvider


class S3CompatibleProvider(StorageProvider):
    name = "s3"

    def __init__(self) -> None:
        if not settings.S3_ACCESS_KEY or not settings.S3_SECRET_KEY:
            raise ProviderError("S3 credentials not configured")
        client_kwargs: dict = {
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "region_name": settings.S3_REGION,
            "config": Config(signature_version="s3v4"),
        }
        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        self._client = boto3.client("s3", **client_kwargs)

    def _bucket(self, bucket: str | None) -> str:
        return bucket or settings.S3_BUCKET

    async def presign_upload(
        self, bucket: str, object_key: str, mime_type: str, size: int
    ) -> PresignUploadResult:
        b = self._bucket(bucket)

        def _presign() -> dict:
            return self._client.generate_presigned_post(
                Bucket=b,
                Key=object_key,
                Fields={"Content-Type": mime_type},
                Conditions=[
                    {"Content-Type": mime_type},
                    ["content-length-range", 1, max(size, 1)],
                ],
                ExpiresIn=settings.PRESIGN_UPLOAD_TTL,
            )

        result = await asyncio.to_thread(_presign)
        return PresignUploadResult(
            upload_url=result["url"],
            headers=result["fields"],
            object_key=object_key,
            expires_in=settings.PRESIGN_UPLOAD_TTL,
        )

    async def presign_download(
        self, bucket: str, object_key: str
    ) -> PresignDownloadResult:
        b = self._bucket(bucket)

        def _presign() -> str:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": b, "Key": object_key},
                ExpiresIn=settings.PRESIGN_DOWNLOAD_TTL,
            )

        url = await asyncio.to_thread(_presign)
        return PresignDownloadResult(
            download_url=url, expires_in=settings.PRESIGN_DOWNLOAD_TTL
        )

    async def delete(self, bucket: str, object_key: str) -> None:
        b = self._bucket(bucket)
        await asyncio.to_thread(self._client.delete_object, Bucket=b, Key=object_key)

    async def exists(self, bucket: str, object_key: str) -> bool:
        b = self._bucket(bucket)
        try:
            await asyncio.to_thread(self._client.head_object, Bucket=b, Key=object_key)
            return True
        except Exception:
            return False
