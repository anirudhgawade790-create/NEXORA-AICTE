from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.aph_rules import (
    APH_RULES,
    APH_SOURCE_DOCUMENT,
    APH_WORKFLOW_PATHS,
    appeal_deadline,
    appeal_is_open,
    application_rule_metadata,
    decision_stage_for,
    workflow_path_for,
)
from app.database import get_db
from app.deps import check_application_access, get_current_user, require_roles
from app.models import (
    Application, ApplicationAppeal, ApplicationStage, DeficiencyCompliance, Institution,
    Documents, ScrutinyObservations, User, WorkflowRules,
)
from app.schemas.applications import (
    AppealCreate, ApplicationCreate, DecisionRecordRequest, ObservationRequest,
    ResubmitRequest, TransitionRequest,
)
from app.services.audit import log_action
from app.services.notifications_service import create_notification
from app.services.workflow_engine import latest_deficiency_compliance, transition
from app.workflow_paths import DEFAULT_WORKFLOW_PATH, WORKFLOW_PATHS

router = APIRouter(prefix="/api/applications", tags=["applications"])


def serialize_application(db: Session, item: Application) -> dict:
    institution = db.query(Institution).filter(Institution.id == item.institution_id).first()
    officer = db.query(User).filter(User.id == item.assigned_officer_id).first() if item.assigned_officer_id else None
    path_key = item.workflow_path or DEFAULT_WORKFLOW_PATH
    path = APH_WORKFLOW_PATHS.get(path_key) or WORKFLOW_PATHS.get(
        path_key, WORKFLOW_PATHS[DEFAULT_WORKFLOW_PATH]
    )
    appeal = db.query(ApplicationAppeal).filter_by(application_id=item.id).first()
    allowed_appeal_until = (
        appeal_deadline(item.decision_at, item.decision_authority)
        if item.decision_at else None
    )
    return {
        "id": item.id,
        "institution_id": item.institution_id,
        "institution": institution.name if institution else "Unknown institution",
        "region": item.region,
        "type": item.application_type,
        "application_type": item.application_type,
        "workflow_path": path_key,
        "workflow_path_label": path["label"],
        "workflow_stages": list(path["stages"]),
        "aph_rule_key": item.aph_rule_key,
        "aph_rule_metadata": item.aph_rule_metadata,
        "processing_timeline": (
            item.aph_rule_metadata.get("processing_timeline")
            if item.aph_rule_metadata else None
        ),
        "required_documents": (
            item.aph_rule_metadata.get("required_documents", [])
            if item.aph_rule_metadata else []
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
        "decision_at": item.decision_at,
        "decision_authority": item.decision_authority,
        "decision_reference": item.decision_reference,
        "decision_document_id": item.decision_document_id,
        "appeal_deadline": allowed_appeal_until,
        "appeal_submitted": appeal is not None,
        "appeal_status": appeal.status if appeal else None,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("institution")),
):
    aph_rule_key = payload.aph_rule_key
    if aph_rule_key:
        if aph_rule_key not in APH_RULES:
            raise HTTPException(status_code=400, detail="Choose a supported APH 2024-2027 application category")
        workflow_path = workflow_path_for(aph_rule_key)
        if payload.workflow_path and payload.workflow_path != workflow_path:
            raise HTTPException(status_code=400, detail="APH categories determine their workflow path")
        rule_metadata = application_rule_metadata(aph_rule_key)
        minimum_core_courses = APH_RULES[aph_rule_key]["minimum_core_courses"]
        if minimum_core_courses and payload.program_area is None:
            raise HTTPException(
                status_code=400,
                detail="Select whether this application is for Engineering and Technology.",
            )
        if (
            minimum_core_courses
            and payload.program_area == "engineering_technology"
            and (payload.core_course_count is None or payload.core_course_count < minimum_core_courses)
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Clause 2.6 requires at least {minimum_core_courses} core courses for this Engineering and Technology category.",
            )
        rule_metadata["applicant_assertions"] = {
            "program_area": payload.program_area,
            "core_course_count": payload.core_course_count,
        }
    else:
        if payload.workflow_path not in WORKFLOW_PATHS:
            raise HTTPException(
                status_code=400,
                detail="Choose an APH application category or a supported demo workflow path.",
            )
        workflow_path = payload.workflow_path
        rule_metadata = None
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
        workflow_path=workflow_path,
        aph_rule_key=aph_rule_key,
        aph_rule_metadata=rule_metadata,
        current_stage=rule.stage_key, status="pending", assigned_officer_id=officer.id if officer else None,
        deadline=(
            None if aph_rule_key else
            now + timedelta(days=rule.deadline_days) if rule.deadline_days else None
        ),
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
            "workflow_stage": observation.workflow_stage,
            "compliance_submissions": [
                {
                    "id": submission.id,
                    "evidence_document_id": submission.evidence_document_id,
                    "submitted_at": submission.submitted_at,
                    "status": submission.status,
                    "reviewed_at": submission.reviewed_at,
                    "remarks": submission.remarks,
                }
                for submission in db.query(DeficiencyCompliance).filter_by(
                    observation_id=observation.id
                ).order_by(DeficiencyCompliance.submitted_at).all()
            ],
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
        workflow_stage=item.current_stage,
    )
    db.add(observation)
    log_action(db, user, "observation_added", "application", item.id,
               updated_status="deficiency" if payload.is_deficiency else item.status,
               reason=payload.observation_text, workflow_stage=item.current_stage)
    db.commit()
    db.refresh(observation)
    return {"id": observation.id, "application_id": item.id, "observation_text": observation.observation_text}


