"""Sign-up, login, logout and "who am I".

After a successful sign-up or login, the backend puts the login token in an
httpOnly cookie. The browser sends that cookie back automatically on every request,
and page JavaScript can't read it, so a malicious script can't steal the token.
SameSite=Lax stops other websites from making requests with it (CSRF protection).
"""

import logging

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import CurrentBusiness, CurrentUser, DbSession
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.core.security import ACCESS_TOKEN_COOKIE, create_access_token
from app.schemas.auth import (
    BusinessSummary,
    LoginRequest,
    RegisterRequest,
    SessionOut,
    UserOut,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest, request: Request, response: Response, db: DbSession
) -> SessionOut:
    limiter: RateLimiter = request.app.state.register_limiter
    ip = _client_ip(request)
    if limiter.is_limited(ip):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many sign-ups. Please try again later."
        )
    limiter.record(ip)

    try:
        user, business = auth_service.register_owner(db, data)
    except auth_service.EmailAlreadyRegisteredError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with this email already exists."
        ) from None

    _set_session_cookie(response, create_access_token(user.id))
    logger.info("Registered user %s with business %s", user.id, business.id)
    return SessionOut(
        user=UserOut.model_validate(user), business=BusinessSummary.model_validate(business)
    )


@router.post("/login")
def login(data: LoginRequest, request: Request, response: Response, db: DbSession) -> SessionOut:
    # Limit failed attempts per account, which slows down password guessing.
    limiter: RateLimiter = request.app.state.login_limiter
    if limiter.is_limited(data.email):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed login attempts. Please wait a few minutes and try again.",
        )

    user = auth_service.authenticate(db, data.email, data.password)
    if user is None:
        limiter.record(data.email)
        # Same message for "no such account" and "wrong password", so the response
        # doesn't reveal which emails have accounts.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    limiter.reset(data.email)

    business = auth_service.get_business_for_owner(db, user.id)
    if business is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No business is linked to this account")

    _set_session_cookie(response, create_access_token(user.id))
    logger.info("User %s logged in", user.id)
    return SessionOut(
        user=UserOut.model_validate(user), business=BusinessSummary.model_validate(business)
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(
        ACCESS_TOKEN_COOKIE,
        path="/",
        httponly=True,
        secure=get_settings().is_production,
        samesite="lax",
    )


@router.get("/me")
def me(user: CurrentUser, business: CurrentBusiness) -> SessionOut:
    return SessionOut(
        user=UserOut.model_validate(user), business=BusinessSummary.model_validate(business)
    )
