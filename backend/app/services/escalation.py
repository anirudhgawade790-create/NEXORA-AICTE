from datetime import datetime

from sqlalchemy.orm import Session

import json

from app.models import Application, Escalations, Institution, SystemConfig, User
from app.services.audit import log_action
from app.services.notifications_service import create_notification


def escalate(db: Session, application: Application, level: int, reason: str) -> Escalations | None:
    if level not in (1, 2, 3):
        raise ValueError("Escalation level must be 1, 2 or 3")
    existing = db.query(Escalations).filter(
        Escalations.application_id == application.id,
        Escalations.level == level,
    ).first()
    if existing:
        return existing
    target_role = "regional_officer" if level == 1 else ("bureau_officer" if level == 2 else "admin")
    config_row = db.query(SystemConfig).filter_by(key="escalation_config").first()
    if config_row:
        config = json.loads(config_row.value)
        if level not in config.get("levels", [1, 2, 3]):
            return None
        configured_role = config.get("targets", {}).get(str(level))
        if configured_role in {"regional_officer", "bureau_officer", "admin", "evc_committee"}:
            target_role = configured_role
    query = db.query(User).filter(User.role == target_role, User.is_active.is_(True))
    if target_role == "regional_officer":
        query = query.filter(User.region == application.region)
    target = query.first()
    if target is None:
        target = db.query(User).filter(User.role == "admin", User.is_active.is_(True)).first()
    if target is None:
        return None
    item = Escalations(
        application_id=application.id,
        record_type="application",
        record_id=application.id,
        level=level,
        from_user_id=application.assigned_officer_id or target.id,
        to_user_id=target.id,
        reason=reason,
    )
    db.add(item)
    create_notification(
        db, "escalation", application.id, target.id,
        f"Level {level} escalation: {reason}", application.deadline,
        f"/applications/{application.id}",
    )
    log_action(db, None, "escalation_created", "application", application.id,
               updated_status=f"level_{level}", reason=reason)
    return item


def escalate_record(
    db: Session,
    record_type: str,
    record_id: str | int,
    institution_id: int,
    due_date: datetime | None,
    reason: str,
    level: int,
) -> Escalations | None:
    if record_type not in {"compliance_submission", "undertaking", "document", "evc"}:
        raise ValueError("Unsupported escalation record type")
    if level not in (1, 2, 3):
        raise ValueError("Escalation level must be 1, 2 or 3")

    record_id = str(record_id)
    existing = db.query(Escalations).filter(
        Escalations.record_type == record_type,
        Escalations.record_id == record_id,
        Escalations.level == level,
    ).first()
    if existing:
        return existing

    target_role = {1: "regional_officer", 2: "bureau_officer", 3: "admin"}[level]
    config_row = db.query(SystemConfig).filter_by(key="escalation_config").first()
    config = json.loads(config_row.value) if config_row else {}
    if level not in config.get("levels", [1, 2, 3]):
        return None
    configured_role = config.get("targets", {}).get(str(level))
    if configured_role in {"regional_officer", "bureau_officer", "admin", "evc_committee"}:
        target_role = configured_role

    institution = db.query(Institution).filter_by(id=institution_id).first()
    if institution is None:
        return None
    target_query = db.query(User).filter(User.role == target_role, User.is_active.is_(True))
    if target_role == "regional_officer":
        target_query = target_query.filter(User.region == institution.region)
    target = target_query.order_by(User.id).first()
    if target is None:
        target = db.query(User).filter_by(role="admin", is_active=True).order_by(User.id).first()
    if target is None:
        return None

    source = db.query(User).filter_by(
        institution_id=institution_id,
        role="institution",
        is_active=True,
    ).order_by(User.id).first()
    if source is None:
        source = target
    item = Escalations(
        record_type=record_type,
        record_id=record_id,
        level=level,
        from_user_id=source.id,
        to_user_id=target.id,
        reason=reason,
    )
    db.add(item)
    create_notification(
        db,
        "escalation",
        f"{record_type}:{record_id}",
        target.id,
        f"Level {level} escalation: {reason}",
        due_date,
        "/lease" if record_type == "document" else (
            "/evc" if record_type == "evc" else "/compliance"
        ),
    )
    log_action(
        db,
        None,
        "escalation_created",
        record_type,
        record_id,
        updated_status=f"level_{level}",
        reason=reason,
    )
    return item
