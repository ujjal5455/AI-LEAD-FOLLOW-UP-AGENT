import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import LeadSource, LeadStatus, Level, db_enum, enum_check


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A potential customer of a business."""

    __tablename__ = "leads"
    __table_args__ = (
        # Child tables reference (business_id, id) as a pair. That way the database
        # itself guarantees a conversation, follow-up or appointment belongs to the
        # same business as its lead, even if application code has a bug.
        UniqueConstraint("business_id", "id"),
        # One phone number is one lead per business (WhatsApp identifies people by number).
        Index(
            "uq_leads_business_id_phone",
            "business_id",
            "phone",
            unique=True,
            postgresql_where=text("phone IS NOT NULL"),
        ),
        Index("ix_leads_business_id_status", "business_id", "status"),
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
        enum_check("source", LeadSource),
        enum_check("status", LeadStatus),
        enum_check("urgency", Level),
        enum_check("purchase_intent", Level),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(320))
    source: Mapped[LeadSource] = mapped_column(db_enum(LeadSource))
    status: Mapped[LeadStatus] = mapped_column(
        db_enum(LeadStatus),
        default=LeadStatus.NEW,
        server_default=LeadStatus.NEW.value,
    )
    score: Mapped[int] = mapped_column(default=0, server_default="0")
    # Why the lead has its score, e.g. [{"factor": "budget_fit", "points": 20, "reason": "..."}]
    score_breakdown: Mapped[list[Any]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )

    # Qualification details, gathered naturally during the conversation.
    service_interest: Mapped[str | None] = mapped_column(String(200))
    budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    location: Mapped[str | None] = mapped_column(String(200))
    urgency: Mapped[Level | None] = mapped_column(db_enum(Level))
    timeline: Mapped[str | None] = mapped_column(String(200))
    requirements: Mapped[str | None] = mapped_column(Text)
    availability: Mapped[str | None] = mapped_column(String(200))
    purchase_intent: Mapped[Level | None] = mapped_column(db_enum(Level))

    summary: Mapped[str | None] = mapped_column(Text)
    last_contact_at: Mapped[datetime | None]
