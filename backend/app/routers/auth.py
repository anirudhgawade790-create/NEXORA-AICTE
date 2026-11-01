from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Institution, User
from app.rate_limit import limiter
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.security import create_access_token, hash_password, verify_password
from app.services.audit import log_action

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
    return TokenResponse(access_token=create_access_token(subject=user.id, role=user.role), user=user)


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


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
