from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base_model import Base


def utcnow():
    return datetime.now(timezone.utc)


class SmsMessage(Base):
    __tablename__ = "sms_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    forward_id = Column(UUID(as_uuid=True), unique=True, nullable=True, index=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    phone = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, index=True)
    starred = Column(Boolean, nullable=False, default=False, index=True)
    deleted = Column(Boolean, nullable=False, default=False)
    source = Column(String(20), nullable=False, default="web")
    device_id = Column(String(36), nullable=True)
    rule_id = Column(Integer, nullable=True)
    content_sha256 = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    user = relationship("User", back_populates="sms_messages")
