from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Notifications


def create_notification(
    db: Session,
    event_type: str,
    related_id: str | int | None,
    recipient_id: int,
    message: str,
    due_date: datetime | None = None,
    action_link: str | None = None,
) -> Notifications:
    item = Notifications(
        event_type=event_type,
        related_id=str(related_id) if related_id is not None else None,
        recipient_id=recipient_id,
        message=message,
        due_date=due_date,
        action_link=action_link,
    )
    db.add(item)
    return item
