from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Notifications, User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    unread_only: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Notifications).filter_by(recipient_id=user.id)
    if unread_only:
        query = query.filter(Notifications.is_read.is_(False))
    return query.order_by(Notifications.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(Notifications).filter_by(recipient_id=user.id, is_read=False).count()
    return {"count": count}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    item = db.query(Notifications).filter_by(id=notification_id, recipient_id=user.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    item.is_read = True
    db.commit()
    return {"id": item.id, "is_read": item.is_read}


@router.get("/config")
def notification_config(user: User = Depends(get_current_user)):
    from app.config import settings
    configured = bool(settings.SMTP_HOST and (settings.SMTP_FROM or settings.SMTP_USER))
    return {"email_configured": configured,
            "email_status": "configured" if configured else "unconfigured"}
