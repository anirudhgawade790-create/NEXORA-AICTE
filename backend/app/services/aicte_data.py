"""Authorized public AICTE institution-data synchronization."""

import hashlib
import json
import re
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import AICTEInstitutionCache, AICTESyncState

OGD_RESOURCE_URL = "https://api.data.gov.in/resource"
OGD_RESOURCE_ID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
PAGE_SIZE = 1000
MAX_RECORDS = 100_000
REQUEST_TIMEOUT_SECONDS = 20


class PublicDataSyncError(Exception):
    """Raised when a configured public dataset cannot be synchronized."""


def source_is_configured() -> bool:
    dataset_url = urlsplit(settings.AICTE_DATASET_PAGE_URL.strip())
    return bool(
        settings.AICTE_OGD_API_KEY.strip()
        and OGD_RESOURCE_ID_PATTERN.fullmatch(settings.AICTE_OGD_RESOURCE_ID.strip())
        and settings.AICTE_OGD_PUBLISHER_VERIFIED
        and dataset_url.scheme == "https"
        and dataset_url.hostname in {"data.gov.in", "www.data.gov.in", "aicte.gov.in", "www.aicte.gov.in"}
    )


def _official_dataset_url() -> str:
    value = settings.AICTE_DATASET_PAGE_URL.strip()
    parsed = urlsplit(value)
    if parsed.scheme == "https" and parsed.username is None and parsed.password is None and parsed.hostname in {
        "data.gov.in", "www.data.gov.in", "aicte.gov.in", "www.aicte.gov.in",
    }:
        return value
    return "https://data.gov.in/"


def _first_value(record: dict, aliases: tuple[str, ...]):
    normalized = {str(key).strip().lower().replace(" ", "_"): value for key, value in record.items()}
    for alias in aliases:
        value = normalized.get(alias)
        if value is not None and str(value).strip():
            return value
    return None


def _as_courses(value) -> list[str]:
    if isinstance(value, list):
        values = value
    elif value is None:
        values = []
    else:
        values = re.split(r"[;\n|]", str(value))
    return list(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))


