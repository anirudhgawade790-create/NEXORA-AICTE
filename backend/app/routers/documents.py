import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import check_application_access, get_current_user, require_roles
from app.models import Application, DocumentCategory, Documents, DocumentVerifications, Institution, User
from app.schemas.documents import DocumentVerifyRequest
from app.services.audit import log_action
from app.services.ocr import extract_text
from app.services.notifications_service import create_notification

router = APIRouter(prefix="/api/documents", tags=["documents"])
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
UPLOAD_DIR = Path(
    os.environ.get("UPLOAD_DIR", str(Path(__file__).resolve().parents[2] / "uploads"))
)


async def store_upload(file: UploadFile) -> tuple[Path, int]:
    extension = Path(file.filename or "").suffix.lower()
    expected_type = ALLOWED_EXTENSIONS.get(extension)
    if expected_type is None or file.content_type != expected_type:
        raise HTTPException(status_code=415, detail="Only PDF, JPG, JPEG and PNG files are accepted")
    content = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
    target = UPLOAD_DIR / safe_name
    target.write_bytes(content)
    return target, len(content)


def allowed_document(user: User, document: Documents, db: Session) -> None:
    if user.role in {"admin", "bureau_officer"}:
        return
    if user.role == "regional_officer":
        if document.application_id:
            application = db.query(Application).filter_by(id=document.application_id).first()
            if application:
                check_application_access(user, application)
            elif document.institution_id:
                institution = db.query(Institution).filter_by(id=document.institution_id).first()
                if institution and institution.region != user.region:
                    raise HTTPException(status_code=403, detail="Document is outside your region")
        elif document.institution_id:
            institution = db.query(Institution).filter_by(id=document.institution_id).first()
            if institution and institution.region != user.region:
                raise HTTPException(status_code=403, detail="Document is outside your region")
        return
    if user.role == "evc_committee":
        raise HTTPException(status_code=403, detail="EVC committee users do not have document access")
    if user.role != "institution" or document.institution_id != user.institution_id:
        raise HTTPException(status_code=403, detail="Document belongs to another institution")


@router.post("", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(...),
    application_id: str | None = Form(None),
    expiry_date: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("institution")),
):
    application = None
    if application_id:
        application = db.query(Application).filter_by(id=application_id).first()
        if application is None:
            raise HTTPException(status_code=404, detail="Application not found")
        check_application_access(user, application)
    if db.query(DocumentCategory).filter_by(name=category).first() is None:
        raise HTTPException(status_code=400, detail="Unknown document category")
    try:
        expires = datetime.fromisoformat(expiry_date) if expiry_date else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="expiry_date must be ISO formatted") from exc
    path, size = await store_upload(file)
    document = Documents(
        application_id=application.id if application else None,
        institution_id=user.institution_id,
        category=category,
        file_name=Path(file.filename or "upload").name,
        stored_path=str(path),
        mime_type=file.content_type or "",
        file_size=size,
        uploaded_by=user.id,
        expiry_date=expires,
        status="under_verification",
    )
    text, attempted, note = extract_text(str(path), document.mime_type)
    document.ocr_text = text
    db.add(document)
    db.flush()
    db.add(DocumentVerifications(
        document_id=document.id, verifier_id=user.id, status="under_verification",
        is_ocr_attempted=attempted, ocr_summary=note,
    ))
    log_action(db, user, "document_uploaded", "document", document.id,
               updated_status=document.status)
    if application and application.assigned_officer_id:
        create_notification(
            db, "pending_verification", document.id, application.assigned_officer_id,
            f"Document {document.file_name} needs verification", action_link=f"/documents",
        )
    db.commit()
    db.refresh(document)
    return {"id": document.id, "file_name": document.file_name, "category": document.category,
            "status": document.status, "ocr_summary": note, "file_size": size}


@router.get("")
def list_documents(
    application_id: str | None = None,
    category: str | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Documents)
    if user.role == "institution":
        query = query.filter(Documents.institution_id == user.institution_id)
    elif user.role == "regional_officer":
        institution_ids = [item.id for item in db.query(Institution).filter_by(region=user.region).all()]
        query = query.filter(Documents.institution_id.in_(institution_ids))
    elif user.role == "evc_committee":
        query = query.filter(Documents.id == -1)
    if application_id:
        query = query.filter(Documents.application_id == application_id)
    if category:
        query = query.filter(Documents.category == category)
    if status_filter:
        query = query.filter(Documents.status == status_filter)
    documents = query.order_by(Documents.uploaded_at.desc()).all()
    ids = [item.id for item in documents]
    verifications = db.query(DocumentVerifications).filter(
        DocumentVerifications.document_id.in_(ids)
    ).order_by(DocumentVerifications.created_at.desc()).all() if ids else []
    summary_by_id = {}
    for verification in verifications:
        if verification.ocr_summary:
            summary_by_id.setdefault(verification.document_id, verification.ocr_summary)
    return [
        {
            "id": item.id,
            "application_id": item.application_id,
            "institution_id": item.institution_id,
            "category": item.category,
            "file_name": item.file_name,
            "status": item.status,
            "expiry_date": item.expiry_date,
            "file_size": item.file_size,
            "uploaded_at": item.uploaded_at,
            "ocr_summary": summary_by_id.get(item.id),
        }
        for item in documents
    ]


@router.get("/{document_id}/metadata")
def document_metadata(document_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    document = db.query(Documents).filter_by(id=document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    allowed_document(user, document, db)
    return {"id": document.id, "file_name": document.file_name, "category": document.category,
            "mime_type": document.mime_type, "file_size": document.file_size,
            "status": document.status, "uploaded_at": document.uploaded_at,
            "expiry_date": document.expiry_date, "ocr_text": document.ocr_text,
            "ocr_summary": db.query(DocumentVerifications.ocr_summary).filter_by(
                document_id=document.id
            ).filter(DocumentVerifications.ocr_summary.is_not(None)).order_by(
                DocumentVerifications.created_at.desc()
            ).scalar()}


@router.get("/{document_id}/file")
def document_file(document_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    document = db.query(Documents).filter_by(id=document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    allowed_document(user, document, db)
    path = Path(document.stored_path).resolve()
    if not path.is_relative_to(UPLOAD_DIR.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Stored document file is unavailable")
    return FileResponse(path, media_type=document.mime_type, filename=document.file_name)


@router.post("/{document_id}/verify")
def verify_document(document_id: int, payload: DocumentVerifyRequest,
                    db: Session = Depends(get_db),
                    user: User = Depends(require_roles("regional_officer", "bureau_officer", "admin"))):
    if payload.status not in {"verified", "deficient", "rejected"} or not payload.remarks.strip():
        raise HTTPException(status_code=400, detail="Choose a valid status and provide remarks")
    document = db.query(Documents).filter_by(id=document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    allowed_document(user, document, db)
    previous = document.status
    document.status = payload.status
    document.verified_by = user.id
    document.verified_at = datetime.utcnow()
    db.add(DocumentVerifications(
        document_id=document.id, verifier_id=user.id, status=payload.status,
        remarks=payload.remarks,
    ))
    log_action(db, user, "document_verified", "document", document.id,
               previous, payload.status, payload.remarks)
    institution_user = db.query(User).filter_by(
        institution_id=document.institution_id, role="institution", is_active=True
    ).first()
    if institution_user:
        create_notification(
            db, "document_verification", document.id, institution_user.id,
            f"Document {document.file_name} marked {payload.status}: {payload.remarks}",
            action_link="/documents",
        )
    db.commit()
    return {"id": document.id, "status": document.status, "remarks": payload.remarks}
