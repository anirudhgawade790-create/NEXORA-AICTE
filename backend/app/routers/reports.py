import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import (
    Application, AuditLogs, ComplianceSubmissions, Documents, EVCAppointments,
    Escalations, Institution, User, Undertakings,
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
        appointments = db.query(EVCAppointments).filter(
            EVCAppointments.application_id.in_(ids)
        ).all() if ids else []
        app_by_id = {application.id: application for application in apps}
        levels = {
            (item.record_type, item.record_id): item.level
            for item in db.query(Escalations).filter(
                Escalations.record_type == "evc"
            ).all()
        }
        rows = [
            [
                "EVC stage",
                application.id,
                application.region,
                application.deadline or "",
                application.current_stage,
                max(0, (now.date() - application.deadline.date()).days)
                if application.deadline and application.deadline < now else 0,
                levels.get(("evc", f"application:{application.id}"), 0),
            ]
            for application in apps
            if application.current_stage in {"evc_scheduling", "evc_completion"}
            and application.status not in {"approved", "rejected"}
        ]
        rows += [
            [
                "EVC visit",
                appointment.application_id,
                app_by_id[appointment.application_id].region
                if appointment.application_id in app_by_id else "",
                appointment.scheduled_date,
                appointment.status,
                max(0, (now.date() - appointment.scheduled_date.date()).days)
                if appointment.status == "scheduled" and appointment.scheduled_date < now else 0,
                levels.get(("evc", f"appointment:{appointment.id}"), 0),
            ]
            for appointment in appointments
        ]
        return csv_response("evc.csv",
                            ["record_type", "application_id", "region", "due_at", "status",
                             "days_overdue", "escalation_level"], rows)
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
        levels: dict[tuple[str, str], int] = {}
        for item in escalations:
            levels[("application", item.application_id or item.record_id or "")] = max(
                levels.get(("application", item.application_id or item.record_id or ""), 0),
                item.level,
            )

        region_institutions = [
            item.id for item in db.query(Institution.id).filter_by(region=user.region).all()
        ] if user.role == "regional_officer" else []

        def scope_institution_records(query, model):
            if user.role == "institution":
                return query.filter(model.institution_id == user.institution_id)
            if user.role == "regional_officer":
                return query.filter(model.institution_id.in_(region_institutions))
            if user.role == "evc_committee":
                return query.filter(model.id == -1)
            return query

        compliance = scope_institution_records(
            db.query(Undertakings).filter(
                Undertakings.due_date < now,
                Undertakings.status != "verified",
            ),
            Undertakings,
        ).all()
        submissions = scope_institution_records(
            db.query(ComplianceSubmissions).filter(
                ComplianceSubmissions.due_date < now,
                ComplianceSubmissions.verification_status != "verified",
            ),
            ComplianceSubmissions,
        ).all()
        documents = scope_institution_records(
            db.query(Documents).filter(Documents.expiry_date < now),
            Documents,
        ).all()
        related_escalations = db.query(Escalations).filter(
            Escalations.record_type.in_(["undertaking", "compliance_submission", "document"])
        ).all()
        for item in related_escalations:
            key = (item.record_type or "", item.record_id or "")
            levels[key] = max(levels.get(key, 0), item.level)

        institutions = {item.id: item for item in db.query(Institution).all()}
        rows = [
            [
                "Application", item.id, item.region,
                (now.date() - item.deadline.date()).days,
                levels.get(("application", item.id), 0),
            ]
            for item in apps
            if item.deadline and item.deadline < now and item.status not in {"approved", "rejected"}
        ]
        rows += [
            [
                "Undertaking", str(item.id),
                institutions.get(item.institution_id).region if institutions.get(item.institution_id) else "",
                (now.date() - item.due_date.date()).days,
                levels.get(("undertaking", str(item.id)), 0),
            ]
            for item in compliance
        ]
        rows += [
            [
                "Compliance submission", str(item.id),
                institutions.get(item.institution_id).region if institutions.get(item.institution_id) else "",
                (now.date() - item.due_date.date()).days,
                levels.get(("compliance_submission", str(item.id)), 0),
            ]
            for item in submissions
        ]
        rows += [
            [
                "Document", str(item.id),
                institutions.get(item.institution_id).region if item.institution_id and institutions.get(item.institution_id) else "",
                (now.date() - item.expiry_date.date()).days,
                levels.get(("document", str(item.id)), 0),
            ]
            for item in documents
        ]
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
