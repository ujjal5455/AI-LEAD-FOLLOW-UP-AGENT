"""Reusable request dependencies.

FastAPI runs these before an endpoint and hands it the result. `CurrentBusiness` is
the heart of tenant isolation: endpoints get the business from the logged-in user's
session, never from anything the caller sends, so nobody can ask for another
business's data by changing an ID in the request.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ACCESS_TOKEN_COOKIE, decode_access_token
from app.models import Business, User
from app.services.auth_service import get_business_for_owner

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, db: DbSession) -> User:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    user_id = decode_access_token(token) if token else None
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_business(user: CurrentUser, db: DbSession) -> Business:
    business = get_business_for_owner(db, user.id)
    if business is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No business is linked to this account")
    return business


CurrentBusiness = Annotated[Business, Depends(get_current_business)]
