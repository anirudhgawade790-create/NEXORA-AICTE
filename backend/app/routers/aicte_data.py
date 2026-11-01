from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import AICTEInstitutionCache, User
from app.services.aicte_data import (
    PublicDataSyncError,
    source_is_configured,
    sync_public_institutions,
    sync_status,
)

router = APIRouter(prefix="/api/aicte-data", tags=["public AICTE data"])


@router.get("")
def list_public_institutions(
    search: str | None = None,
    state: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(AICTEInstitutionCache)
    if search:
        query = query.filter(AICTEInstitutionCache.record["name"].as_string().ilike(f"%{search}%"))
    if state:
        query = query.filter(AICTEInstitutionCache.record["state"].as_string().ilike(f"%{state}%"))
    total = query.count()
    rows = query.order_by(AICTEInstitutionCache.record["name"].as_string()).offset(offset).limit(limit).all()
    return {
        "status": sync_status(db),
        "total": total,
        "records": [row.record for row in rows],
    }


@router.post("/sync")
def refresh_public_institutions(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    if not source_is_configured():
        raise HTTPException(
            status_code=503,
            detail="No verified AICTE dataset is configured. Set its official OGD resource ID, API key and dataset page, and confirm the publisher/access terms.",
        )
    try:
        return sync_public_institutions(db)
    except PublicDataSyncError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
