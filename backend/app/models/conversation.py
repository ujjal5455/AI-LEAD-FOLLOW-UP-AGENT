import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Channel, ConversationStatus, db_enum, enum_check


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A message thread with one lead on one channel (e.g. a WhatsApp chat)."""

    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("business_id", "id"),
        ForeignKeyConstraint(
            ["business_id", "lead_id"], ["leads.business_id", "leads.id"], ondelete="CASCADE"
        ),
        Index("ix_conversations_business_id_lead_id", "business_id", "lead_id"),
        enum_check("channel", Channel),
        enum_check("status", ConversationStatus),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    lead_id: Mapped[uuid.UUID]
    channel: Mapped[Channel] = mapped_column(db_enum(Channel))
    status: Mapped[ConversationStatus] = mapped_column(
        db_enum(ConversationStatus),
        default=ConversationStatus.ACTIVE,
        server_default=ConversationStatus.ACTIVE.value,
    )
    last_message_at: Mapped[datetime | None]
