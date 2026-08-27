from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base_model import Base


def utcnow():
    return datetime.now(timezone.utc)


class RelayPair(Base):
    __tablename__ = "relay_pairs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    pair_id = Column(String(64), unique=True, nullable=False, index=True)
    pair_token_hash = Column(String(64), nullable=False)
    agent_token_hash = Column(String(64), nullable=False)
    device_name = Column(String(128), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    user = relationship("User", back_populates="relay_pairs")


class RelayMessage(Base):
    __tablename__ = "relay_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    pair_id = Column(String(64), nullable=False, index=True)
    text = Column(Text, nullable=False)
    mode = Column(String(32), nullable=True)
    after_key = Column(String(32), nullable=True)
    smart_mode = Column(Boolean, nullable=False, default=False)
    smart_action = Column(String(128), nullable=True)
    delivery_status = Column(String(32), nullable=False, default="pending")
    ack_ok = Column(Boolean, nullable=True)
    ack_error = Column(String(512), nullable=True)
    client_ip = Column(String(64), nullable=True)
    deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )

    user = relationship("User", back_populates="relay_messages")
