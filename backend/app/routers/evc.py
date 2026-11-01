from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import check_application_access, get_current_user, require_roles
from app.models import Application, EVCAppointments, User
from app.schemas.evc import EVCAppointmentCreate, EVCCompletion
from app.services.audit import log_action
from app.services.notifications_service import create_notification
from app.services.workflow_engine import transition

router = APIRouter(prefix="/api/evc", tags=["evc"])


@router.post("", status_code=201)
def schedule(payload: EVCAppointmentCreate, db: Session = Depends(get_db),
             user: User = Depends(require_roles("regional_officer", "bureau_officer", "evc_committee", "admin"))):
    application = db.query(Application).filter_by(id=payload.application_id).first()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_access(user, application)
    if application.current_stage not in {"evc_scheduling", "evc_completion"}:
        raise HTTPException(status_code=409, detail="Application is not in the EVC queue")
    item = EVCAppointments(
        application_id=application.id, scheduled_date=payload.scheduled_date,
        location=payload.location, committee_members=",".join(map(str, payload.committee_members)),
        status="scheduled",
    )
    db.add(item)
    db.flush()
    log_action(db, user, "evc_scheduled", "evc_appointment", item.id,
               updated_status="scheduled", workflow_stage=application.current_stage)
    institution_user = db.query(User).filter_by(
        institution_id=application.institution_id, role="institution", is_active=True
    ).first()
    if institution_user:
        create_notification(db, "evc_scheduled", item.id, institution_user.id,
                            f"EVC visit scheduled for {application.id}", item.scheduled_date,
                            f"/applications/{application.id}")
    committee = db.query(User).filter_by(role="evc_committee", is_active=True).all()
    for member in committee:
        create_notification(db, "evc_scheduled", item.id, member.id,
                            f"EVC appointment scheduled for {application.id}", item.scheduled_date,
                            f"/evc")
    db.commit()
    db.refresh(item)
    return item


@router.get("")
def list_appointments(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(EVCAppointments)
    if user.role == "institution":
        ids = [row.id for row in db.query(Application.id).filter_by(institution_id=user.institution_id).all()]
        query = query.filter(EVCAppointments.application_id.in_(ids))
    elif user.role == "regional_officer":
        ids = [row.id for row in db.query(Application.id).filter_by(region=user.region).all()]
        query = query.filter(EVCAppointments.application_id.in_(ids))
    if start_date:
        query = query.filter(EVCAppointments.scheduled_date >= start_date)
    if end_date:
        query = query.filter(EVCAppointments.scheduled_date <= end_date)
    if status_filter:
        query = query.filter(EVCAppointments.status == status_filter)
    return query.order_by(EVCAppointments.scheduled_date).all()


@router.post("/{appointment_id}/complete")
def complete(appointment_id: int, payload: EVCCompletion, db: Session = Depends(get_db),
             user: User = Depends(require_roles("evc_committee", "regional_officer", "bureau_officer", "admin"))):
    item = db.query(EVCAppointments).filter_by(id=appointment_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="EVC appointment not found")
    if item.status != "scheduled":
        raise HTTPException(status_code=409, detail="Appointment is not awaiting completion")
    application = db.query(Application).filter_by(id=item.application_id).first()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_access(user, application)
    item.status = "completed"
    item.completed_at = datetime.utcnow()
    item.completed_by = user.id
    item.findings = payload.findings
    item.recommendation = payload.recommendation
    db.commit()
    if application.current_stage == "evc_scheduling":
        transition(db, application, "forward", user, payload.findings)
    if application.current_stage == "evc_completion":
        transition(db, application, "complete", user, payload.recommendation)
    log_action(db, user, "evc_completed", "evc_appointment", item.id,
               "scheduled", "completed", payload.findings, application.current_stage)
    institution_user = db.query(User).filter_by(
        institution_id=application.institution_id, role="institution", is_active=True
    ).first()
    if institution_user:
        create_notification(db, "evc_completed", item.id, institution_user.id,
                            f"EVC visit completed for {application.id}", action_link=f"/applications/{application.id}")
    db.commit()
    return {"id": item.id, "status": item.status, "application": application.id,
            "current_stage": application.current_stage, "findings": item.findings,
            "recommendation": item.recommendation}
