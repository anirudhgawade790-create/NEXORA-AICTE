from datetime import datetime, timedelta
import json

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Application, ComplianceSubmissions, Documents, EVCAppointments, Escalations, Notifications,
    Institution, SystemConfig, Undertakings, User,
)
from app.services.escalation import escalate, escalate_record
from app.services.expiry import run_expiry_update
from app.services.notifications_service import create_notification

scheduler = BackgroundScheduler(daemon=True)


def run_monitor(db: Session) -> dict[str, int]:
    now = datetime.utcnow()
    reminder_window = now + timedelta(days=3)
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
        ComplianceSubmissions.verification_status != "verified",
    ).all()
    overdue_undertakings = db.query(Undertakings).filter(
        Undertakings.due_date < now, Undertakings.status != "verified",
    ).all()
    new_compliance_escalations = 0
    overdue_records = [
        (item, "compliance_submission", "verification_status")
        for item in overdue_submissions
    ] + [
        (item, "undertaking", "status")
        for item in overdue_undertakings
    ]
    for record, record_type, status_field in overdue_records:
        setattr(record, status_field, "overdue")
        recipient = db.query(User).filter_by(
            institution_id=record.institution_id, role="institution", is_active=True
        ).first()
        related_id = f"{record_type}:{record.id}"
        if recipient and not db.query(Notifications).filter_by(
            recipient_id=recipient.id,
            related_id=related_id,
            event_type="compliance_overdue",
        ).first():
            create_notification(
                db, "compliance_overdue", related_id, recipient.id,
                f"Compliance requirement overdue: {record.description}", record.due_date,
                "/compliance",
            )
        days_overdue = max(0, (now.date() - record.due_date.date()).days)
        for level in configured_levels:
            threshold = 0 if level == 1 else intervals[min(level - 2, len(intervals) - 1)]
            exists = db.query(Escalations).filter_by(
                record_type=record_type,
                record_id=str(record.id),
                level=level,
            ).first()
            if days_overdue >= threshold and not exists:
                escalation = escalate_record(
                    db,
                    record_type,
                    record.id,
                    record.institution_id,
                    record.due_date,
                    f"{record_type.replace('_', ' ').title()} overdue "
                    f"({days_overdue} days): {record.description}",
                    level,
                )
                if escalation:
                    new_compliance_escalations += 1

    expiring_documents = db.query(Documents).filter(
        Documents.status.in_(["expired", "expiring_soon"])
    ).all()
    new_document_escalations = 0
    for document in expiring_documents:
        event_type = "document_expired" if document.status == "expired" else "document_expiring"
        institution_id = document.institution_id
        if institution_id is None and document.application_id:
            application = db.query(Application).filter_by(id=document.application_id).first()
            institution_id = application.institution_id if application else None
        recipient = db.query(User).filter_by(
            institution_id=institution_id, role="institution", is_active=True
        ).order_by(User.id).first() if institution_id else None
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
        if document.status == "expired" and institution_id and document.expiry_date:
            days_overdue = max(0, (now.date() - document.expiry_date.date()).days)
            for level in configured_levels:
                threshold = 0 if level == 1 else intervals[min(level - 2, len(intervals) - 1)]
                exists = db.query(Escalations).filter_by(
                    record_type="document",
                    record_id=str(document.id),
                    level=level,
                ).first()
                if days_overdue >= threshold and not exists:
                    escalation = escalate_record(
                        db,
                        "document",
                        document.id,
                        institution_id,
                        document.expiry_date,
                        f"Document {document.file_name} expired ({days_overdue} days overdue)",
                        level,
                    )
                    if escalation:
                        new_document_escalations += 1

    evc_applications = db.query(Application).filter(
        Application.current_stage.in_(["evc_scheduling", "evc_completion"]),
        Application.status.notin_(["approved", "rejected"]),
    ).all()
    overdue_evc_escalations = 0
    upcoming_evc_reminders = 0
    for application in evc_applications:
        if application.deadline is None:
            continue
        institution_users = db.query(User).filter_by(
            institution_id=application.institution_id,
            role="institution",
            is_active=True,
        ).all()
        officer_users = db.query(User).filter(
            User.id == application.assigned_officer_id,
            User.is_active.is_(True),
        ).all() if application.assigned_officer_id else []
        committee_users = db.query(User).filter_by(
            role="evc_committee",
            is_active=True,
        ).all()
        recipients = {user.id: user for user in institution_users + officer_users + committee_users}

        if now < application.deadline <= reminder_window:
            for recipient in recipients.values():
                related_id = f"application:{application.id}"
                if not db.query(Notifications).filter_by(
                    recipient_id=recipient.id,
                    related_id=related_id,
                    event_type="evc_due_soon",
                ).first():
                    create_notification(
                        db,
                        "evc_due_soon",
                        related_id,
                        recipient.id,
                        f"EVC action for {application.id} is due within 3 days",
                        application.deadline,
                        f"/applications/{application.id}",
                    )
                    upcoming_evc_reminders += 1

        if application.deadline >= now:
            continue

        for recipient in recipients.values():
            related_id = f"application:{application.id}"
            if not db.query(Notifications).filter_by(
                recipient_id=recipient.id,
                related_id=related_id,
                event_type="evc_overdue",
            ).first():
                create_notification(
                    db,
                    "evc_overdue",
                    related_id,
                    recipient.id,
                    f"EVC stage {application.current_stage.replace('_', ' ')} is overdue for {application.id}",
                    application.deadline,
                    f"/applications/{application.id}",
                )

        days_overdue = max(0, (now.date() - application.deadline.date()).days)
        for level in configured_levels:
            threshold = 0 if level == 1 else intervals[min(level - 2, len(intervals) - 1)]
            related_id = f"application:{application.id}"
            exists = db.query(Escalations).filter_by(
                record_type="evc",
                record_id=related_id,
                level=level,
            ).first()
            if days_overdue >= threshold and not exists:
                escalation = escalate_record(
                    db,
                    "evc",
                    related_id,
                    application.institution_id,
                    application.deadline,
                    f"EVC stage {application.current_stage.replace('_', ' ')} overdue "
                    f"({days_overdue} days): {application.id}",
                    level,
                )
                if escalation:
                    overdue_evc_escalations += 1

    scheduled_visits = db.query(EVCAppointments, Application).join(
        Application,
        Application.id == EVCAppointments.application_id,
    ).filter(EVCAppointments.status == "scheduled").all()
    overdue_evc_visits = 0
    for appointment, application in scheduled_visits:
        if application.status in {"approved", "rejected"}:
            continue
        institution_users = db.query(User).filter_by(
            institution_id=application.institution_id,
            role="institution",
            is_active=True,
        ).all()
        committee_users = db.query(User).filter_by(
            role="evc_committee",
            is_active=True,
        ).all()
        recipients = {user.id: user for user in institution_users + committee_users}
        related_id = f"appointment:{appointment.id}"

        if now < appointment.scheduled_date <= reminder_window:
            for recipient in recipients.values():
                if not db.query(Notifications).filter_by(
                    recipient_id=recipient.id,
                    related_id=related_id,
                    event_type="evc_visit_due_soon",
                ).first():
                    create_notification(
                        db,
                        "evc_visit_due_soon",
                        related_id,
                        recipient.id,
                        f"EVC visit for {application.id} is scheduled within 3 days",
                        appointment.scheduled_date,
                        "/evc",
                    )
                    upcoming_evc_reminders += 1

        if appointment.scheduled_date >= now:
            continue
        for recipient in recipients.values():
            if not db.query(Notifications).filter_by(
                recipient_id=recipient.id,
                related_id=related_id,
                event_type="evc_visit_overdue",
            ).first():
                create_notification(
                    db,
                    "evc_visit_overdue",
                    related_id,
                    recipient.id,
                    f"Scheduled EVC visit for {application.id} is overdue for completion",
                    appointment.scheduled_date,
                    "/evc",
                )

        days_overdue = max(0, (now.date() - appointment.scheduled_date.date()).days)
        for level in configured_levels:
            threshold = 0 if level == 1 else intervals[min(level - 2, len(intervals) - 1)]
            exists = db.query(Escalations).filter_by(
                record_type="evc",
                record_id=related_id,
                level=level,
            ).first()
            if days_overdue >= threshold and not exists:
                escalation = escalate_record(
                    db,
                    "evc",
                    related_id,
                    application.institution_id,
                    appointment.scheduled_date,
                    f"Scheduled EVC visit overdue for completion "
                    f"({days_overdue} days): {application.id}",
                    level,
                )
                if escalation:
                    overdue_evc_visits += 1
    db.commit()
    return {"overdue_applications": len(overdue_apps), "new_escalations": alerts,
            "overdue_compliance": len(overdue_submissions) + len(overdue_undertakings),
            "new_compliance_escalations": new_compliance_escalations,
            "new_document_escalations": new_document_escalations,
            "overdue_evc_escalations": overdue_evc_escalations,
            "overdue_evc_visits": overdue_evc_visits,
            "upcoming_evc_reminders": upcoming_evc_reminders}


def scheduled_monitor() -> None:
    db = SessionLocal()
    try:
        run_monitor(db)
    finally:
        db.close()
