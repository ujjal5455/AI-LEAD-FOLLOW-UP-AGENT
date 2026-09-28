"""Fixed sets of allowed values, shared by the database, the API and (later) the AI tools."""

from enum import StrEnum

from sqlalchemy import CheckConstraint
from sqlalchemy import Enum as SAEnum


def db_enum(enum_cls: type[StrEnum]) -> SAEnum:
    """Store an enum as plain text (easier to evolve than PostgreSQL's native ENUM type).

    Pair every such column with `enum_check(...)` in the table's __table_args__.
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=32,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )


def enum_check(column: str, enum_cls: type[StrEnum]) -> CheckConstraint:
    """A CHECK constraint so the database itself rejects values outside the enum.

    When an enum gains or loses a value, write a migration that replaces this constraint.
    """
    allowed = ", ".join(f"'{member.value}'" for member in enum_cls)
    return CheckConstraint(f"{column} IN ({allowed})", name=f"{column}_allowed")


class LeadStatus(StrEnum):
    NEW = "new"
    ENGAGED = "engaged"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    HOT = "hot"
    APPOINTMENT_PENDING = "appointment_pending"
    APPOINTMENT_BOOKED = "appointment_booked"
    HUMAN_HANDOFF = "human_handoff"
    CONVERTED = "converted"
    LOST = "lost"
    NOT_INTERESTED = "not_interested"
    OPTED_OUT = "opted_out"


class LeadSource(StrEnum):
    SIMULATOR = "simulator"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    WEBSITE = "website"
    EMAIL = "email"
    MANUAL = "manual"


class Channel(StrEnum):
    SIMULATOR = "simulator"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    WEBSITE = "website"
    EMAIL = "email"


class ConversationStatus(StrEnum):
    ACTIVE = "active"  # the AI replies automatically
    HUMAN_HANDOFF = "human_handoff"  # the AI is paused; a person is handling it
    CLOSED = "closed"


class SenderType(StrEnum):
    CUSTOMER = "customer"
    AI = "ai"
    HUMAN = "human"  # the business owner or their staff
    SYSTEM = "system"  # internal notes and automated events


class FollowUpStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"
    FAILED = "failed"


class AppointmentStatus(StrEnum):
    PENDING = "pending"  # requested, not yet confirmed by the business
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Level(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
