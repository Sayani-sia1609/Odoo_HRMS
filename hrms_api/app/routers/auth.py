"""
Authentication routes: sign up, email verification, login.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User
from app.schemas import (
    UserSignUp,
    UserSignUpResponse,
    EmailVerifyRequest,
    Token,
)
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_verification_token,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _send_verification_email(email: str, token: str) -> None:
    """
    Stub for sending the verification email.

    Wire this up to a real provider (SMTP, SendGrid, SES, etc.) when ready.
    For now it just logs the link so the flow is fully testable end to end.
    """
    print(f"[HRMS] Verification link for {email}: /auth/verify?token={token}")


@router.post("/signup", response_model=UserSignUpResponse, status_code=status.HTTP_201_CREATED)
def sign_up(payload: UserSignUp, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.email == payload.email) | (User.employee_id == payload.employee_id)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email or employee ID already exists",
        )

    token = generate_verification_token()
    user = User(
        employee_id=payload.employee_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_verified=False,
        verification_token=token,
        verification_token_expires=datetime.utcnow()
        + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES),
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email or employee ID already exists",
        )
    db.refresh(user)

    _send_verification_email(user.email, token)

    return UserSignUpResponse(
        message="Signup successful. Please verify your email before logging in.",
        email=user.email,
        verification_token=token if settings.DEV_RETURN_VERIFICATION_TOKEN else None,
    )


@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(payload: EmailVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == payload.token).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")

    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token has expired")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    return {"message": "Email verified successfully. You can now log in."}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm sends the identifier in `username`; we treat
    # that field as the user's email address.
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})

    return Token(
        access_token=access_token,
        role=user.role,
        employee_id=user.employee_id,
        user_id=user.id,
    )
