import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.deps import require_admin
from app.models import DocumentCategory, Documents, SystemConfig, User
from app.services.audit import log_action
from app.services.scheduler import run_monitor

router = APIRouter(prefix="/api/admin", tags=["admin"])


class EscalationConfig(BaseModel):
    levels: list[int] = Field(default_factory=lambda: [1, 2, 3], min_length=1)
    intervals: list[int] = Field(default_factory=lambda: [7, 14, 30], min_length=1)
    targets: dict[str, str] = Field(default_factory=dict)


@router.get("/config")
def get_config(admin: User = Depends(require_admin)):
    from app.config import settings
    return {"email_configured": bool(settings.SMTP_HOST), "email_status": "configured" if settings.SMTP_HOST else "unconfigured"}


@router.post("/reset-demo-data")
def reset_demo_data(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    db.close()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.seed import seed_demo_data
    replacement = SessionLocal()
    try:
        seed_demo_data(replacement)
        counts = {
            "users": replacement.query(User).count(),
            "applications": replacement.query(__import__("app.models", fromlist=["Application"]).Application).count(),
        }
        log_action(replacement, None, "demo_data_reset", "system", "demo", updated_status="seeded")
        replacement.commit()
        return counts
    finally:
        replacement.close()


@router.get("/document-categories")
def categories(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(DocumentCategory).order_by(DocumentCategory.name).all()


@router.post("/document-categories", status_code=201)
def add_category(payload: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    name = str(payload.get("name", "")).strip()
    if not name or len(name) > 100:
        raise HTTPException(status_code=400, detail="Category name is required")
    if db.query(DocumentCategory).filter_by(name=name).first():
        raise HTTPException(status_code=409, detail="Category already exists")
    item = DocumentCategory(name=name)
    db.add(item)
    db.flush()
    log_action(db, admin, "category_created", "document_category", item.id)
    db.commit()
    return item


@router.get("/reminder-intervals")
def get_intervals(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from app.services.expiry import reminder_intervals
    return {"intervals": reminder_intervals(db), "note": "Prototype reminder windows; not official AICTE requirements"}


@router.put("/reminder-intervals")
def set_intervals(payload: list[int], db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not payload or any(value <= 0 or value > 3650 for value in payload):
        raise HTTPException(status_code=400, detail="Reminder intervals must be between 1 and 3650 days")
    item = db.query(SystemConfig).filter_by(key="reminder_intervals").first()
    value = ",".join(str(day) for day in sorted(set(payload), reverse=True))
    if item is None:
        item = SystemConfig(key="reminder_intervals", value=value)
        db.add(item)
    else:
        item.value = value
    log_action(db, admin, "reminder_intervals_updated", "system_config", "reminder_intervals")
    db.commit()
    return {"intervals": [int(day) for day in value.split(",")]}


@router.put("/document-categories/{category_id}")
def update_category(category_id: int, payload: dict, db: Session = Depends(get_db),
                    admin: User = Depends(require_admin)):
    item = db.query(DocumentCategory).filter_by(id=category_id).first()
    name = str(payload.get("name", "")).strip()
    if item is None:
        raise HTTPException(status_code=404, detail="Document category not found")
    if not name or len(name) > 100:
        raise HTTPException(status_code=400, detail="Category name is required")
    duplicate = db.query(DocumentCategory).filter(
        DocumentCategory.name == name, DocumentCategory.id != category_id
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Category already exists")
    item.name = name
    log_action(db, admin, "category_updated", "document_category", item.id)
    db.commit()
    return item


@router.delete("/document-categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db),
                    admin: User = Depends(require_admin)):
    item = db.query(DocumentCategory).filter_by(id=category_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Document category not found")
    if db.query(Documents).filter_by(category=item.name).first():
        raise HTTPException(status_code=409, detail="Category is in use by existing documents")
    log_action(db, admin, "category_deleted", "document_category", item.id,
               reason=item.name)
    db.delete(item)
    db.commit()


@router.get("/escalation-config")
def get_escalation_config(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    item = db.query(SystemConfig).filter_by(key="escalation_config").first()
    return {"levels": [1, 2, 3], "intervals": [7, 14, 30], "targets": {}} if item is None else json.loads(item.value)


@router.put("/escalation-config")
def set_escalation_config(payload: EscalationConfig, db: Session = Depends(get_db),
                          admin: User = Depends(require_admin)):
    if any(level not in (1, 2, 3) for level in payload.levels):
        raise HTTPException(status_code=400, detail="Escalation levels must be 1, 2 or 3")
    if any(day < 1 or day > 3650 for day in payload.intervals):
        raise HTTPException(status_code=400, detail="Escalation intervals must be between 1 and 3650 days")
    value = payload.model_dump_json()
    item = db.query(SystemConfig).filter_by(key="escalation_config").first()
    if item is None:
        item = SystemConfig(key="escalation_config", value=value)
        db.add(item)
    else:
        item.value = value
    log_action(db, admin, "escalation_config_updated", "system_config", "escalation_config")
    db.commit()
    return payload


@router.post("/run-monitor")
def monitor(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return run_monitor(db)
