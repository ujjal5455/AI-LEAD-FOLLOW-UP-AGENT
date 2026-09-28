"""All database models. Importing this package registers every table with `Base.metadata`,
which is what Alembic compares against the database when generating migrations."""

from app.models.appointment import Appointment
from app.models.base import Base
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.message import Message
from app.models.user import User

__all__ = [
    "Appointment",
    "Base",
    "Business",
    "Conversation",
    "FollowUp",
    "Lead",
    "Message",
    "User",
]
