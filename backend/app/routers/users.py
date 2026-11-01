from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models import User
from app.schemas.auth import UserOut
from app.schemas.users import UserCreate, UserUpdate
from app.deps import get_current_user
from app.security import hash_password
from app.services.audit import log_action

router = APIRouter(prefix="/api/users", tags=["users"])
VALID_ROLES = {"institution", "regional_officer", "bureau_officer", "evc_committee", "admin"}


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.get("", response_model=list[UserOut])
def list_users(
    role: str | None = None,
    region: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if region:
        query = query.filter(User.region == region)
    return query.order_by(User.id).offset(offset).limit(limit).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported user role")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(
        email=payload.email, full_name=payload.full_name, role=payload.role,
        region=payload.region, institution_id=payload.institution_id,
        password_hash=hash_password(payload.password), is_active=True,
    )
    db.add(user)
    db.flush()
    log_action(db, admin, "user_created", "user", user.id)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db),
                admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role and payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported user role")
    previous = user.role
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    log_action(db, admin, "user_updated", "user", user.id, previous, user.role)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    user.is_active = False
    log_action(db, admin, "user_deactivated", "user", user.id, "active", "inactive")
    db.commit()
