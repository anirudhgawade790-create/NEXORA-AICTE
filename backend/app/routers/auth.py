from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
import smtplib
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Institution, PasswordResetToken, User
from app.rate_limit import enforce_password_reset_email_limit, limiter
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.security import create_access_token, hash_password, verify_password
from app.services.audit import log_action
from app.services.password_reset_email import send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)
PASSWORD_RESET_TOKEN_LIFETIME = timedelta(minutes=30)
PASSWORD_RESET_REQUEST_MESSAGE = (
    "If an active account matches that email, password reset instructions will be sent."
)


@router.get("/institutions")
def list_institutions(db: Session = Depends(get_db)):
    return db.query(Institution).order_by(Institution.name).all()


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    log_action(db, user, "login", "user", user.id)
    db.commit()
    return TokenResponse(
        access_token=create_access_token(
            subject=user.id,
            role=user.role,
            token_version=user.token_version,
        ),
        user=user,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    if payload.institution_id is None or db.query(Institution).filter(
        Institution.id == payload.institution_id
    ).first() is None:
        raise HTTPException(status_code=400, detail="A valid institution_id is required")
    institution = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role="institution",
        region=payload.region or institution.region,
        institution_id=payload.institution_id,
        is_active=False,
    )
    db.add(user)
    db.flush()
    log_action(db, user, "registration_pending", "user", user.id)
    db.commit()
    db.refresh(user)
    return user


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("20/hour")
def forgot_password(payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    from app.config import settings

    enforce_password_reset_email_limit(request, str(payload.email))

    if not settings.SMTP_HOST or not (settings.SMTP_FROM or settings.SMTP_USER):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password recovery email is not configured. Contact your administrator.",
        )

    user = db.query(User).filter(User.email == payload.email, User.is_active.is_(True)).first()
    if user is not None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).update({"used_at": now}, synchronize_session=False)

        reset_token = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(reset_token.encode("utf-8")).hexdigest(),
            expires_at=now + PASSWORD_RESET_TOKEN_LIFETIME,
        ))
        db.commit()
        reset_url = (
            f"{settings.FRONTEND_BASE_URL.rstrip('/')}/reset-password?"
            f"{urlencode({'token': reset_token})}"
        )
        try:
            send_password_reset_email(user.email, reset_url)
        except (OSError, ValueError, RuntimeError, smtplib.SMTPException) as exc:
            logger.error("Password reset email delivery failed: %s", exc)

    return {"message": PASSWORD_RESET_REQUEST_MESSAGE}


@router.post("/reset-password")
@limiter.limit("5/hour")
def reset_password(
    payload: PasswordResetConfirmRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .with_for_update()
        .first()
    )
    if reset_token is None:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset link")

    user = db.query(User).filter(User.id == reset_token.user_id, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset link")

    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": now}, synchronize_session=False)
    log_action(db, user, "password_reset", "user", user.id)
    db.commit()
    return {"message": "Password updated. You can now sign in with your new password."}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
