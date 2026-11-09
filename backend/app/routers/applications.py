from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import check_application_access, get_current_user, require_roles
from app.models import (
    Application, ApplicationStage, Institution, ScrutinyObservations, User, WorkflowRules,
)
from app.schemas.applications import ApplicationCreate, ObservationRequest, ResubmitRequest, TransitionRequest
from app.services.audit import log_action
from app.services.notifications_service import create_notification
from app.services.workflow_engine import transition
from app.workflow_paths import DEFAULT_WORKFLOW_PATH, WORKFLOW_PATHS

router = APIRouter(prefix="/api/applications", tags=["applications"])


def serialize_application(db: Session, item: Application) -> dict:
    institution = db.query(Institution).filter(Institution.id == item.institution_id).first()
    officer = db.query(User).filter(User.id == item.assigned_officer_id).first() if item.assigned_officer_id else None
    return {
        "id": item.id,
        "institution_id": item.institution_id,
        "institution": institution.name if institution else "Unknown institution",
        "region": item.region,
        "type": item.application_type,
        "application_type": item.application_type,
        "workflow_path": item.workflow_path or DEFAULT_WORKFLOW_PATH,
        "workflow_path_label": WORKFLOW_PATHS.get(
            item.workflow_path or DEFAULT_WORKFLOW_PATH, WORKFLOW_PATHS[DEFAULT_WORKFLOW_PATH]
        )["label"],
        "workflow_stages": list(
            WORKFLOW_PATHS.get(
                item.workflow_path or DEFAULT_WORKFLOW_PATH, WORKFLOW_PATHS[DEFAULT_WORKFLOW_PATH]
            )["stages"]
        ),
        "submittedAt": item.submitted_at.isoformat() if item.submitted_at else None,
        "submitted_at": item.submitted_at,
        "stage": item.current_stage,
        "current_stage": item.current_stage,
        "officer": officer.full_name if officer else "Unassigned",
        "assigned_officer_id": item.assigned_officer_id,
        "daysPending": max(0, (datetime.utcnow() - item.submitted_at).days) if item.submitted_at else 0,
        "deadline": item.deadline,
        "status": item.status,
        "priority": item.priority,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("institution")),
):
    if payload.workflow_path not in WORKFLOW_PATHS:
        raise HTTPException(status_code=400, detail="Choose a supported example workflow path")
    institution_id = user.institution_id
    if payload.institution_id and payload.institution_id != user.institution_id:
        raise HTTPException(status_code=403, detail="Institution users may only apply for their own institution")
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if institution is None:
        raise HTTPException(status_code=400, detail="Your account is not linked to an institution")
    rule = db.query(WorkflowRules).filter_by(stage_key="submission", is_active=True).first()
    if rule is None:
        raise HTTPException(status_code=503, detail="Submission workflow rule is not configured")
    year = datetime.utcnow().year
    count = db.query(Application).filter(Application.id.like(f"APP-{year}-%")).count() + 1
    app_id = f"APP-{year}-{count:04d}"
    officer = db.query(User).filter(
        User.role == "regional_officer", User.region == institution.region, User.is_active.is_(True)
    ).first()
    now = datetime.utcnow()
    item = Application(
        id=app_id, institution_id=institution.id, region=institution.region,
        application_type=payload.application_type, submitted_at=now,
        workflow_path=payload.workflow_path,
        current_stage=rule.stage_key, status="pending", assigned_officer_id=officer.id if officer else None,
        deadline=now + timedelta(days=rule.deadline_days) if rule.deadline_days else None,
        priority="Medium",
    )
    db.add(item)
    db.flush()
    db.add(ApplicationStage(
        application_id=item.id, stage_key=rule.stage_key, stage_name=rule.stage_name,
        actor_user_id=user.id, reason="Application submitted",
    ))
    log_action(db, user, "application_submitted", "application", item.id,
               updated_status="pending", workflow_stage=rule.stage_key)
    if officer:
        create_notification(db, "submission", item.id, officer.id,
                            f"New application {item.id} submitted", item.deadline,
                            f"/applications/{item.id}")
    db.commit()
    db.refresh(item)
    return serialize_application(db, item)


