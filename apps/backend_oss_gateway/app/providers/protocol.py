from abc import ABC, abstractmethod

from app.providers.base import PresignDownloadResult, PresignUploadResult


class StorageProvider(ABC):
    name: str

    @abstractmethod
    async def presign_upload(
        self,
        bucket: str,
        object_key: str,
        mime_type: str,
        size: int,
    ) -> PresignUploadResult: ...

    @abstractmethod
    async def presign_download(
        self, bucket: str, object_key: str
    ) -> PresignDownloadResult: ...

    @abstractmethod
    async def delete(self, bucket: str, object_key: str) -> None: ...

    @abstractmethod
    async def exists(self, bucket: str, object_key: str) -> bool: ...
