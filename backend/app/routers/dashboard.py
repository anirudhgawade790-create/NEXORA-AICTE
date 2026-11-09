from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import (
    Application, ComplianceSubmissions, Documents, EVCAppointments, Institution,
    User, Undertakings,
)
from app.services.expiry import compute_document_status, reminder_intervals

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(
    region: str | None = None,
    application_type: str | None = None,
    stage: str | None = None,
    status: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
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
    if stage:
        query = query.filter(Application.current_stage == stage)
    if status:
        query = query.filter(Application.status == status)
    if start_date:
        query = query.filter(Application.submitted_at >= start_date)
    if end_date:
        query = query.filter(Application.submitted_at <= end_date)
    applications = query.all()
    app_ids = [item.id for item in applications]
    open_apps = [item for item in applications if item.status not in {"approved", "rejected"}]
    awaiting_evc = sum(item.current_stage in {"evc_scheduling", "evc_completion"} for item in applications)
    awaiting_committee = sum(item.current_stage == "committee_stage" for item in applications)
    now = datetime.utcnow()
    due_soon = db.query(Undertakings).filter(
        Undertakings.due_date >= now,
        Undertakings.due_date <= now + timedelta(days=30),
        Undertakings.status.notin_(["verified", "overdue"]),
    )
    if user.role == "institution":
        due_soon = due_soon.filter(Undertakings.institution_id == user.institution_id)
    elif user.role == "regional_officer":
        region_institutions = [item.id for item in db.query(Institution.id).filter_by(region=user.region).all()]
        due_soon = due_soon.filter(Undertakings.institution_id.in_(region_institutions))
    elif user.role == "evc_committee":
        due_soon = due_soon.filter(Undertakings.id == -1)
    compliance_due_soon = db.query(ComplianceSubmissions).filter(
        ComplianceSubmissions.due_date >= now,
        ComplianceSubmissions.due_date <= now + timedelta(days=30),
        ComplianceSubmissions.verification_status.notin_(["verified", "overdue"]),
    )
    overdue_compliance = db.query(Undertakings).filter(
        Undertakings.due_date < now,
        Undertakings.status != "verified",
    )
    overdue_submissions = db.query(ComplianceSubmissions).filter(
        ComplianceSubmissions.due_date < now,
        ComplianceSubmissions.verification_status != "verified",
    )
    if user.role == "institution":
        compliance_due_soon = compliance_due_soon.filter(
            ComplianceSubmissions.institution_id == user.institution_id
        )
        overdue_compliance = overdue_compliance.filter(
            Undertakings.institution_id == user.institution_id
        )
        overdue_submissions = overdue_submissions.filter(
            ComplianceSubmissions.institution_id == user.institution_id
        )
    elif user.role == "regional_officer":
        region_institutions = [
            item.id for item in db.query(Institution.id).filter_by(region=user.region).all()
        ]
        compliance_due_soon = compliance_due_soon.filter(
            ComplianceSubmissions.institution_id.in_(region_institutions)
        )
        overdue_compliance = overdue_compliance.filter(
            Undertakings.institution_id.in_(region_institutions)
        )
        overdue_submissions = overdue_submissions.filter(
            ComplianceSubmissions.institution_id.in_(region_institutions)
        )
    elif user.role == "evc_committee":
        compliance_due_soon = compliance_due_soon.filter(ComplianceSubmissions.id == -1)
        overdue_compliance = overdue_compliance.filter(Undertakings.id == -1)
        overdue_submissions = overdue_submissions.filter(ComplianceSubmissions.id == -1)
    compliance_due_soon_count = due_soon.count() + compliance_due_soon.count()
    overdue_compliance_count = overdue_compliance.count() + overdue_submissions.count()
    evc_app_query = db.query(Application).filter(
        Application.current_stage.in_(["evc_scheduling", "evc_completion"]),
        Application.status.notin_(["approved", "rejected"]),
        Application.deadline < now,
    )
    evc_visit_query = db.query(EVCAppointments, Application).join(
        Application,
        Application.id == EVCAppointments.application_id,
    ).filter(
        EVCAppointments.status == "scheduled",
        EVCAppointments.scheduled_date < now,
        Application.status.notin_(["approved", "rejected"]),
    )
    if user.role == "institution":
        evc_app_query = evc_app_query.filter(Application.institution_id == user.institution_id)
        evc_visit_query = evc_visit_query.filter(Application.institution_id == user.institution_id)
    elif user.role == "regional_officer":
        evc_app_query = evc_app_query.filter(Application.region == user.region)
        evc_visit_query = evc_visit_query.filter(Application.region == user.region)
    elif user.role == "evc_committee":
        evc_app_query = evc_app_query.filter(Application.current_stage.in_(["evc_scheduling", "evc_completion"]))
        evc_visit_query = evc_visit_query.filter(Application.current_stage.in_(["evc_scheduling", "evc_completion"]))
    overdue_evc_count = evc_app_query.count() + evc_visit_query.count()
    overdue_count = sum(item.deadline is not None and item.deadline < now for item in open_apps)
    doc_query = db.query(Documents)
    if user.role == "institution":
        doc_query = doc_query.filter(Documents.institution_id == user.institution_id)
    elif user.role == "regional_officer":
        region_institutions = [
            item.id for item in db.query(Institution.id).filter_by(region=user.region).all()
        ]
        doc_query = doc_query.filter(
            Documents.institution_id.in_(region_institutions)
            | (Documents.application_id.in_(app_ids) if app_ids else Documents.id == -1)
        )
    elif user.role == "evc_committee":
        doc_query = doc_query.filter(Documents.id == -1)
    documents = doc_query.all()
    expired = sum(compute_document_status(item, reminder_intervals(db))[0] == "expired" for item in documents)
    kpis = [
        {"label": "Total Applications", "value": len(applications), "change": "NEXORA DB"},
        {"label": "Pending Applications", "value": len(open_apps), "change": "NEXORA DB"},
        {"label": "Under Scrutiny", "value": sum(item.current_stage in {"initial_scrutiny", "deficiency_check"} for item in applications), "change": "NEXORA DB"},
        {"label": "Awaiting EVC", "value": awaiting_evc, "change": "NEXORA DB"},
        {"label": "Awaiting Committee Review", "value": awaiting_committee, "change": "NEXORA DB"},
        {"label": "Compliance Due Soon", "value": compliance_due_soon_count, "change": "Next 30 days"},
        {"label": "Overdue Compliance", "value": overdue_compliance_count, "change": "NEXORA DB"},
        {"label": "Overdue EVC Actions", "value": overdue_evc_count, "change": "Queue deadlines & missed visits"},
        {"label": "Overdue Cases", "value": overdue_count, "change": "NEXORA DB"},
        {"label": "Expired Documents", "value": expired, "change": "NEXORA DB"},
    ]
    status_counts = Counter(item.status for item in applications)
    region_counts = Counter(item.region for item in open_apps)
    stage_counts = Counter(item.current_stage for item in applications)
    monthly_counts = Counter(item.submitted_at.strftime("%Y-%m") for item in applications if item.submitted_at)
    undertakings = db.query(Undertakings)
    if user.role == "institution":
        undertakings = undertakings.filter(Undertakings.institution_id == user.institution_id)
    elif user.role == "regional_officer":
        region_institutions = [item.id for item in db.query(Institution.id).filter_by(region=user.region).all()]
        undertakings = undertakings.filter(Undertakings.institution_id.in_(region_institutions))
    elif user.role == "evc_committee":
        undertakings = undertakings.filter(Undertakings.id == -1)
    compliance_rows = undertakings.all()
    comp_by_category = Counter()
    comp_verified = Counter()
    for item in compliance_rows:
        category = "Undertakings"
        comp_by_category[category] += 1
        if item.status == "verified":
            comp_verified[category] += 1
    deadlines = [
        {
            "id": item.id, "kind": "Application", "title": item.id,
            "due_date": item.deadline.isoformat(), "status": item.status,
        }
        for item in open_apps if item.deadline and item.deadline <= now + timedelta(days=30)
    ]
    deadlines += [
        {
            "id": item.id, "kind": "Compliance", "title": item.description,
            "due_date": item.due_date.isoformat(), "status": item.status,
        }
        for item in compliance_rows
        if item.status != "verified" and item.due_date <= now + timedelta(days=30)
    ]
    submission_rows = db.query(ComplianceSubmissions)
    if user.role == "institution":
        submission_rows = submission_rows.filter(
            ComplianceSubmissions.institution_id == user.institution_id
        )
    elif user.role == "regional_officer":
        region_institutions = [
            item.id for item in db.query(Institution.id).filter_by(region=user.region).all()
        ]
        submission_rows = submission_rows.filter(
            ComplianceSubmissions.institution_id.in_(region_institutions)
        )
    elif user.role == "evc_committee":
        submission_rows = submission_rows.filter(ComplianceSubmissions.id == -1)
    deadlines += [
        {
            "id": item.id, "kind": "Compliance submission", "title": item.description,
            "due_date": item.due_date.isoformat(), "status": item.verification_status,
        }
        for item in submission_rows.all()
        if item.verification_status != "verified" and item.due_date <= now + timedelta(days=30)
    ]
    evc_application_rows = db.query(Application).filter(
        Application.current_stage.in_(["evc_scheduling", "evc_completion"]),
        Application.status.notin_(["approved", "rejected"]),
        Application.deadline.is_not(None),
        Application.deadline <= now + timedelta(days=30),
    )
    evc_appointment_rows = db.query(EVCAppointments, Application).join(
        Application,
        Application.id == EVCAppointments.application_id,
    ).filter(
        EVCAppointments.status == "scheduled",
        EVCAppointments.scheduled_date <= now + timedelta(days=30),
        Application.status.notin_(["approved", "rejected"]),
    )
    if user.role == "institution":
        evc_application_rows = evc_application_rows.filter(
            Application.institution_id == user.institution_id
        )
        evc_appointment_rows = evc_appointment_rows.filter(
            Application.institution_id == user.institution_id
        )
    elif user.role == "regional_officer":
        evc_application_rows = evc_application_rows.filter(Application.region == user.region)
        evc_appointment_rows = evc_appointment_rows.filter(Application.region == user.region)
    elif user.role == "evc_committee":
        evc_application_rows = evc_application_rows.filter(Application.id.in_(app_ids))
        evc_appointment_rows = evc_appointment_rows.filter(Application.id.in_(app_ids))
    deadlines += [
        {
            "id": item.id, "kind": "EVC stage", "title": item.id,
            "due_date": item.deadline.isoformat(),
            "status": "overdue" if item.deadline < now else item.current_stage,
        }
        for item in evc_application_rows.all()
    ]
    deadlines += [
        {
            "id": appointment.id, "kind": "EVC visit",
            "title": application.id,
            "due_date": appointment.scheduled_date.isoformat(),
            "status": "overdue" if appointment.scheduled_date < now else appointment.status,
        }
        for appointment, application in evc_appointment_rows.all()
    ]
    deadlines += [
        {
            "id": item.id, "kind": "Document", "title": item.file_name,
            "due_date": item.expiry_date.isoformat(),
            "status": compute_document_status(item, reminder_intervals(db))[0],
        }
        for item in documents
        if item.expiry_date and item.expiry_date <= now + timedelta(days=30)
    ]
    overdue = sorted(
        (item for item in deadlines if datetime.fromisoformat(item["due_date"]) < now),
        key=lambda item: item["due_date"],
        reverse=True,
    )
    upcoming = sorted(
        (item for item in deadlines if datetime.fromisoformat(item["due_date"]) >= now),
        key=lambda item: item["due_date"],
    )
    attention_queue = (overdue[:5] + upcoming[:5])[:10]
    return {
        "kpis": kpis,
        "statusDistribution": [{"name": key, "value": value} for key, value in sorted(status_counts.items())],
        "regionPendency": [{"region": key, "value": value} for key, value in sorted(region_counts.items())],
        "stageDistribution": [{"name": key, "value": value} for key, value in sorted(stage_counts.items())],
        "monthlyTrend": [{"month": key, "applications": value} for key, value in sorted(monthly_counts.items())],
        "complianceCompletion": [
            {"name": key, "percent": round(comp_verified[key] * 100 / count) if count else 0}
            for key, count in sorted(comp_by_category.items())
        ],
        "upcomingDeadlines": upcoming[:10],
        "attentionQueue": attention_queue,
        "attentionSummary": {"overdue": len(overdue), "dueSoon": len(upcoming)},
    }
