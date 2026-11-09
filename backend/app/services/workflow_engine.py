from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.aph_rules import APH_RULES, APH_WORKFLOW_PATHS
from app.deps import check_application_access
from app.models import (
    Application, ApplicationStage, DeficiencyCompliance, Documents, EVCAppointments,
    ScrutinyObservations, User, WorkflowRules,
)
from app.services.audit import log_action
from app.services.notifications_service import create_notification
from app.workflow_paths import DEFAULT_WORKFLOW_PATH, WORKFLOW_PATHS

FINAL_STATUSES = {"approved", "rejected"}


def ordered_rules(db: Session) -> list[WorkflowRules]:
    return db.query(WorkflowRules).filter(WorkflowRules.is_active.is_(True)).order_by(
        WorkflowRules.stage_order
    ).all()


def unresolved_deficiencies(db: Session, application: Application) -> list[ScrutinyObservations]:
    observations = db.query(ScrutinyObservations).filter_by(
        application_id=application.id, is_deficiency=True
    ).order_by(ScrutinyObservations.created_at, ScrutinyObservations.id).all()
    unresolved = []
    for observation in observations:
        latest = db.query(DeficiencyCompliance).filter_by(
            observation_id=observation.id
        ).order_by(DeficiencyCompliance.submitted_at.desc(), DeficiencyCompliance.id.desc()).first()
        if latest is None or latest.status != "verified":
            unresolved.append(observation)
    return unresolved


def latest_deficiency_compliance(db: Session, observation_id: int) -> DeficiencyCompliance | None:
    return db.query(DeficiencyCompliance).filter_by(
        observation_id=observation_id
    ).order_by(DeficiencyCompliance.submitted_at.desc(), DeficiencyCompliance.id.desc()).first()


def next_rule(
    rules: list[WorkflowRules],
    current: WorkflowRules,
    workflow_path: str = DEFAULT_WORKFLOW_PATH,
    application: Application | None = None,
    db: Session | None = None,
) -> WorkflowRules | None:
    path = APH_WORKFLOW_PATHS.get(workflow_path) or WORKFLOW_PATHS.get(workflow_path)
    if path is None:
        raise HTTPException(status_code=409, detail="Application workflow path is not configured")
    stage_keys = path["stages"]
    try:
        current_index = stage_keys.index(current.stage_key)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Stage {current.stage_key} is not part of this application's workflow path",
        ) from exc

    active_rules = {rule.stage_key: rule for rule in rules}
    for stage_key in stage_keys[current_index + 1:]:
        candidate = active_rules.get(stage_key)
        if candidate is None:
            if application and application.aph_rule_key and stage_key not in {
                "deficiency_check", "committee_stage",
            }:
                raise HTTPException(
                    status_code=409,
                    detail=f"Mandatory APH stage {stage_key} is not configured.",
                )
            continue
        if stage_key in {"initial_scrutiny", "deficiency_check"} and not candidate.requires_scrutiny:
            if application and application.aph_rule_key and stage_key == "initial_scrutiny":
                raise HTTPException(status_code=409, detail="Mandatory APH scrutiny is disabled in workflow configuration.")
            continue
        if stage_key in {"evc_scheduling", "evc_completion"} and not candidate.requires_evc:
            if application and application.aph_rule_key:
                raise HTTPException(status_code=409, detail="Mandatory APH EVC is disabled in workflow configuration.")
            continue
        if stage_key == "committee_stage" and not candidate.requires_committee:
            if application and application.aph_rule_key and application.committee_referral:
                raise HTTPException(status_code=409, detail="Conditional APH committee stage is disabled in workflow configuration.")
            continue
        if application and application.aph_rule_key:
            if stage_key == "deficiency_check" and db and not unresolved_deficiencies(db, application):
                continue
            if stage_key == "committee_stage" and not application.committee_referral:
                continue
        return candidate
    return None


