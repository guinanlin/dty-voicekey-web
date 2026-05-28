import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FileVisibility(str, enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"


class FileStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DELETED = "deleted"


class OssFile(Base):
    __tablename__ = "oss_files"
    __table_args__ = (
        Index(
            "oss_files_tenant_object_key_uk",
            "tenant_id",
            "object_key",
            unique=True,
        ),
        Index("oss_files_hash_size_idx", "hash", "size"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    visibility: Mapped[FileVisibility] = mapped_column(
        Enum(
            FileVisibility,
            name="oss_file_visibility",
            native_enum=False,
            length=16,
        ),
        default=FileVisibility.PRIVATE,
        nullable=False,
    )
    status: Mapped[FileStatus] = mapped_column(
        Enum(
            FileStatus,
            name="oss_file_status",
            native_enum=False,
            length=16,
        ),
        default=FileStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    references: Mapped[list["OssFileReference"]] = relationship(
        "OssFileReference", back_populates="file", cascade="all, delete-orphan"
    )


class OssFileReference(Base):
    __tablename__ = "oss_file_references"
    __table_args__ = (
        Index("oss_file_references_file_id_idx", "file_id"),
        Index("oss_file_references_biz_idx", "biz_type", "biz_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("oss_files.id", name="oss_file_references_file_id_fk"),
        nullable=False,
        index=True,
    )
    biz_type: Mapped[str] = mapped_column(String(64), nullable=False)
    biz_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    file: Mapped["OssFile"] = relationship("OssFile", back_populates="references")
