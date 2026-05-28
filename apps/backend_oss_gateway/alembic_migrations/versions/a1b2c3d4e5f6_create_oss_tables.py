"""create oss_* tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-05-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "oss_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("bucket", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("hash", sa.String(length=128), nullable=True),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("storage_class", sa.String(length=64), nullable=True),
        sa.Column(
            "visibility",
            sa.String(length=16),
            nullable=False,
            server_default="private",
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="oss_files_pkey"),
    )
    op.create_index("oss_files_tenant_id_idx", "oss_files", ["tenant_id"])
    op.create_index(
        "oss_files_tenant_object_key_uk",
        "oss_files",
        ["tenant_id", "object_key"],
        unique=True,
    )
    op.create_index("oss_files_hash_size_idx", "oss_files", ["hash", "size"])

    op.create_table(
        "oss_file_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("biz_type", sa.String(length=64), nullable=False),
        sa.Column("biz_id", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["oss_files.id"],
            name="oss_file_references_file_id_fk",
        ),
        sa.PrimaryKeyConstraint("id", name="oss_file_references_pkey"),
    )
    op.create_index(
        "oss_file_references_file_id_idx", "oss_file_references", ["file_id"]
    )
    op.create_index(
        "oss_file_references_biz_idx",
        "oss_file_references",
        ["biz_type", "biz_id"],
    )


def downgrade() -> None:
    op.drop_index("oss_file_references_biz_idx", table_name="oss_file_references")
    op.drop_index("oss_file_references_file_id_idx", table_name="oss_file_references")
    op.drop_table("oss_file_references")
    op.drop_index("oss_files_hash_size_idx", table_name="oss_files")
    op.drop_index("oss_files_tenant_object_key_uk", table_name="oss_files")
    op.drop_index("oss_files_tenant_id_idx", table_name="oss_files")
    op.drop_table("oss_files")
