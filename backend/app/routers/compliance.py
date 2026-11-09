from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import check_application_access, get_current_user, require_roles
from app.models import (
    Application, DeficiencyCompliance, Documents, Institution, ScrutinyObservations,
    Undertakings, User,
)
from app.schemas.compliance import (
    ComplianceCreate, ComplianceVerifyRequest, DeficiencyComplianceReview,
    DeficiencyComplianceSubmit,
)
from app.services.audit import log_action
from app.services.notifications_service import create_notification
from app.services.workflow_engine import latest_deficiency_compliance

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


def serialize(item: Undertakings) -> dict:
    remaining = (item.due_date.date() - datetime.utcnow().date()).days
    computed_status = "due_soon" if 0 <= remaining <= 30 and item.status == "pending" else item.status
    return {
        "id": item.id, "institution_id": item.institution_id, "application_id": item.application_id,
        "description": item.description, "due_date": item.due_date, "status": computed_status,
        "days_remaining": remaining, "submitted_at": item.submitted_at,
        "evidence_document_id": item.evidence_document_id, "remarks": item.remarks,
    }


def serialize_deficiency_submission(item: DeficiencyCompliance) -> dict:
    return {
        "id": item.id,
        "observation_id": item.observation_id,
        "application_id": item.application_id,
        "evidence_document_id": item.evidence_document_id,
        "submitted_by": item.submitted_by,
        "submitted_at": item.submitted_at,
        "status": item.status,
        "reviewed_by": item.reviewed_by,
        "reviewed_at": item.reviewed_at,
        "remarks": item.remarks,
    }


@router.post(
    "/applications/{application_id}/deficiencies/{observation_id}/submissions",
    status_code=201,
)
def submit_deficiency_compliance(
    application_id: str,
    observation_id: int,
    payload: DeficiencyComplianceSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("institution")),
):
    application = db.query(Application).filter_by(id=application_id).first()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_access(user, application)
    if application.status != "returned":
        raise HTTPException(status_code=409, detail="The application must be returned for compliance before evidence is submitted")
    observation = db.query(ScrutinyObservations).filter_by(
        id=observation_id, application_id=application.id, is_deficiency=True
    ).first()
    if observation is None:
        raise HTTPException(status_code=404, detail="Deficiency observation not found for this application")
    previous = latest_deficiency_compliance(db, observation.id)
    if previous and previous.status == "verified":
        raise HTTPException(status_code=409, detail="This deficiency has already been verified")
    document = db.query(Documents).filter_by(
        id=payload.evidence_document_id,
        application_id=application.id,
        institution_id=user.institution_id,
        category="Compliance Evidence",
    ).first()
    if document is None:
        raise HTTPException(
            status_code=400,
            detail="Attach a Compliance Evidence document to this application before submitting it against the deficiency.",
        )
    item = DeficiencyCompliance(
        observation_id=observation.id,
        application_id=application.id,
        institution_id=user.institution_id,
        evidence_document_id=document.id,
        submitted_by=user.id,
        status="pending",
    )
    db.add(item)
    db.flush()
    log_action(
        db, user, "deficiency_compliance_submitted", "deficiency_compliance",
        item.id, previous.status if previous else None, "pending",
        f"Evidence submitted for observation {observation.id}", application.current_stage,
    )
    db.commit()
    db.refresh(item)
    return serialize_deficiency_submission(item)


