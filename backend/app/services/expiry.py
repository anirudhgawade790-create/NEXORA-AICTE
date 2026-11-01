from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Documents, SystemConfig


def reminder_intervals(db: Session) -> list[int]:
    config = db.query(SystemConfig).filter(SystemConfig.key == "reminder_intervals").first()
    if not config:
        return [90, 60, 30, 7]
    try:
        values = [int(value) for value in config.value.split(",") if int(value) > 0]
    except ValueError:
        return [90, 60, 30, 7]
    return values or [90, 60, 30, 7]


def compute_document_status(document: Documents, intervals: list[int]) -> tuple[str, int | None]:
    if document.expiry_date is None:
        return document.status, None
    days = (document.expiry_date.date() - datetime.utcnow().date()).days
    if days < 0:
        return "expired", days
    if days <= max(intervals, default=0):
        return "expiring_soon", days
    if document.status in {"expired", "expiring_soon"}:
        return ("verified" if document.verified_at else "under_verification"), days
    return document.status, days


def run_expiry_update(db: Session) -> int:
    intervals = reminder_intervals(db)
    updated = 0
    for document in db.query(Documents).filter(Documents.expiry_date.is_not(None)).all():
        status, _ = compute_document_status(document, intervals)
        if status in {"expired", "expiring_soon"} and document.status != status:
            document.status = status
            updated += 1
        elif status not in {"expired", "expiring_soon"} and document.status in {"expired", "expiring_soon"}:
            document.status = "verified" if document.verified_at else "under_verification"
            updated += 1
    db.commit()
    return updated
