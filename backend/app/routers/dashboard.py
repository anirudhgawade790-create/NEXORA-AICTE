from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Application, Documents, Institution, User, Undertakings
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
    overdue_count = sum(item.deadline is not None and item.deadline < now for item in open_apps)
    doc_query = db.query(Documents)
    if user.role == "institution":
        doc_query = doc_query.filter(Documents.institution_id == user.institution_id)
    elif user.role == "regional_officer" and app_ids:
        doc_query = doc_query.filter(
            (Documents.institution_id.in_(
                [item.institution_id for item in applications]
            )) | (Documents.application_id.in_(app_ids))
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
        {"label": "Compliance Due Soon", "value": due_soon.count(), "change": "Next 30 days"},
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
