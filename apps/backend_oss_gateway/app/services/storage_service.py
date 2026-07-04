import uuid
from pathlib import PurePosixPath

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import FileStatus, FileVisibility
from app.providers.base import ProviderError
from app.providers.registry import default_bucket, get_provider
from app.repositories.metadata_repo import MetadataRepository


def _build_object_key(tenant_id: str, filename: str) -> str:
    safe_name = PurePosixPath(filename).name
    return f"{tenant_id}/{uuid.uuid4().hex}/{safe_name}"


class StorageService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = MetadataRepository(session)
        self.session = session

    async def presign_upload(
        self,
        *,
        tenant_id: str,
        filename: str,
        size: int,
        mime_type: str,
        provider_name: str | None,
        visibility: str,
    ) -> dict:
        provider = get_provider(provider_name)
        bucket = default_bucket(provider.name)
        object_key = _build_object_key(tenant_id, filename)
        vis = (
            FileVisibility.PUBLIC if visibility == "public" else FileVisibility.PRIVATE
        )
        record = await self.repo.create_pending_file(
            tenant_id=tenant_id,
            provider=provider.name,
            bucket=bucket,
            object_key=object_key,
            mime_type=mime_type,
            size=size,
            visibility=vis,
        )
        presign = await provider.presign_upload(bucket, object_key, mime_type, size)
        await self.session.commit()
        return {
            "file_id": str(record.id),
            "upload_url": presign.upload_url,
            "headers": presign.headers,
            "object_key": presign.object_key,
            "provider": provider.name,
            "expires_in": presign.expires_in,
        }

    async def complete_upload(
        self,
        *,
        tenant_id: str,
        file_id: str,
        object_key: str,
        file_hash: str | None,
        size: int | None,
        mime_type: str | None,
        idempotency_key: str | None,
        biz_type: str | None,
        biz_id: str | None,
    ) -> dict:
        if idempotency_key:
            existing = await self.repo.get_by_idempotency(tenant_id, idempotency_key)
            if existing and existing.status == FileStatus.ACTIVE:
                return {
                    "file_id": str(existing.id),
                    "status": existing.status.value,
                    "object_key": existing.object_key,
                }

        record = await self.repo.get_by_id(uuid.UUID(file_id), tenant_id)
        if not record:
            raise ValueError("File not found")
        if record.object_key != object_key:
            raise ValueError("Object key mismatch")
        if record.status == FileStatus.ACTIVE:
            return {
                "file_id": str(record.id),
                "status": record.status.value,
                "object_key": record.object_key,
            }

        provider = get_provider(record.provider)
        if record.provider != "local":
            exists = await provider.exists(record.bucket, object_key)
            if not exists:
                raise ValueError("Object not found in storage")

        idem_hash = idempotency_key or file_hash
        record = await self.repo.activate_file(
            record, file_hash=idem_hash, size=size, mime_type=mime_type
        )
        if biz_type and biz_id:
            await self.repo.add_reference(record.id, biz_type, biz_id)
        await self.session.commit()
        return {
            "file_id": str(record.id),
            "status": record.status.value,
            "object_key": record.object_key,
        }

    async def get_download_url(self, *, tenant_id: str, file_id: str) -> dict:
        record = await self.repo.get_by_id(uuid.UUID(file_id), tenant_id)
        if not record or record.status != FileStatus.ACTIVE:
            raise ValueError("File not found or not active")
        provider = get_provider(record.provider)
        presign = await provider.presign_download(record.bucket, record.object_key)
        return {
            "file_id": str(record.id),
            "download_url": presign.download_url,
            "expires_in": presign.expires_in,
        }

    async def delete_file(self, *, tenant_id: str, file_id: str) -> dict:
        record = await self.repo.get_by_id(uuid.UUID(file_id), tenant_id)
        if not record or record.status == FileStatus.DELETED:
            raise ValueError("File not found")
        provider = get_provider(record.provider)
        try:
            await provider.delete(record.bucket, record.object_key)
        except ProviderError:
            pass
        record = await self.repo.mark_deleted(record)
        await self.session.commit()
        return {"file_id": str(record.id), "status": record.status.value}