@router.post("/deficiency-submissions/{submission_id}/review")
def review_deficiency_compliance(
    submission_id: int,
    payload: DeficiencyComplianceReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("regional_officer", "bureau_officer", "admin")),
):
    item = db.query(DeficiencyCompliance).filter_by(id=submission_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Deficiency compliance submission not found")
    application = db.query(Application).filter_by(id=item.application_id).first()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_access(user, application)
    latest = latest_deficiency_compliance(db, item.observation_id)
    if latest is None or latest.id != item.id or item.status != "pending":
        raise HTTPException(status_code=409, detail="Only the latest pending evidence submission can be reviewed")
    previous = item.status
    item.status = payload.status
    item.reviewed_by = user.id
    item.reviewed_at = datetime.utcnow()
    item.remarks = payload.remarks.strip()
    log_action(
        db, user, "deficiency_compliance_reviewed", "deficiency_compliance",
        item.id, previous, item.status, item.remarks, application.current_stage,
    )
    institution_user = db.query(User).filter_by(
        institution_id=item.institution_id, role="institution", is_active=True
    ).first()
    if institution_user:
        create_notification(
            db, "deficiency_compliance_reviewed", item.id, institution_user.id,
            f"Compliance evidence for a deficiency was marked {item.status}: {item.remarks}",
            action_link=f"/applications/{application.id}",
        )
    db.commit()
    db.refresh(item)
    return serialize_deficiency_submission(item)


@router.post("", status_code=201)
def create_compliance(payload: ComplianceCreate, db: Session = Depends(get_db),
                      user: User = Depends(require_roles("institution"))):
    item = Undertakings(
        institution_id=user.institution_id, application_id=payload.application_id,
        description=payload.description, due_date=payload.due_date, status="pending",
    )
    db.add(item)
    db.flush()
    institution_user = db.query(User).filter_by(
        institution_id=user.institution_id, role="institution", is_active=True
    ).first()
    if institution_user:
        create_notification(db, "compliance_deadline", item.id, institution_user.id,
                            f"Compliance item created: {item.description}", item.due_date,
                            "/compliance")
    log_action(db, user, "compliance_created", "compliance", item.id,
               updated_status="pending", reason=payload.description)
    db.commit()
    db.refresh(item)
    return serialize(item)


@router.get("")
def list_compliance(status_filter: str | None = None, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    if user.role == "evc_committee":
        raise HTTPException(status_code=403, detail="EVC committee users do not have compliance access")
    query = db.query(Undertakings)
    if user.role == "institution":
        query = query.filter(Undertakings.institution_id == user.institution_id)
    elif user.role == "regional_officer":
        institution_ids = [item.id for item in db.query(Institution).filter_by(region=user.region).all()]
        query = query.filter(Undertakings.institution_id.in_(institution_ids))
    items = query.order_by(Undertakings.due_date).all()
    output = [serialize(item) for item in items]
    return [item for item in output if not status_filter or item["status"] == status_filter]


@router.post("/{compliance_id}/evidence")
def submit_evidence(compliance_id: int, evidence_document_id: int,
                    db: Session = Depends(get_db), user: User = Depends(require_roles("institution"))):
    item = db.query(Undertakings).filter_by(id=compliance_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    if item.institution_id != user.institution_id:
        raise HTTPException(status_code=403, detail="Compliance item belongs to another institution")
    item.evidence_document_id = evidence_document_id
    item.submitted_at = datetime.utcnow()
    item.status = "submitted"
    log_action(db, user, "compliance_evidence_submitted", "compliance", item.id,
               "pending", "submitted")
    db.commit()
    return serialize(item)


@router.post("/{compliance_id}/verify")
@router.post("/{compliance_id}/deficiency")
def verify_compliance(compliance_id: int, payload: ComplianceVerifyRequest,
                      db: Session = Depends(get_db),
                      user: User = Depends(require_roles("regional_officer", "bureau_officer", "admin"))):
    if payload.status not in {"verified", "deficient"}:
        raise HTTPException(status_code=400, detail="Status must be verified or deficient")
    item = db.query(Undertakings).filter_by(id=compliance_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    previous = item.status
    item.status = payload.status
    item.verifying_officer_id = user.id
    item.remarks = payload.remarks
    log_action(db, user, "compliance_verified" if payload.status == "verified" else "compliance_deficiency",
               "compliance", item.id, previous, item.status, payload.remarks)
    institution_user = db.query(User).filter_by(
        institution_id=item.institution_id, role="institution", is_active=True
    ).first()
    if institution_user:
        create_notification(db, "compliance_update", item.id, institution_user.id,
                            f"Compliance item marked {payload.status}: {payload.remarks}", item.due_date)
    db.commit()
    return serialize(item)
