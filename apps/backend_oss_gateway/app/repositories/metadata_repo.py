import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import FileStatus, FileVisibility, OssFile, OssFileReference


class MetadataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_pending_file(
        self,
        *,
        tenant_id: str,
        provider: str,
        bucket: str,
        object_key: str,
        mime_type: str | None,
        size: int | None,
        visibility: FileVisibility = FileVisibility.PRIVATE,
    ) -> OssFile:
        record = OssFile(
            tenant_id=tenant_id,
            provider=provider,
            bucket=bucket,
            object_key=object_key,
            mime_type=mime_type,
            size=size,
            visibility=visibility,
            status=FileStatus.PENDING,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_by_id(self, file_id: uuid.UUID, tenant_id: str) -> OssFile | None:
        stmt = select(OssFile).where(
            OssFile.id == file_id, OssFile.tenant_id == tenant_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_object_key(
        self, tenant_id: str, object_key: str
    ) -> OssFile | None:
        stmt = select(OssFile).where(
            OssFile.tenant_id == tenant_id, OssFile.object_key == object_key
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency(
        self, tenant_id: str, idempotency_key: str
    ) -> OssFile | None:
        # MVP: idempotency_key stored in object_key suffix pattern or hash field
        stmt = select(OssFile).where(
            OssFile.tenant_id == tenant_id, OssFile.hash == idempotency_key
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def activate_file(
        self,
        record: OssFile,
        *,
        file_hash: str | None,
        size: int | None,
        mime_type: str | None,
    ) -> OssFile:
        record.hash = file_hash
        record.size = size
        record.mime_type = mime_type or record.mime_type
        record.status = FileStatus.ACTIVE
        await self.session.flush()
        return record

    async def mark_deleted(self, record: OssFile) -> OssFile:
        record.status = FileStatus.DELETED
        await self.session.flush()
        return record

    async def add_reference(
        self, file_id: uuid.UUID, biz_type: str, biz_id: str
    ) -> OssFileReference:
        ref = OssFileReference(file_id=file_id, biz_type=biz_type, biz_id=biz_id)
        self.session.add(ref)
        await self.session.flush()
        return ref
