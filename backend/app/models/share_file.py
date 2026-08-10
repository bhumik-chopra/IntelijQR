from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


ShareAccessMode = Literal["public", "password", "authenticated", "private"]


@dataclass(frozen=True, slots=True)
class ShareFile:
    id: str
    user_id: str
    slug: str
    filename: str
    media_type: str
    size: int
    content_hash: str
    stored_path: str
    qr_generation_id: str
    access_mode: ShareAccessMode
    access_password_hash: str | None
    allowed_emails: list[str]
    expires_at: datetime | None
    max_downloads: int | None
    download_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @property
    def status(self) -> str:
        if not self.is_active: return "paused"
        if self.expires_at and self.expires_at <= datetime.now(timezone.utc): return "expired"
        if self.max_downloads is not None and self.download_count >= self.max_downloads: return "download_limit_reached"
        return "active"
