from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )
    webhook_api_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")
    sms_messages = relationship(
        "SmsMessage", back_populates="user", cascade="all, delete-orphan"
    )
