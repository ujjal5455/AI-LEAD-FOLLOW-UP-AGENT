import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import SenderType, db_enum, enum_check


class Message(UUIDPrimaryKeyMixin, Base):
    """One message in a conversation. Messages are never edited once stored."""

    __tablename__ = "messages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["business_id", "conversation_id"],
            ["conversations.business_id", "conversations.id"],
            ondelete="CASCADE",
        ),
        Index("ix_messages_conversation_id_created_at", "conversation_id", "created_at"),
        # Each provider message ID (e.g. WhatsApp's) is stored once, so a webhook
        # delivered twice can never create a duplicate message or a duplicate reply.
        Index(
            "uq_messages_business_id_external_id",
            "business_id",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
        enum_check("sender_type", SenderType),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    conversation_id: Mapped[uuid.UUID]
    sender_type: Mapped[SenderType] = mapped_column(db_enum(SenderType))
    content: Mapped[str] = mapped_column(Text)
    # SQLAlchemy reserves the attribute name "metadata", so in Python it's `meta`.
    meta: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
