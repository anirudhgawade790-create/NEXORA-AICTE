from app.models import AuditLogs, User
from sqlalchemy.orm import Session


def log_action(
    db: Session,
    user: User | None,
    action: str,
    record_type: str,
    record_id: str | int,
    previous_status: str | None = None,
    updated_status: str | None = None,
    reason: str | None = None,
    workflow_stage: str | None = None,
) -> AuditLogs:
    entry = AuditLogs(
        user_id=user.id if user else None,
        action=action,
        affected_record_type=record_type,
        affected_record_id=str(record_id),
        previous_status=previous_status,
        updated_status=updated_status,
        reason=reason,
        workflow_stage=workflow_stage,
    )
    db.add(entry)
    return entry
