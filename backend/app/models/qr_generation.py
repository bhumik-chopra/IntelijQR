from dataclasses import dataclass
from datetime import datetime
from typing import Literal


QrPayloadType = Literal["url", "text", "email", "phone", "wifi", "contact", "location"]
QrFileFormat = Literal["png", "svg", "pdf"]
QrStatus = Literal["active", "paused", "expired", "scan_limit_reached"]
QrAccessMode = Literal["public", "password", "authenticated", "private"]


@dataclass(frozen=True, slots=True)
class QrDesign:
    foreground_color: str = "#111827"
    background_color: str = "#FFFFFF"
    gradient_enabled: bool = False
    gradient_color: str = "#7C3AED"
    gradient_direction: Literal["horizontal", "vertical", "diagonal"] = "diagonal"
    module_style: Literal["square", "rounded", "dots"] = "square"
    frame_style: Literal["none", "square", "rounded"] = "none"
    frame_text: str | None = None
    error_correction: Literal["L", "M", "Q", "H"] = "H"
    size: int = 1024
    margin: int = 4


@dataclass(frozen=True, slots=True)
class QrGeneration:
    id: str
    user_id: str
    payload_type: QrPayloadType
    label: str | None
    payload_preview: str
    payload_hash: str
    payload_details: dict
    files: dict[QrFileFormat, str]
    slug: str
    dynamic_url: str | None
    destination_url: str | None
    encrypted_destination: str | None
    access_mode: QrAccessMode
    access_password_hash: str | None
    allowed_emails: list[str]
    is_active: bool
    is_favorite: bool
    expires_at: datetime | None
    max_scans: int | None
    scan_count: int
    design: dict
    logo_file: str | None
    created_at: datetime
    updated_at: datetime

    @property
    def status(self) -> QrStatus:
        from datetime import timezone

        now = datetime.now(timezone.utc)
        if not self.is_active:
            return "paused"
        if self.expires_at is not None and self.expires_at <= now:
            return "expired"
        if self.max_scans is not None and self.scan_count >= self.max_scans:
            return "scan_limit_reached"
        return "active"