def normalize_records(records: list[dict], synchronized_at: datetime) -> list[dict]:
    grouped: dict[str, dict] = {}
    for raw in records:
        if not isinstance(raw, dict):
            continue
        academic_year = _first_value(
            raw, ("academic_year", "academic_session", "approval_year")
        )
        institute_count = _first_value(
            raw,
            (
                "number_of_government_engineering_institutes",
                "government_engineering_institutes",
            ),
        )
        approved_seats = _first_value(
            raw,
            (
                "approved_seats_in_government_engineering_institutes",
                "government_engineering_institute_approved_seats",
            ),
        )
        if academic_year is not None and institute_count is not None and approved_seats is not None:
            item = {
                "record_type": "aggregate",
                "aicte_id": None,
                "name": "Government Engineering Institutes (aggregate)",
                "state": None,
                "district": None,
                "city": None,
                "address": None,
                "approved_courses": [],
                "approval_status": None,
                "academic_year": str(academic_year).strip(),
                "source_updated_at": _first_value(
                    raw, ("updated_at", "last_updated", "data_updated_at")
                ),
                "government_engineering_institutes_count": institute_count,
                "approved_seats_count": approved_seats,
                "synchronized_at": synchronized_at.isoformat(),
            }
            record_key = hashlib.sha256(
                json.dumps(raw, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            grouped[record_key] = item
            continue
        aicte_id = _first_value(
            raw, ("aicte_id", "aicteid", "institute_id", "institution_id", "permanent_id")
        )
        name = _first_value(
            raw, ("institution_name", "institute_name", "college_name", "name")
        )
        if not name:
            continue
        aicte_id = str(aicte_id).strip() if aicte_id is not None else None
        key_source = aicte_id or json.dumps(raw, sort_keys=True, default=str)
        record_key = hashlib.sha256(key_source.encode("utf-8")).hexdigest()
        item = grouped.setdefault(record_key, {
            "record_type": "institution",
            "aicte_id": aicte_id,
            "name": str(name).strip(),
            "state": _first_value(raw, ("state", "state_name")),
            "district": _first_value(raw, ("district", "district_name")),
            "city": _first_value(raw, ("city", "town")),
            "address": _first_value(raw, ("address", "institution_address")),
            "approved_courses": [],
            "approval_status": _first_value(
                raw, ("approval_status", "approval", "status_of_approval", "status")
            ),
            "academic_year": academic_year,
            "source_updated_at": _first_value(
                raw, ("updated_at", "last_updated", "data_updated_at")
            ),
            "synchronized_at": synchronized_at.isoformat(),
        })
        item["approved_courses"] = list(dict.fromkeys(
            item["approved_courses"] + _as_courses(_first_value(
                raw, ("approved_courses", "course_name", "programme_name", "program_name", "course")
            ))
        ))
    return list(grouped.values())


def _fetch_page(offset: int) -> dict:
    resource_id = settings.AICTE_OGD_RESOURCE_ID.strip()
    if not OGD_RESOURCE_ID_PATTERN.fullmatch(resource_id):
        raise PublicDataSyncError("The configured OGD resource ID is invalid.")
    query = urlencode({
        "api-key": settings.AICTE_OGD_API_KEY.strip(),
        "format": "json",
        "limit": PAGE_SIZE,
        "offset": offset,
    })
    request = Request(
        f"{OGD_RESOURCE_URL}/{resource_id}?{query}",
        headers={"Accept": "application/json", "User-Agent": "NEXORA-AICTE/1.0"},
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = response.read(10_000_001)
            if len(body) > 10_000_000:
                raise PublicDataSyncError("Open Government Data API response exceeded the 10 MB page limit.")
            payload = json.loads(body)
    except HTTPError as exc:
        raise PublicDataSyncError(f"Open Government Data API returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise PublicDataSyncError("Open Government Data API could not be reached.") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PublicDataSyncError("Open Government Data API returned invalid JSON.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise PublicDataSyncError("The configured dataset did not return a records array.")
    return payload


def _fetch_all_records() -> list[dict]:
    all_records: list[dict] = []
    offset = 0
    while True:
        payload = _fetch_page(offset)
        page = payload["records"]
        all_records.extend(page)
        total = payload.get("total")
        if len(all_records) > MAX_RECORDS:
            raise PublicDataSyncError(f"Dataset exceeds the {MAX_RECORDS} record safety limit.")
        if not page or len(page) < PAGE_SIZE:
            break
        if total is not None and offset + len(page) >= int(total):
            break
        offset += len(page)
    return all_records


def sync_public_institutions(db: Session) -> dict:
    state = db.query(AICTESyncState).filter_by(id=1).first()
    if state is None:
        state = AICTESyncState(id=1, status="not_configured")
        db.add(state)
        db.flush()
    now = datetime.utcnow()
    state.last_attempt_at = now
    if not source_is_configured():
        state.status = "not_configured"
        state.last_error = (
            "Configure the documented OGD resource ID and API key, an official dataset page, "
            "and confirm the AICTE publisher/access terms."
        )
        db.commit()
        return sync_status(db)

    try:
        raw_records = _fetch_all_records()
        records = normalize_records(raw_records, now)
        if raw_records and not records:
            raise PublicDataSyncError(
                "The dataset returned records, but no institution names matched the supported documented fields."
            )
        db.query(AICTEInstitutionCache).delete(synchronize_session=False)
        for record in records:
            record_key = hashlib.sha256(
                (record["aicte_id"] or json.dumps(record, sort_keys=True)).encode("utf-8")
            ).hexdigest()
            db.add(AICTEInstitutionCache(
                record_key=record_key,
                record=record,
                synchronized_at=now,
            ))
        state.status = "available"
        state.last_success_at = now
        state.last_error = None
        state.record_count = len(records)
        db.commit()
    except Exception as exc:
        db.rollback()
        state = db.query(AICTESyncState).filter_by(id=1).first()
        if state is None:
            state = AICTESyncState(id=1)
            db.add(state)
        state.last_attempt_at = now
        state.status = "degraded" if state.last_success_at else "unavailable"
        state.last_error = str(exc)[:500]
        db.commit()
        if isinstance(exc, PublicDataSyncError):
            raise
        raise PublicDataSyncError("Public institution data synchronization failed.") from exc
    return sync_status(db)


def sync_status(db: Session) -> dict:
    state = db.query(AICTESyncState).filter_by(id=1).first()
    configured = source_is_configured()
    if state is None:
        status = "not_configured" if not configured else "never_synced"
        last_attempt_at = last_success_at = last_error = None
        record_count = db.query(AICTEInstitutionCache).count()
    else:
        status = state.status if configured else "not_configured"
        last_attempt_at = state.last_attempt_at.isoformat() if state.last_attempt_at else None
        last_success_at = state.last_success_at.isoformat() if state.last_success_at else None
        last_error = state.last_error
        record_count = state.record_count
    dataset_url = _official_dataset_url()
    return {
        "status": status,
        "configured": configured,
        "record_count": record_count,
        "last_attempt_at": last_attempt_at,
        "last_success_at": last_success_at,
        "last_error": last_error,
        "sync_interval_minutes": settings.AICTE_SYNC_INTERVAL_MINUTES,
        "source_name": (
            "AICTE dataset via Open Government Data Platform India"
            if configured else "Open Government Data Platform India (not connected)"
        ),
        "source_url": dataset_url,
        "onod_url": "https://onod.aicte-india.org/",
        "aicte_url": "https://aicte.gov.in/",
    }


def scheduled_public_data_sync() -> None:
    db = SessionLocal()
    try:
        sync_public_institutions(db)
    except PublicDataSyncError:
        # The persisted sync status and error are surfaced in the dashboard.
        pass
    finally:
        db.close()