def transition(db: Session, application: Application, action: str, user: User, reason: str | None):
    check_application_access(user, application)
    if action not in {"forward", "return", "reject", "resubmit", "complete", "refer_committee"}:
        raise HTTPException(status_code=400, detail="Unsupported workflow action")
    if action in {"return", "reject"} and not (reason and reason.strip()):
        raise HTTPException(status_code=400, detail="A reason is required")
    if application.status in FINAL_STATUSES:
        raise HTTPException(status_code=409, detail="Final applications cannot be reopened")
    if application.aph_rule_key and action == "reject":
        raise HTTPException(
            status_code=409,
            detail="Record an externally notified competent-authority decision instead of rejecting during workflow processing.",
        )
    if action == "resubmit":
        if user.role != "institution" or application.institution_id != user.institution_id:
            raise HTTPException(status_code=403, detail="Only the owning institution may resubmit")
        if application.status != "returned":
            raise HTTPException(status_code=409, detail="Application is not awaiting resubmission")
        path = WORKFLOW_PATHS.get(application.workflow_path or DEFAULT_WORKFLOW_PATH)
        path = APH_WORKFLOW_PATHS.get(application.workflow_path) or path
        if path is None:
            raise HTTPException(status_code=409, detail="Application workflow path is not configured")
        if application.aph_rule_key:
            identified_deficiencies = db.query(ScrutinyObservations).filter_by(
                application_id=application.id, is_deficiency=True
            ).order_by(ScrutinyObservations.created_at, ScrutinyObservations.id).all()
        else:
            identified_deficiencies = []
        if identified_deficiencies:
            for observation in identified_deficiencies:
                latest = latest_deficiency_compliance(db, observation.id)
                if latest is None or latest.submitted_at <= application.updated_at:
                    raise HTTPException(
                        status_code=409,
                        detail="Submit compliance evidence against every returned deficiency before resubmitting.",
                    )
            observation_stage = application.current_stage
            first_review_stage = (
                "evc_completion"
                if observation_stage in {"evc_scheduling", "evc_completion"}
                else "deficiency_check"
            )
            if first_review_stage not in path["stages"]:
                raise HTTPException(
                    status_code=409,
                    detail="This application route does not contain a compatible deficiency review stage.",
                )
        else:
            first_review_stage = next(
                (stage_key for stage_key in path["stages"] if stage_key != "submission"),
                None,
            )
        target = next(
            (rule for rule in ordered_rules(db) if rule.stage_key == first_review_stage),
            None,
        )
        if target is None:
            raise HTTPException(status_code=409, detail="First review stage is not configured")
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
        if action == "refer_committee":
            if user.role not in {"regional_officer", "bureau_officer", "admin"}:
                raise HTTPException(status_code=403, detail="Role cannot refer an application to SAC/SHC")
            if not (reason and reason.strip()):
                raise HTTPException(status_code=400, detail="A reason is required for a conditional committee referral")
            path = APH_WORKFLOW_PATHS.get(application.workflow_path)
            if (
                not application.aph_rule_key
                or path is None
                or "committee_stage" not in path["stages"]
            ):
                raise HTTPException(status_code=409, detail="SAC/SHC is not part of this application category")
            rule = APH_RULES[application.aph_rule_key]
            expected_stage = (
                "evc_completion" if "evc" in rule["mandatory_steps"] else "initial_scrutiny"
            )
            if application.current_stage != expected_stage:
                raise HTTPException(
                    status_code=409,
                    detail="A conditional SAC/SHC referral may be recorded only after the required prior processing stage.",
                )
            if "evc" in rule["mandatory_steps"] and not db.query(EVCAppointments).filter_by(
                application_id=application.id, status="completed"
            ).first():
                raise HTTPException(
                    status_code=409,
                    detail="Complete an EVC appointment before the conditional SAC/SHC referral.",
                )
            if unresolved_deficiencies(db, application):
                raise HTTPException(
                    status_code=409,
                    detail="Resolve all identified deficiencies before recording a conditional SAC/SHC referral.",
                )
            target = next(
                (rule for rule in ordered_rules(db) if rule.stage_key == "committee_stage"),
                None,
            )
            if target is None:
                raise HTTPException(status_code=409, detail="SAC/SHC stage is not configured")
            application.committee_referral = True
            new_status = "pending"
        if action == "return":
            target, new_status = current_rule, "returned"
        elif action == "reject":
            target, new_status = current_rule, "rejected"
        elif action != "refer_committee":
            if application.aph_rule_key and application.current_stage == "submission":
                required = APH_RULES[application.aph_rule_key]["required_documents"]
                for category in required:
                    if not db.query(Documents).filter_by(
                        application_id=application.id, category=category
                    ).first():
                        raise HTTPException(
                            status_code=409,
                            detail=f"Upload the required {category} document before starting APH processing.",
                        )
            if application.aph_rule_key and unresolved_deficiencies(db, application):
                raise HTTPException(
                    status_code=409,
                    detail="Identified deficiencies must be addressed and reviewed before the application can proceed.",
                )
            if application.aph_rule_key and application.current_stage == "final_status":
                raise HTTPException(
                    status_code=409,
                    detail="Workflow completion does not grant approval. Record an externally notified competent-authority decision separately.",
                )
            if (
                application.aph_rule_key
                and application.current_stage == "evc_completion"
                and not db.query(EVCAppointments).filter_by(
                    application_id=application.id, status="completed"
                ).first()
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Complete an EVC appointment before advancing from the APH EVC stage.",
                )
            target = next_rule(
                rules,
                current_rule,
                application.workflow_path or DEFAULT_WORKFLOW_PATH,
                application=application,
                db=db,
            )
            if target is None:
                if application.aph_rule_key:
                    raise HTTPException(
                        status_code=409,
                        detail="No further APH workflow stage is configured; an external decision record is required.",
                    )
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
        None if application.aph_rule_key else
        now + timedelta(days=target.deadline_days)
        if target.deadline_days is not None else None
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
