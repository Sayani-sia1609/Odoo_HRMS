"""
Authentication routes: sign up, email verification, login.

Covers PRD 3.1:
- 3.1.1 Sign Up: employee_id, email, password, role; password rules;
  email verification required before login.
- 3.1.2 Sign In: email + password; clear error messages on bad
  credentials; returns a token the frontend uses to reach the dashboard.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import auth_settings
from .database import get_db
from .dependencies import get_current_user, oauth2_scheme
from .models import RevokedToken, User
from .schemas import (
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    UserLogin,
    UserSignUp,
    UserSignUpResponse,
    EmailVerifyRequest,
    Token,
    UserOut,
)
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_verification_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_verification_link(token: str) -> str:
    separator = "&" if "?" in auth_settings.FRONTEND_VERIFY_URL else "?"
    return f"{auth_settings.FRONTEND_VERIFY_URL}{separator}token={token}"


def _send_verification_email(email: str, token: str) -> None:
    """
    Stub for sending the verification email.

    Wire this up to a real provider (SMTP, SendGrid, SES, etc.) later.
    For the hackathon, it just prints the link so the flow is fully
    testable end to end without a mail server.
    """
    print(f"[AUTH] Verification link for {email}: {_build_verification_link(token)}")


def _authenticate_user(email: str, password: str, db: Session) -> User:
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
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

    return user


def _issue_access_token(user: User) -> Token:
    access_expires_delta = timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires_delta = timedelta(days=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value},
        expires_delta=access_expires_delta,
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "role": user.role.value},
        expires_delta=refresh_expires_delta,
    )
    return Token(
        access_token=access_token,
        expires_in=int(access_expires_delta.total_seconds()),
        refresh_token=refresh_token,
        refresh_expires_in=int(refresh_expires_delta.total_seconds()),
        role=user.role,
        employee_id=user.employee_id,
        user_id=user.id,
    )


def _revoke_token(token: str, expected_type: str, db: Session) -> None:
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    token_type = payload.get("type")
    token_jti = payload.get("jti")
    user_id = payload.get("sub")
    exp_ts = payload.get("exp")

    if token_type != expected_type or token_jti is None or user_id is None or exp_ts is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    existing = db.query(RevokedToken).filter(RevokedToken.jti == token_jti).first()
    if existing is not None:
        return

    db.add(
        RevokedToken(
            jti=token_jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).replace(tzinfo=None),
        )
    )


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
        + timedelta(minutes=auth_settings.EMAIL_VERIFICATION_EXPIRE_MINUTES),
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
        verification_token=token if auth_settings.DEV_RETURN_VERIFICATION_TOKEN else None,
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


@router.get("/verify-email", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def verify_email_from_link(token: str = Query(...), db: Session = Depends(get_db)):
    return verify_email(EmailVerifyRequest(token=token), db)


@router.post("/resend-verification", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Avoid user enumeration by always returning success-style messaging.
        return MessageResponse(message="If your account exists, a verification email has been sent")

    if user.is_verified:
        return MessageResponse(message="Email is already verified")

    token = generate_verification_token()
    user.verification_token = token
    user.verification_token_expires = datetime.utcnow() + timedelta(
        minutes=auth_settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
    )
    db.commit()

    _send_verification_email(user.email, token)
    return MessageResponse(message="If your account exists, a verification email has been sent")


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm sends the identifier in `username`.
    user = _authenticate_user(form_data.username, form_data.password, db)
    return _issue_access_token(user)


@router.post("/login/json", response_model=Token)
def login_json(payload: UserLogin, db: Session = Depends(get_db)):
    user = _authenticate_user(payload.email, payload.password, db)
    return _issue_access_token(user)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    refresh_payload = decode_token(payload.refresh_token)
    if refresh_payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if refresh_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    refresh_jti = refresh_payload.get("jti")
    user_id = refresh_payload.get("sub")
    if refresh_jti is None or user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    is_revoked = db.query(RevokedToken).filter(RevokedToken.jti == refresh_jti).first()
    if is_revoked is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Rotate refresh token by revoking the old one and issuing a new pair.
    _revoke_token(payload.refresh_token, expected_type="refresh", db=db)
    db.commit()
    return _issue_access_token(user)


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def logout(
    payload: LogoutRequest,
    access_token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    refresh_payload = decode_token(payload.refresh_token)
    if refresh_payload is None or refresh_payload.get("sub") != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    _revoke_token(access_token, expected_type="access", db=db)
    _revoke_token(payload.refresh_token, expected_type="refresh", db=db)
    db.commit()

    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def me(current_user: User = Depends(get_current_user)):
    return current_user
