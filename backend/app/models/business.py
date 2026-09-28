import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Business(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A tenant. Every lead, conversation, message, follow-up and appointment belongs
    to exactly one business, and one business can never see another's data."""

    __tablename__ = "businesses"

    # Unique: one business per owner account in the MVP (team accounts come later).
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(64))
    timezone: Mapped[str] = mapped_column(
        String(64), default="Asia/Kolkata", server_default="Asia/Kolkata"
    )
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(320))

    # The business facts the AI reads instead of inventing them. The exact shape of
    # each field is validated by the API when the owner edits their profile.
    business_hours: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    services: Mapped[list[Any]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    service_area: Mapped[list[Any]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    pricing_information: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    ai_instructions: Mapped[str | None] = mapped_column(Text)
