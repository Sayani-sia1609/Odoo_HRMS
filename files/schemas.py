"""
Request/response models for the auth module.

Password rule (PRD 3.1.1 "Password must follow security rules"):
at least 8 chars, one uppercase, one lowercase, one digit, one special char.
"""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from .models import RoleEnum


class UserSignUp(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: RoleEnum = RoleEnum.employee

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:,.<>?/\\|~`]", value):
            raise ValueError("Password must contain at least one special character")
        return value


class UserSignUpResponse(BaseModel):
    message: str
    email: EmailStr
    # Only populated when auth_settings.DEV_RETURN_VERIFICATION_TOKEN is True.
    verification_token: Optional[str] = None


class EmailVerifyRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    role: RoleEnum
    employee_id: str
    user_id: str


class MessageResponse(BaseModel):
    message: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    employee_id: str
    email: EmailStr
    role: RoleEnum
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
