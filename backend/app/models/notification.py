from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Notification:
    id: str
    user_id: str
    event_type: str
    category: str
    severity: str
    title: str
    message: str
    action_url: str | None
    metadata: dict
    is_read: bool
    created_at: datetime
