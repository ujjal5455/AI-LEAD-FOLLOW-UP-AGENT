import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AppointmentStatus, db_enum, enum_check


class Appointment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A consultation or site visit booked with a lead."""

    __tablename__ = "appointments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["business_id", "lead_id"], ["leads.business_id", "leads.id"], ondelete="CASCADE"
        ),
        Index("ix_appointments_business_id_lead_id", "business_id", "lead_id"),
        Index("ix_appointments_business_id_scheduled_at", "business_id", "scheduled_at"),
        CheckConstraint("duration_minutes > 0", name="duration_positive"),
        enum_check("status", AppointmentStatus),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    lead_id: Mapped[uuid.UUID]
    scheduled_at: Mapped[datetime]
    duration_minutes: Mapped[int] = mapped_column(default=60, server_default="60")
    status: Mapped[AppointmentStatus] = mapped_column(
        db_enum(AppointmentStatus),
        default=AppointmentStatus.PENDING,
        server_default=AppointmentStatus.PENDING.value,
    )
    notes: Mapped[str | None] = mapped_column(Text)
