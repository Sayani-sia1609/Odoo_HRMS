"""
Pydantic schemas (request/response models).
"""
from datetime import datetime, date, time
from typing import Optional, List

import re

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.models import RoleEnum, AttendanceStatusEnum, LeaveTypeEnum, LeaveStatusEnum


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
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
    # Only populated when settings.DEV_RETURN_VERIFICATION_TOKEN is True,
    # so the frontend/QA can verify accounts without a real mail server.
    verification_token: Optional[str] = None


class EmailVerifyRequest(BaseModel):
    token: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: RoleEnum
    employee_id: str
    user_id: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class UserOut(BaseModel):
    id: str
    employee_id: str
    email: EmailStr
    role: RoleEnum
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture_url: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    date_of_joining: Optional[date] = None


class ProfileUpdateEmployee(BaseModel):
    """Fields an employee is allowed to edit on their own profile."""
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture_url: Optional[str] = None


class ProfileUpdateAdmin(ProfileBase):
    """Admins may edit every field on any employee's profile."""
    pass


class ProfileOut(ProfileBase):
    id: str
    user_id: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeProfileOut(BaseModel):
    """Combined user + profile view, returned by /profile endpoints."""
    user: UserOut
    profile: Optional[ProfileOut] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
class CheckInRequest(BaseModel):
    # Optional: defaults to server time if not supplied
    check_in_time: Optional[time] = None


class CheckOutRequest(BaseModel):
    check_out_time: Optional[time] = None


class AttendanceOut(BaseModel):
    id: str
    user_id: str
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: AttendanceStatusEnum

    model_config = ConfigDict(from_attributes=True)


class AttendanceManualCreate(BaseModel):
    """Admin can log/override attendance for an employee for a given date."""
    date: date
    status: AttendanceStatusEnum
    check_in: Optional[time] = None
    check_out: Optional[time] = None


# ---------------------------------------------------------------------------
# Leave
# ---------------------------------------------------------------------------
class LeaveApply(BaseModel):
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    remarks: Optional[str] = None


class LeaveDecision(BaseModel):
    status: LeaveStatusEnum = Field(..., description="Must be 'approved' or 'rejected'")
    admin_comment: Optional[str] = None


class LeaveOut(BaseModel):
    id: str
    user_id: str
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    remarks: Optional[str] = None
    status: LeaveStatusEnum
    admin_comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------
class PayrollOut(BaseModel):
    id: str
    user_id: str
    basic_salary: float
    allowances: float
    deductions: float
    net_salary: float
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayrollUpdate(BaseModel):
    basic_salary: Optional[float] = Field(None, ge=0)
    allowances: Optional[float] = Field(None, ge=0)
    deductions: Optional[float] = Field(None, ge=0)