@router.get("")
def list_applications(
    region: str | None = None,
    application_type: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    current_stage: str | None = None,
    search: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    sort_by: str = "submitted_at",
    sort_order: str = "desc",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Application)
    if user.role == "institution":
        query = query.filter(Application.institution_id == user.institution_id)
    elif user.role == "regional_officer":
        query = query.filter(Application.region == user.region)
    elif user.role == "evc_committee":
        query = query.filter(Application.current_stage.in_(["evc_scheduling", "evc_completion"]))
    if region:
        query = query.filter(Application.region == region)
    if application_type:
        query = query.filter(Application.application_type == application_type)
    if status_filter:
        query = query.filter(Application.status == status_filter)
    if current_stage:
        query = query.filter(Application.current_stage == current_stage)
    if search:
        query = query.filter(or_(Application.id.ilike(f"%{search}%"),
                                 Application.application_type.ilike(f"%{search}%")))
    if start_date:
        query = query.filter(Application.submitted_at >= start_date)
    if end_date:
        query = query.filter(Application.submitted_at <= end_date)
    sort_columns = {
        "submitted_at": Application.submitted_at,
        "deadline": Application.deadline,
        "status": Application.status,
        "current_stage": Application.current_stage,
    }
    if sort_by not in sort_columns or sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid sort field or order")
    sort_column = sort_columns[sort_by]
    query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())
    return [serialize_application(db, item) for item in query.offset(offset).limit(limit).all()]


@router.get("/{application_id}")
def get_application(application_id: str, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    item = db.query(Application).filter(Application.id == application_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_access(user, item)
    result = serialize_application(db, item)
    result["timeline"] = [
        {
            "id": stage.id, "stage": stage.stage_name, "stage_key": stage.stage_key,
            "entered_at": stage.entered_at, "exited_at": stage.exited_at,
            "status": stage.status, "actor_user_id": stage.actor_user_id, "reason": stage.reason,
        }
        for stage in db.query(ApplicationStage).filter_by(application_id=item.id)
        .order_by(ApplicationStage.entered_at).all()
    ]
    result["observations"] = [
        {
            "id": observation.id, "observation_text": observation.observation_text,
            "is_deficiency": observation.is_deficiency, "severity": observation.severity,
            "created_at": observation.created_at, "officer_id": observation.officer_id,
        }
        for observation in db.query(ScrutinyObservations).filter_by(application_id=item.id)
        .order_by(ScrutinyObservations.created_at).all()
    ]
    from app.models import Documents
    result["documents"] = [
        {"id": document.id, "category": document.category, "file_name": document.file_name,
         "status": document.status}
        for document in db.query(Documents).filter_by(application_id=item.id).all()
    ]
    return result


@router.post("/{application_id}/transition")
def transition_application(application_id: str, payload: TransitionRequest,
                           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Application).filter(Application.id == application_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return serialize_application(db, transition(db, item, payload.action, user, payload.reason))


@router.post("/{application_id}/resubmit")
def resubmit_application(application_id: str, payload: ResubmitRequest = ResubmitRequest(),
                         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Application).filter(Application.id == application_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return serialize_application(db, transition(db, item, "resubmit", user, payload.reason))


@router.post("/{application_id}/observations", status_code=201)
def add_observation(application_id: str, payload: ObservationRequest,
                    db: Session = Depends(get_db),
                    user: User = Depends(require_roles("regional_officer", "bureau_officer", "admin"))):
    item = db.query(Application).filter(Application.id == application_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_access(user, item)
    observation = ScrutinyObservations(
        application_id=item.id, officer_id=user.id, observation_text=payload.observation_text,
        is_deficiency=payload.is_deficiency, severity=payload.severity,
    )
    db.add(observation)
    log_action(db, user, "observation_added", "application", item.id,
               updated_status="deficiency" if payload.is_deficiency else item.status,
               reason=payload.observation_text, workflow_stage=item.current_stage)
    db.commit()
    db.refresh(observation)
    return {"id": observation.id, "application_id": item.id, "observation_text": observation.observation_text}
