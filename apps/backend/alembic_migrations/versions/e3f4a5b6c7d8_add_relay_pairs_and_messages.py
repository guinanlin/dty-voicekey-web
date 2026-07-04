"""add relay pairs and messages

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-07-04 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "relay_pairs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("pair_id", sa.String(length=64), nullable=False),
        sa.Column("pair_token_hash", sa.String(length=64), nullable=False),
        sa.Column("agent_token_hash", sa.String(length=64), nullable=False),
        sa.Column("device_name", sa.String(length=128), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_relay_pairs_pair_id"), "relay_pairs", ["pair_id"], unique=True
    )
    op.create_index(
        op.f("ix_relay_pairs_user_id"), "relay_pairs", ["user_id"], unique=False
    )

    op.create_table(
        "relay_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("pair_id", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=True),
        sa.Column("after_key", sa.String(length=32), nullable=True),
        sa.Column("smart_mode", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("smart_action", sa.String(length=128), nullable=True),
        sa.Column("delivery_status", sa.String(length=32), nullable=False),
        sa.Column("ack_ok", sa.Boolean(), nullable=True),
        sa.Column("ack_error", sa.String(length=512), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_relay_messages_created_at"),
        "relay_messages",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_relay_messages_deleted"), "relay_messages", ["deleted"], unique=False
    )
    op.create_index(
        op.f("ix_relay_messages_pair_id"), "relay_messages", ["pair_id"], unique=False
    )
    op.create_index(
        op.f("ix_relay_messages_user_id"), "relay_messages", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_relay_messages_user_id"), table_name="relay_messages")
    op.drop_index(op.f("ix_relay_messages_pair_id"), table_name="relay_messages")
    op.drop_index(op.f("ix_relay_messages_deleted"), table_name="relay_messages")
    op.drop_index(op.f("ix_relay_messages_created_at"), table_name="relay_messages")
    op.drop_table("relay_messages")
    op.drop_index(op.f("ix_relay_pairs_user_id"), table_name="relay_pairs")
    op.drop_index(op.f("ix_relay_pairs_pair_id"), table_name="relay_pairs")
    op.drop_table("relay_pairs")
