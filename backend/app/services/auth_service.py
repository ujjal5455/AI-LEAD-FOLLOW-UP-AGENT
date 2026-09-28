"""Account business logic: sign-up and login. Kept separate from the HTTP layer so
it can be reused (e.g. by a seed script) and tested directly."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, spend_equivalent_verify_time, verify_password
from app.models import Business, User
from app.schemas.auth import RegisterRequest


class EmailAlreadyRegisteredError(Exception):
    pass


def register_owner(db: Session, data: RegisterRequest) -> tuple[User, Business]:
    """Create an owner account together with their business, in one transaction."""
    if db.scalar(select(User.id).where(User.email == data.email)) is not None:
        raise EmailAlreadyRegisteredError

    user = User(
        email=data.email, password_hash=hash_password(data.password), full_name=data.full_name
    )
    try:
        db.add(user)
        db.flush()  # assigns user.id
        business = Business(owner_id=user.id, name=data.business_name)
        db.add(business)
        db.commit()
    except IntegrityError as exc:
        # Two sign-ups with the same email at the same instant: the database's unique
        # constraint lets exactly one of them through.
        db.rollback()
        raise EmailAlreadyRegisteredError from exc
    return user, business


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Return the user if the email and password are correct, otherwise None."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        spend_equivalent_verify_time(password)
        return None

    is_valid, new_hash = verify_password(password, user.password_hash)
    if not is_valid or not user.is_active:
        return None
    if new_hash is not None:
        # Hashing settings were upgraded since this password was saved.
        user.password_hash = new_hash
        db.commit()
    return user


def get_business_for_owner(db: Session, owner_id: uuid.UUID) -> Business | None:
    return db.scalar(select(Business).where(Business.owner_id == owner_id))
