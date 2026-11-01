from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import AuditLogs, User

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(
    user_id: int | None = None,
    record_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(AuditLogs)
    if user.role not in {"admin", "bureau_officer"}:
        query = query.filter(AuditLogs.user_id == user.id)
    if user_id is not None and user.role in {"admin", "bureau_officer"}:
        query = query.filter(AuditLogs.user_id == user_id)
    if record_type:
        query = query.filter(AuditLogs.affected_record_type == record_type)
    if start_date:
        query = query.filter(AuditLogs.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLogs.timestamp <= end_date)
    return query.order_by(AuditLogs.timestamp.desc()).offset(offset).limit(limit).all()
