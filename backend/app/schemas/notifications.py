from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    event_type: str
    related_id: str | None
    message: str
    is_read: bool
    action_link: str | None
