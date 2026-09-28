"""Shapes of the data the auth endpoints accept and return.

Incoming data is validated here before any code touches it: wrong types, missing
fields or out-of-range values are rejected with a 422 response automatically.
"""

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
BusinessName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
# Passwords are taken exactly as typed (no trimming). The upper bound stops someone
# from sending megabytes of "password" to make hashing slow.
NewPassword = Annotated[str, Field(min_length=8, max_length=128)]


class _EmailLowercase(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def lowercase(cls, value: str) -> str:
        return value.lower()


class RegisterRequest(_EmailLowercase):
    full_name: Name
    business_name: BusinessName
    password: NewPassword


class LoginRequest(_EmailLowercase):
    password: Annotated[str, Field(min_length=1, max_length=128)]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None


class BusinessSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    industry: str | None
    timezone: str


class SessionOut(BaseModel):
    """Who is logged in, and which business (tenant) they are working in."""

    user: UserOut
    business: BusinessSummary
