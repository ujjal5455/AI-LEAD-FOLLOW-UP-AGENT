import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import FollowUpStatus, db_enum, enum_check


class FollowUp(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A message scheduled to re-engage a lead who stopped replying."""

    __tablename__ = "followups"
    __table_args__ = (
        ForeignKeyConstraint(
            ["business_id", "lead_id"], ["leads.business_id", "leads.id"], ondelete="CASCADE"
        ),
        Index("ix_followups_business_id_lead_id", "business_id", "lead_id"),
        # What the follow-up worker asks for: pending follow-ups that are due.
        Index("ix_followups_status_scheduled_at", "status", "scheduled_at"),
        # At most one pending follow-up per lead, so a lead can't be double-messaged.
        Index(
            "uq_followups_one_pending_per_lead",
            "lead_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        enum_check("status", FollowUpStatus),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    lead_id: Mapped[uuid.UUID]
    scheduled_at: Mapped[datetime]
    # Empty means "write it at send time", using the latest conversation context.
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[FollowUpStatus] = mapped_column(
        db_enum(FollowUpStatus),
        default=FollowUpStatus.PENDING,
        server_default=FollowUpStatus.PENDING.value,
    )
    attempt_number: Mapped[int] = mapped_column(default=1, server_default="1")
    sent_at: Mapped[datetime | None]
    cancel_reason: Mapped[str | None] = mapped_column(String(64))
