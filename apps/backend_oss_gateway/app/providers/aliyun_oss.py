import asyncio

import oss2

from app.core.config import settings
from app.providers.base import PresignDownloadResult, PresignUploadResult, ProviderError
from app.providers.protocol import StorageProvider


class AliyunOSSProvider(StorageProvider):
    name = "oss"

    def __init__(self) -> None:
        if not settings.OSS_ACCESS_KEY_ID or not settings.OSS_ACCESS_KEY_SECRET:
            raise ProviderError("Aliyun OSS credentials not configured")
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        self._bucket_name = settings.OSS_BUCKET
        self._bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, self._bucket_name)

    def _bucket(self, bucket: str | None) -> str:
        return bucket or self._bucket_name

    async def presign_upload(
        self, bucket: str, object_key: str, mime_type: str, size: int
    ) -> PresignUploadResult:
        def _presign() -> str:
            return self._bucket.sign_url(
                "PUT",
                object_key,
                settings.PRESIGN_UPLOAD_TTL,
                headers={"Content-Type": mime_type},
            )

        url = await asyncio.to_thread(_presign)
        return PresignUploadResult(
            upload_url=url,
            headers={"Content-Type": mime_type},
            object_key=object_key,
            expires_in=settings.PRESIGN_UPLOAD_TTL,
        )

    async def presign_download(
        self, bucket: str, object_key: str
    ) -> PresignDownloadResult:
        def _presign() -> str:
            return self._bucket.sign_url(
                "GET", object_key, settings.PRESIGN_DOWNLOAD_TTL
            )

        url = await asyncio.to_thread(_presign)
        return PresignDownloadResult(
            download_url=url, expires_in=settings.PRESIGN_DOWNLOAD_TTL
        )

    async def delete(self, bucket: str, object_key: str) -> None:
        await asyncio.to_thread(self._bucket.delete_object, object_key)

    async def exists(self, bucket: str, object_key: str) -> bool:
        try:
            await asyncio.to_thread(self._bucket.head_object, object_key)
            return True
        except oss2.exceptions.NoSuchKey:
            return False
        except Exception:
            return False
