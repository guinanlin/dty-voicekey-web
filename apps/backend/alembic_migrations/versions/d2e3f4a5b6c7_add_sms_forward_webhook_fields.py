"""add webhook fields for sms forward

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3d4e5f6
Create Date: 2026-07-04 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("webhook_api_key", sa.String(length=128), nullable=True),
    )
    op.create_index(
        op.f("ix_user_webhook_api_key"), "user", ["webhook_api_key"], unique=True
    )

    op.add_column(
        "sms_messages",
        sa.Column("forward_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "sms_messages",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="web"),
    )
    op.add_column(
        "sms_messages",
        sa.Column("device_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "sms_messages",
        sa.Column("rule_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "sms_messages",
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_sms_messages_forward_id"), "sms_messages", ["forward_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_sms_messages_forward_id"), table_name="sms_messages")
    op.drop_column("sms_messages", "content_sha256")
    op.drop_column("sms_messages", "rule_id")
    op.drop_column("sms_messages", "device_id")
    op.drop_column("sms_messages", "source")
    op.drop_column("sms_messages", "forward_id")
    op.drop_index(op.f("ix_user_webhook_api_key"), table_name="user")
    op.drop_column("user", "webhook_api_key")
