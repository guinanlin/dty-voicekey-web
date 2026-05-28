import asyncio
import secrets
from pathlib import Path

from app.core.config import settings
from app.providers.base import PresignDownloadResult, PresignUploadResult
from app.providers.protocol import StorageProvider

# In-memory upload tokens for local dev (Phase 2: Redis)
_local_upload_tokens: dict[str, str] = {}


class LocalProvider(StorageProvider):
    name = "local"

    def __init__(self) -> None:
        self.storage_path = Path(settings.LOCAL_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.base_url = settings.LOCAL_PUBLIC_BASE_URL.rstrip("/")

    def _object_path(self, bucket: str, object_key: str) -> Path:
        return self.storage_path / bucket / object_key

    async def presign_upload(
        self, bucket: str, object_key: str, mime_type: str, size: int
    ) -> PresignUploadResult:
        token = secrets.token_urlsafe(32)
        _local_upload_tokens[token] = f"{bucket}/{object_key}"
        upload_url = f"{self.base_url}/api/v1/upload/local/{token}"
        return PresignUploadResult(
            upload_url=upload_url,
            headers={"Content-Type": mime_type},
            object_key=object_key,
            expires_in=settings.PRESIGN_UPLOAD_TTL,
        )

    async def presign_download(
        self, bucket: str, object_key: str
    ) -> PresignDownloadResult:
        return PresignDownloadResult(
            download_url=f"{self.base_url}/api/v1/files/local/{bucket}/{object_key}",
            expires_in=settings.PRESIGN_DOWNLOAD_TTL,
        )

    async def delete(self, bucket: str, object_key: str) -> None:
        path = self._object_path(bucket, object_key)
        if path.exists():
            await asyncio.to_thread(path.unlink)

    async def exists(self, bucket: str, object_key: str) -> bool:
        return self._object_path(bucket, object_key).exists()

    def resolve_upload_token(self, token: str) -> tuple[str, str] | None:
        value = _local_upload_tokens.get(token)
        if not value:
            return None
        bucket, object_key = value.split("/", 1)
        return bucket, object_key

    def consume_upload_token(self, token: str) -> tuple[str, str] | None:
        value = _local_upload_tokens.pop(token, None)
        if not value:
            return None
        bucket, object_key = value.split("/", 1)
        return bucket, object_key

    def save_upload(self, bucket: str, object_key: str, data: bytes) -> None:
        path = self._object_path(bucket, object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read_file(self, bucket: str, object_key: str) -> bytes | None:
        path = self._object_path(bucket, object_key)
        if not path.exists():
            return None
        return path.read_bytes()
