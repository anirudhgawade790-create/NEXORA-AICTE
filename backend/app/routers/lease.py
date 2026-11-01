from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import Documents, Institution, User
from app.routers.documents import store_upload
from app.services.audit import log_action
from app.services.notifications_service import create_notification
from app.services.expiry import compute_document_status, reminder_intervals

router = APIRouter(prefix="/api/lease", tags=["lease"])


@router.get("/dashboard")
def lease_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Documents).filter(Documents.expiry_date.is_not(None))
    if user.role == "institution":
        query = query.filter(Documents.institution_id == user.institution_id)
    elif user.role == "regional_officer":
        institution_ids = [item.id for item in db.query(Institution.id).filter_by(region=user.region).all()]
        query = query.filter(Documents.institution_id.in_(institution_ids))
    elif user.role == "evc_committee":
        query = query.filter(Documents.id == -1)
    docs = query.all()
    intervals = reminder_intervals(db)
    ids = {document.id for document in docs}
    replacements = db.query(Documents).filter(Documents.replacement_for.in_(ids)).all() if ids else []
    replaced = {item.replacement_for: item for item in replacements}
    buckets = {"Valid": [], "Expiring Soon": [], "Expired": [],
               "Renewal Awaited": [], "Renewal Under Verification": []}
    for document in docs:
        replacement = replaced.get(document.id)
        if replacement and replacement.status in {"under_verification", "uploaded"}:
            buckets["Renewal Under Verification"].append(document)
            status_value, _ = compute_document_status(document, intervals)
            if status_value == "expired":
                buckets["Expired"].append(document)
            continue
        if replacement and replacement.status == "verified":
            buckets["Valid"].append(replacement)
            continue
        status_value, days = compute_document_status(document, intervals)
        if status_value == "expired":
            buckets["Expired"].append(document)
            if replacement is None:
                buckets["Renewal Awaited"].append(document)
        elif status_value == "expiring_soon":
            buckets["Expiring Soon"].append(document)
        else:
            buckets["Valid"].append(document)
    return {
        "buckets": {key: [{"id": item.id, "category": item.category, "expiry_date": item.expiry_date,
                           "status": item.status, "replacement_for": item.replacement_for}
                          for item in values] for key, values in buckets.items()},
        "counts": {key: len(values) for key, values in buckets.items()},
        "reminder_intervals": intervals,
        "note": "Reminder windows are configurable examples, not official AICTE requirements.",
    }


@router.post("/{document_id}/renew", status_code=201)
async def renew_document(document_id: int, file: UploadFile = File(...),
                         category: str = Form("Lease Documents"),
                         expiry_date: str | None = Form(None),
                         db: Session = Depends(get_db),
                         user: User = Depends(require_roles("institution"))):
    old = db.query(Documents).filter_by(id=document_id).first()
    if old is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if old.institution_id != user.institution_id:
        raise HTTPException(status_code=403, detail="Document belongs to another institution")
    try:
        expires = datetime.fromisoformat(expiry_date) if expiry_date else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="expiry_date must be ISO formatted") from exc
    path, size = await store_upload(file)
    replacement = Documents(
        application_id=old.application_id, institution_id=user.institution_id,
        category=category, file_name=file.filename or "renewal", stored_path=str(path),
        mime_type=file.content_type or "", file_size=size, uploaded_by=user.id,
        expiry_date=expires, replacement_for=old.id, status="under_verification",
    )
    db.add(replacement)
    log_action(db, user, "lease_renewal_submitted", "document", replacement.id,
               updated_status=replacement.status, reason=f"Replaces document {old.id}")
    create_notification(
        db, "lease_renewal", replacement.id, user.id,
        f"Renewal document submitted for {old.file_name}", expires,
        "/lease",
    )
    db.commit()
    db.refresh(replacement)
    return {"id": replacement.id, "replacement_for": old.id, "status": replacement.status}
