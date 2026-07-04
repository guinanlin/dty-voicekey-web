"""add user phone and sms_messages

Revision ID: c1a2b3d4e5f6
Revises: b389592974f8
Create Date: 2026-07-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, None] = "b389592974f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("phone", sa.String(length=20), nullable=True))
    op.create_index(op.f("ix_user_phone"), "user", ["phone"], unique=True)

    op.create_table(
        "sms_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("starred", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sms_messages_user_id"), "sms_messages", ["user_id"])
    op.create_index(op.f("ix_sms_messages_phone"), "sms_messages", ["phone"])
    op.create_index(
        op.f("ix_sms_messages_received_at"), "sms_messages", ["received_at"]
    )
    op.create_index(op.f("ix_sms_messages_starred"), "sms_messages", ["starred"])


def downgrade() -> None:
    op.drop_index(op.f("ix_sms_messages_starred"), table_name="sms_messages")
    op.drop_index(op.f("ix_sms_messages_received_at"), table_name="sms_messages")
    op.drop_index(op.f("ix_sms_messages_phone"), table_name="sms_messages")
    op.drop_index(op.f("ix_sms_messages_user_id"), table_name="sms_messages")
    op.drop_table("sms_messages")
    op.drop_index(op.f("ix_user_phone"), table_name="user")
    op.drop_column("user", "phone")