@router.post("/{application_id}/decision")
def record_external_decision(
    application_id: str,
    payload: DecisionRecordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("bureau_officer", "admin")),
):
    item = db.query(Application).filter_by(id=application_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if not item.aph_rule_key:
        raise HTTPException(status_code=409, detail="External APH decision recording is only enabled for APH-routed applications")
    if item.current_stage != decision_stage_for(item.aph_rule_key):
        raise HTTPException(status_code=409, detail="The APH workflow has not reached the decision-record stage")
    if item.decision_at is not None:
        raise HTTPException(status_code=409, detail="A competent-authority decision is already recorded")
    uploaded_at = (
        payload.uploaded_at.astimezone(timezone.utc).replace(tzinfo=None)
        if payload.uploaded_at.tzinfo else payload.uploaded_at
    )
    if uploaded_at > datetime.utcnow():
        raise HTTPException(status_code=400, detail="Decision upload time cannot be in the future")
    evidence = db.query(Documents).filter_by(
        id=payload.evidence_document_id,
        application_id=item.id,
        institution_id=item.institution_id,
        category="Approval Supporting Documents",
    ).first()
    if evidence is None:
        raise HTTPException(
            status_code=400,
            detail="Attach the externally issued decision/order as an Approval Supporting Documents file before recording it.",
        )
    from app.services.workflow_engine import unresolved_deficiencies
    if unresolved_deficiencies(db, item):
        raise HTTPException(
            status_code=409,
            detail="Identified deficiencies must be complied with and reviewed before an approval decision can be recorded.",
        )
    item.status = payload.outcome
    item.decision_at = uploaded_at
    item.decision_authority = payload.authority
    item.decision_reference = payload.source_reference.strip()
    item.decision_document_id = evidence.id
    item.updated_at = datetime.utcnow()
    log_action(
        db, user, "external_decision_recorded", "application", item.id,
        "pending", item.status, payload.source_reference.strip(), item.current_stage,
    )
    db.commit()
    db.refresh(item)
    return serialize_application(db, item)


@router.post("/{application_id}/appeal", status_code=status.HTTP_201_CREATED)
def file_appeal(
    application_id: str,
    payload: AppealCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("institution")),
):
    item = db.query(Application).filter_by(id=application_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_access(user, item)
    if item.decision_authority != "executive_committee" or item.decision_at is None:
        raise HTTPException(
            status_code=409,
            detail="APH Clause 2.24 allows one appeal only against an Executive Committee decision recorded with its upload date.",
        )
    if not appeal_is_open(item.decision_at, item.decision_authority, datetime.utcnow()):
        raise HTTPException(status_code=409, detail="The seven-day APH appeal period has expired")
    if db.query(ApplicationAppeal).filter_by(application_id=item.id).first():
        raise HTTPException(status_code=409, detail="Only one appeal may be recorded for this application")
    appeal = ApplicationAppeal(
        application_id=item.id,
        reason=payload.reason.strip(),
        status="recorded_for_sac",
        created_by=user.id,
    )
    db.add(appeal)
    db.flush()
    log_action(
        db, user, "appeal_recorded", "application_appeal", appeal.id,
        updated_status=appeal.status, reason=appeal.reason,
        workflow_stage="appeal",
    )
    db.commit()
    db.refresh(appeal)
    return {
        "id": appeal.id,
        "application_id": appeal.application_id,
        "reason": appeal.reason,
        "submitted_at": appeal.submitted_at,
        "status": appeal.status,
        "note": "Recorded in NEXORA only; this does not file an appeal on the AICTE portal.",
        "source_document": APH_SOURCE_DOCUMENT,
        "clause": "2.24",
    }
