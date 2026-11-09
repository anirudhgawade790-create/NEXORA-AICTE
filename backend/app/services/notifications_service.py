from datetime import datetime
import logging
import smtplib

from sqlalchemy.orm import Session

from app.models import Notifications, User
from app.services.audit import log_action

logger = logging.getLogger(__name__)


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
    db.flush()
    log_action(
        db,
        None,
        "notification_created",
        "notification",
        item.id,
        updated_status=event_type,
        reason=message,
    )
    recipient = db.query(User).filter_by(id=recipient_id, is_active=True).first()
    if recipient is not None and recipient.email:
        from app.services.notification_email import send_notification_email

        try:
            send_notification_email(recipient.email, message, action_link)
        except (OSError, ValueError, RuntimeError, smtplib.SMTPException) as exc:
            logger.error("Notification email delivery failed for user %s: %s", recipient.id, exc)
    return item
