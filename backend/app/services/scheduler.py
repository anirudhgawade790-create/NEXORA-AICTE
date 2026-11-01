from datetime import datetime
import json

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Application, ComplianceSubmissions, Documents, Escalations, Notifications,
    SystemConfig, Undertakings, User,
)
from app.services.escalation import escalate
from app.services.expiry import run_expiry_update
from app.services.notifications_service import create_notification

scheduler = BackgroundScheduler(daemon=True)


def run_monitor(db: Session) -> dict[str, int]:
    now = datetime.utcnow()
    run_expiry_update(db)
    config_row = db.query(SystemConfig).filter_by(key="escalation_config").first()
    config = json.loads(config_row.value) if config_row else {}
    configured_levels = config.get("levels", [1, 2, 3])
    intervals = config.get("intervals", [7, 14, 30])
    overdue_apps = db.query(Application).filter(
        Application.deadline < now,
        Application.status.notin_(["approved", "rejected"]),
    ).all()
    alerts = 0
    for application in overdue_apps:
        days_overdue = (now.date() - application.deadline.date()).days if application.deadline else 0
        for level in configured_levels:
            threshold = 0 if level == 1 else intervals[min(level - 2, len(intervals) - 1)]
            exists = db.query(Escalations).filter_by(
                application_id=application.id, level=level
            ).first()
            if days_overdue >= threshold and not exists:
                if escalate(db, application, level, f"Application deadline passed ({days_overdue} days overdue)"):
                    alerts += 1
        recipient = application.assigned_officer_id
        if recipient:
            exists = db.query(Notifications).filter_by(
                recipient_id=recipient, related_id=application.id, event_type="overdue",
            ).first()
            if not exists:
                create_notification(
                    db, "overdue", application.id, recipient,
                    f"Application {application.id} is overdue", application.deadline,
                    f"/applications/{application.id}",
                )
    overdue_submissions = db.query(ComplianceSubmissions).filter(
        ComplianceSubmissions.due_date < now,
        ComplianceSubmissions.verification_status.notin_(["verified", "overdue"]),
    ).all()
    overdue_undertakings = db.query(Undertakings).filter(
        Undertakings.due_date < now, Undertakings.status.notin_(["verified", "overdue"]),
    ).all()
    for record in overdue_submissions:
        record.verification_status = "overdue"
        recipient = db.query(User).filter_by(
            institution_id=record.institution_id, role="institution", is_active=True
        ).first()
        if recipient:
            create_notification(
                db, "compliance_overdue", record.id, recipient.id,
                f"Compliance item {record.id} is overdue", record.due_date,
            )
    for record in overdue_undertakings:
        record.status = "overdue"
        recipient = db.query(User).filter_by(
            institution_id=record.institution_id, role="institution", is_active=True
        ).first()
        if recipient:
            create_notification(
                db, "compliance_overdue", record.id, recipient.id,
                f"Undertaking {record.id} is overdue", record.due_date,
            )
    expiring_documents = db.query(Documents).filter(
        Documents.status.in_(["expired", "expiring_soon"])
    ).all()
    for document in expiring_documents:
        event_type = "document_expired" if document.status == "expired" else "document_expiring"
        recipient = db.query(User).filter_by(
            institution_id=document.institution_id, role="institution", is_active=True
        ).first()
        exists = db.query(Notifications).filter_by(
            event_type=event_type, related_id=str(document.id),
            recipient_id=recipient.id if recipient else -1,
        ).first() if recipient else None
        if recipient and not exists:
            create_notification(
                db, event_type, document.id, recipient.id,
                f"{document.file_name} is {document.status.replace('_', ' ')}",
                document.expiry_date, "/lease",
            )
    db.commit()
    return {"overdue_applications": len(overdue_apps), "new_escalations": alerts,
            "overdue_compliance": len(overdue_submissions) + len(overdue_undertakings)}


def scheduled_monitor() -> None:
    db = SessionLocal()
    try:
        run_monitor(db)
    finally:
        db.close()
