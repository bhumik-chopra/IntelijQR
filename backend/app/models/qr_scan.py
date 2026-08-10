from dataclasses import dataclass
from datetime import datetime
from typing import Literal


QrScanSource = Literal["upload", "webcam"]
QrContentType = Literal[
    "website", "email", "contact", "phone", "wifi", "payment",
    "event", "pdf", "image", "social_media", "location", "text",
]


@dataclass(frozen=True, slots=True)
class QrScan:
    id: str
    user_id: str
    content: str
    content_hash: str
    content_type: QrContentType
    source: QrScanSource
    metadata: dict
    security: dict | None
    created_at: datetime
