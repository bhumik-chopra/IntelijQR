from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import PaginationFields


class NotificationResponse(BaseModel):
    id: str
    event_type: str
    category: str
    severity: Literal["info", "success", "warning", "critical"]
    title: str
    message: str
    action_url: str | None
    metadata: dict
    is_read: bool
    created_at: datetime


class NotificationListResponse(PaginationFields):
    items: list[NotificationResponse]
    unread_count: int


class NotificationUnreadResponse(BaseModel):
    unread_count: int


class NotificationPreferences(BaseModel):
    in_app_enabled: bool = True
    email_enabled: bool = False
    security_alerts: bool = True
    qr_activity: bool = True
    share_activity: bool = True
    bulk_activity: bool = True
    local_smtp_available: bool = False


class NotificationPreferencesUpdate(BaseModel):
    in_app_enabled: bool
    email_enabled: bool
    security_alerts: bool
    qr_activity: bool
    share_activity: bool
    bulk_activity: bool
