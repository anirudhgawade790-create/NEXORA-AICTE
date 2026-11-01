from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.deps import check_application_access
from app.models import Application, ApplicationStage, User, WorkflowRules
from app.services.audit import log_action
from app.services.notifications_service import create_notification

FINAL_STATUSES = {"approved", "rejected"}


def ordered_rules(db: Session) -> list[WorkflowRules]:
    return db.query(WorkflowRules).filter(WorkflowRules.is_active.is_(True)).order_by(
        WorkflowRules.stage_order
    ).all()


def next_rule(rules: list[WorkflowRules], current: WorkflowRules) -> WorkflowRules | None:
    for candidate in rules:
        if candidate.stage_order <= current.stage_order:
            continue
        if candidate.stage_key in {"initial_scrutiny", "deficiency_check"} and not candidate.requires_scrutiny:
            continue
        if candidate.stage_key in {"evc_scheduling", "evc_completion"} and not candidate.requires_evc:
            continue
        if candidate.stage_key == "committee_stage" and not candidate.requires_committee:
            continue
        return candidate
    return None


def transition(db: Session, application: Application, action: str, user: User, reason: str | None):
    check_application_access(user, application)
    if action not in {"forward", "return", "reject", "resubmit", "complete"}:
        raise HTTPException(status_code=400, detail="Unsupported workflow action")
    if action in {"return", "reject"} and not (reason and reason.strip()):
        raise HTTPException(status_code=400, detail="A reason is required")
    if application.status in FINAL_STATUSES:
        raise HTTPException(status_code=409, detail="Final applications cannot be reopened")
    if action == "resubmit":
        if user.role != "institution" or application.institution_id != user.institution_id:
            raise HTTPException(status_code=403, detail="Only the owning institution may resubmit")
        if application.status != "returned":
            raise HTTPException(status_code=409, detail="Application is not awaiting resubmission")
        target = next((rule for rule in ordered_rules(db) if rule.stage_key == "initial_scrutiny"), None)
        if target is None:
            raise HTTPException(status_code=409, detail="Initial scrutiny stage is not configured")
        new_status = "pending"
    else:
        rules = ordered_rules(db)
        current_rule = next((rule for rule in rules if rule.stage_key == application.current_stage), None)
        if current_rule is None:
            raise HTTPException(status_code=409, detail="Current workflow stage is not configured")
        allowed = {role.strip() for role in current_rule.allowed_roles.split(",")}
        if action in {"forward", "complete"} and user.role not in allowed:
            raise HTTPException(status_code=403, detail="Role cannot advance this stage")
        if action in {"return", "reject"} and user.role not in {
            "regional_officer", "bureau_officer", "admin"
        }:
            raise HTTPException(status_code=403, detail="Role cannot return or reject applications")
        if action == "return":
            target, new_status = current_rule, "returned"
        elif action == "reject":
            target, new_status = current_rule, "rejected"
        else:
            target = next_rule(rules, current_rule)
            if target is None:
                target, new_status = current_rule, "approved"
            else:
                new_status = "pending"

    previous_status = application.status
    now = datetime.utcnow()
    active_stage = db.query(ApplicationStage).filter(
        ApplicationStage.application_id == application.id,
        ApplicationStage.status == "active",
    ).order_by(ApplicationStage.entered_at.desc()).first()
    if active_stage:
        active_stage.exited_at = now
        active_stage.status = "returned" if action == "return" else "completed"
    application.current_stage = target.stage_key
    application.status = new_status
    application.updated_at = now
    application.deadline = (
        now + timedelta(days=target.deadline_days)
        if target.deadline_days is not None
        else None
    )
    db.add(ApplicationStage(
        application_id=application.id,
        stage_key=target.stage_key,
        stage_name=target.stage_name,
        entered_at=now,
        status="active" if new_status not in FINAL_STATUSES else "completed",
        actor_user_id=user.id,
        reason=reason,
    ))
    log_action(
        db, user, f"application_{action}", "application", application.id,
        previous_status, new_status, reason, target.stage_key,
    )
    create_notification(
        db, "stage_change", application.id, application.assigned_officer_id or user.id,
        f"Application {application.id} moved to {target.stage_name}",
        application.deadline, f"/applications/{application.id}",
    )
    if application.institution_id:
        institution_user = db.query(User).filter(
            User.institution_id == application.institution_id,
            User.role == "institution",
            User.is_active.is_(True),
        ).first()
        if institution_user and institution_user.id != user.id:
            create_notification(
                db, "deficiency" if action == "return" else "stage_change",
                application.id, institution_user.id,
                reason if action == "return" else f"Application moved to {target.stage_name}",
                application.deadline, f"/applications/{application.id}",
            )
    db.commit()
    db.refresh(application)
    return application
