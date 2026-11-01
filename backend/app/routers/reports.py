import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import (
    Application, AuditLogs, Documents, EVCAppointments, Escalations, Institution,
    User, Undertakings,
)
from app.services.expiry import compute_document_status, reminder_intervals

router = APIRouter(prefix="/api/reports", tags=["reports"])


def safe_csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    formula_candidate = text.lstrip(" \t\r\n")
    if formula_candidate.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    if text.startswith(("\t", "\r")):
        return f"'{text}"
    return text


def scoped_apps(
    db: Session,
    user: User,
    region: str | None = None,
    application_type: str | None = None,
    status: str | None = None,
    stage: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
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
    if status:
        query = query.filter(Application.status == status)
    if stage:
        query = query.filter(Application.current_stage == stage)
    if start_date:
        query = query.filter(Application.submitted_at >= start_date)
    if end_date:
        query = query.filter(Application.submitted_at <= end_date)
    return query.all()


def csv_response(filename: str, headers: list[str], rows: list[list[object]]):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows([[safe_csv_cell(value) for value in row] for row in rows])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{report_name}.csv")
def get_report(
               report_name: str,
               region: str | None = None,
               application_type: str | None = None,
               status: str | None = None,
               stage: str | None = None,
               start_date: datetime | None = None,
               end_date: datetime | None = None,
               db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    apps = scoped_apps(db, user, region, application_type, status, stage, start_date, end_date)
    institution_names = {item.id: item.name for item in db.query(Institution).all()}
    now = datetime.utcnow()
    if report_name == "applications-pendency":
        rows = [[a.id, institution_names.get(a.institution_id, ""), a.region, a.application_type,
                 a.current_stage, a.status, (now - a.submitted_at).days if a.submitted_at else 0,
                 a.deadline or ""] for a in apps]
        return csv_response("applications-pendency.csv",
                            ["id", "institution", "region", "type", "stage", "status", "days_pending", "deadline"], rows)
    if report_name == "region-performance":
        grouped = {}
        for app in apps:
            data = grouped.setdefault(
                app.region,
                {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "processing_days": 0},
            )
            data["total"] += 1
            data[app.status if app.status in {"approved", "rejected"} else "pending"] += 1
            if app.submitted_at and app.updated_at:
                data["processing_days"] += max(0, (app.updated_at - app.submitted_at).days)
        rows = [[region, data["total"], data["pending"], data["approved"], data["rejected"],
                 round(data["processing_days"] / data["total"], 1)]
                for region, data in sorted(grouped.items())]
        return csv_response("region-performance.csv",
                            ["region", "total", "pending", "approved", "rejected", "avg_days"], rows)
    if report_name == "evc":
        ids = [item.id for item in apps]
        appointments = db.query(EVCAppointments).filter(EVCAppointments.application_id.in_(ids)).all() if ids else []
        rows = [[x.id, x.application_id, x.scheduled_date, x.status, x.completed_at,
                 next((a.region for a in apps if a.id == x.application_id), "")] for x in appointments]
        return csv_response("evc.csv",
                            ["appointment_id", "application", "scheduled_date", "status", "completed_at", "region"], rows)
    if report_name == "compliance":
        query = db.query(Undertakings)
        if user.role == "institution":
            query = query.filter_by(institution_id=user.institution_id)
        elif user.role == "regional_officer":
            region_institutions = [item.id for item in db.query(Institution.id).filter_by(region=user.region).all()]
            query = query.filter(Undertakings.institution_id.in_(region_institutions))
        elif user.role == "evc_committee":
            query = query.filter(Undertakings.id == -1)
        rows = [[institution_names.get(x.institution_id, ""), x.application_id or "", x.description,
                 x.due_date, x.status, (x.due_date.date() - now.date()).days, x.verifying_officer_id or ""]
                for x in query.all()]
        return csv_response("compliance.csv",
                            ["institution", "application", "description", "due_date", "status", "days_remaining", "officer"], rows)
    if report_name == "documents":
        query = db.query(Documents)
        if user.role == "institution":
            query = query.filter_by(institution_id=user.institution_id)
        elif user.role == "regional_officer":
            region_institutions = [item.id for item in db.query(Institution.id).filter_by(region=user.region).all()]
            query = query.filter(Documents.institution_id.in_(region_institutions))
        elif user.role == "evc_committee":
            query = query.filter(Documents.id == -1)
        docs = query.filter(Documents.expiry_date.is_not(None)).all()
        intervals = reminder_intervals(db)
        rows = [[institution_names.get(x.institution_id, ""), x.category,
                 compute_document_status(x, intervals)[0], x.expiry_date,
                 (x.expiry_date.date() - now.date()).days] for x in docs]
        return csv_response("documents.csv", ["institution", "category", "status", "expiry_date", "days_to_expiry"], rows)
    if report_name == "overdue":
        escalations = db.query(Escalations).filter(
            Escalations.application_id.in_([item.id for item in apps])
        ).all() if apps else []
        levels = {}
        for item in escalations:
            levels[item.application_id] = max(levels.get(item.application_id, 0), item.level)
        rows = [[a.id, a.id, a.region, (now.date() - a.deadline.date()).days,
                 levels.get(a.id, 0)] for a in apps
                if a.deadline and a.deadline < now and a.status not in {"approved", "rejected"}]
        return csv_response("overdue.csv", ["kind", "record_id", "region", "days_overdue", "escalated_level"], rows)
    if report_name == "decisions":
        final_apps = [a for a in apps if a.status in {"approved", "rejected"}]
        decisions = db.query(AuditLogs).filter(
            AuditLogs.affected_record_type == "application",
            AuditLogs.affected_record_id.in_([item.id for item in final_apps]),
            AuditLogs.updated_status.in_(["approved", "rejected"]),
        ).order_by(AuditLogs.timestamp.desc()).all() if final_apps else []
        decision_by_id = {}
        for decision in decisions:
            decision_by_id.setdefault(decision.affected_record_id, decision)
        rows = [[a.id, institution_names.get(a.institution_id, ""), a.region, a.status,
                 decision_by_id[a.id].user_id if a.id in decision_by_id else (a.assigned_officer_id or ""),
                 decision_by_id[a.id].timestamp if a.id in decision_by_id else a.updated_at,
                 decision_by_id[a.id].reason if a.id in decision_by_id else ""]
                for a in final_apps]
        return csv_response("decisions.csv",
                            ["application_id", "institution", "region", "final_status", "decided_by", "decided_at", "reason"], rows)
    raise HTTPException(status_code=404, detail="Unknown report")
