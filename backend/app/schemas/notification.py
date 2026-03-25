from pydantic import BaseModel
from datetime import datetime
from app.models.notification import NotificationType


class NotificationOut(BaseModel):
    id: str
    user_id: str
    title: str
    body: str
    type: NotificationType
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
