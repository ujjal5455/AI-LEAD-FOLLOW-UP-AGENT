"""Tenant isolation: one business must never be able to reach another business's data.

The API layer scopes everything to the logged-in user's business, and the database
adds a second line of defence with composite foreign keys. These tests check both.
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text, update
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session

from app.models import Business, Conversation, FollowUp, Lead, User
from app.models.enums import Channel, FollowUpStatus, LeadSource
from tests.conftest import register


def make_business(db: Session, email: str, name: str) -> Business:
    owner = User(email=email, password_hash="not-a-real-hash")
    db.add(owner)
    db.flush()
    business = Business(owner_id=owner.id, name=name)
    db.add(business)
    db.flush()
    return business


def make_lead(db: Session, business: Business, phone: str | None = None) -> Lead:
    lead = Lead(business_id=business.id, source=LeadSource.SIMULATOR, phone=phone)
    db.add(lead)
    db.flush()
    return lead


def test_each_owner_only_sees_their_own_business(app) -> None:
    with TestClient(app) as owner_a, TestClient(app) as owner_b:
        register(owner_a, email="a@example.com", business_name="ABC Interiors")
        register(owner_b, email="b@example.com", business_name="XYZ Dental")

        business_a = owner_a.get("/api/auth/me").json()["business"]
        business_b = owner_b.get("/api/auth/me").json()["business"]

    assert business_a["name"] == "ABC Interiors"
    assert business_b["name"] == "XYZ Dental"
    assert business_a["id"] != business_b["id"]


def test_database_rejects_a_conversation_linking_two_businesses(db: Session) -> None:
    business_a = make_business(db, "a@example.com", "A")
    business_b = make_business(db, "b@example.com", "B")
    lead_of_a = make_lead(db, business_a)

    # Business B's conversation pointing at Business A's lead: must be impossible.
    db.add(Conversation(business_id=business_b.id, lead_id=lead_of_a.id, channel=Channel.SIMULATOR))
    with pytest.raises(IntegrityError, match="fk_conversations_business_id_lead_id_leads"):
        db.flush()


def test_database_rejects_a_followup_linking_two_businesses(db: Session) -> None:
    business_a = make_business(db, "a@example.com", "A")
    business_b = make_business(db, "b@example.com", "B")
    lead_of_a = make_lead(db, business_a)

    db.add(
        FollowUp(
            business_id=business_b.id,
            lead_id=lead_of_a.id,
            scheduled_at=datetime.now(UTC) + timedelta(hours=4),
        )
    )
    with pytest.raises(IntegrityError, match="fk_followups_business_id_lead_id_leads"):
        db.flush()


def test_same_phone_is_one_lead_per_business_but_allowed_across_businesses(db: Session) -> None:
    business_a = make_business(db, "a@example.com", "A")
    business_b = make_business(db, "b@example.com", "B")

    make_lead(db, business_a, phone="+919800000001")
    make_lead(db, business_b, phone="+919800000001")  # different business: fine

    with pytest.raises(IntegrityError, match="uq_leads_business_id_phone"):
        make_lead(db, business_a, phone="+919800000001")


def test_a_lead_can_have_only_one_pending_followup(db: Session) -> None:
    business = make_business(db, "a@example.com", "A")
    lead = make_lead(db, business)
    due = datetime.now(UTC) + timedelta(hours=4)

    db.add(FollowUp(business_id=business.id, lead_id=lead.id, scheduled_at=due))
    db.flush()
    db.add(FollowUp(business_id=business.id, lead_id=lead.id, scheduled_at=due, attempt_number=2))
    with pytest.raises(IntegrityError, match="uq_followups_one_pending_per_lead"):
        db.flush()


def test_a_sent_followup_does_not_block_the_next_one(db: Session) -> None:
    business = make_business(db, "a@example.com", "A")
    lead = make_lead(db, business)
    due = datetime.now(UTC) + timedelta(hours=4)

    db.add(
        FollowUp(
            business_id=business.id, lead_id=lead.id, scheduled_at=due, status=FollowUpStatus.SENT
        )
    )
    db.add(FollowUp(business_id=business.id, lead_id=lead.id, scheduled_at=due, attempt_number=2))
    db.flush()


def test_unknown_status_values_are_rejected_by_python_and_by_the_database(db: Session) -> None:
    business = make_business(db, "a@example.com", "A")
    lead = make_lead(db, business)
    db.commit()

    # Layer 1: SQLAlchemy refuses values outside the enum before sending anything.
    with pytest.raises(StatementError, match="not among the defined enum values"):
        db.execute(update(Lead).where(Lead.id == lead.id).values(status="made_up_status"))
    db.rollback()

    # Layer 2: even raw SQL that skips Python is stopped by the CHECK constraint.
    with pytest.raises(IntegrityError, match="ck_leads_status_allowed"):
        db.execute(
            text("UPDATE leads SET status = 'made_up_status' WHERE id = :id"), {"id": lead.id}
        )
