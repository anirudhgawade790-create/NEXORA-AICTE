"""Authentication, role checks and record-level access helpers."""

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application, User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token") from exc
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User is inactive or no longer exists")
    return user


def require_roles(*roles: str) -> Callable:
    def role_dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return role_dependency


require_admin = require_roles("admin")


def check_application_access(user: User, application: Application) -> None:
    if user.role == "institution" and application.institution_id != user.institution_id:
        raise HTTPException(status_code=403, detail="Application belongs to another institution")
    if user.role == "regional_officer" and application.region != user.region:
        raise HTTPException(status_code=403, detail="Application is outside your region")
    if user.role == "evc_committee" and application.current_stage not in {"evc_scheduling", "evc_completion"}:
        raise HTTPException(status_code=403, detail="Application is outside the EVC queue")


def apply_record_scope(query, user: User, model):
    if user.role == "institution":
        if hasattr(model, "institution_id"):
            return query.filter(model.institution_id == user.institution_id)
        if hasattr(model, "application_id"):
            return query.join(Application, model.application_id == Application.id).filter(
                Application.institution_id == user.institution_id
            )
    if user.role == "regional_officer":
        if hasattr(model, "region"):
            return query.filter(model.region == user.region)
        if hasattr(model, "application_id"):
            return query.join(Application, model.application_id == Application.id).filter(
                Application.region == user.region
            )
    return query
