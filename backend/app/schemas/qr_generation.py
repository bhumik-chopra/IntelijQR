from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator, model_validator

from app.schemas.common import PaginationFields


HEX_COLOR = r"^#[0-9A-Fa-f]{6}$"


def _luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


class QrDesignRequest(BaseModel):
    foreground_color: str = Field(default="#111827", pattern=HEX_COLOR)
    background_color: str = Field(default="#FFFFFF", pattern=HEX_COLOR)
    gradient_enabled: bool = False
    gradient_color: str = Field(default="#7C3AED", pattern=HEX_COLOR)
    gradient_direction: Literal["horizontal", "vertical", "diagonal"] = "diagonal"
    module_style: Literal["square", "rounded", "dots"] = "square"
    frame_style: Literal["none", "square", "rounded"] = "none"
    frame_text: str | None = Field(default=None, max_length=40)
    error_correction: Literal["L", "M", "Q", "H"] = "H"
    size: int = Field(default=1024, ge=256, le=2048)
    margin: int = Field(default=4, ge=0, le=10)

    @field_validator("frame_text")
    @classmethod
    def clean_frame_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None

    @model_validator(mode="after")
    def ensure_contrast(self):
        background = _luminance(self.background_color)
        colors = [self.foreground_color]
        if self.gradient_enabled:
            colors.append(self.gradient_color)
        for color in colors:
            foreground = _luminance(color)
            ratio = (max(background, foreground) + 0.05) / (min(background, foreground) + 0.05)
            if ratio < 3:
                raise ValueError("QR foreground colors require at least a 3:1 contrast ratio")
        return self


class BaseQrRequest(BaseModel):
    label: str | None = Field(default=None, max_length=80)
    expires_at: datetime | None = None
    max_scans: int | None = Field(default=None, ge=1, le=10_000_000)
    design: QrDesignRequest = Field(default_factory=QrDesignRequest)
    logo_data_url: str | None = Field(default=None, max_length=3_000_000)
    access_mode: Literal["public", "password", "authenticated", "private"] = "public"
    access_password: str | None = Field(default=None, min_length=8, max_length=72)
    allowed_emails: list[EmailStr] = Field(default_factory=list, max_length=25)

    @field_validator("label")
    @classmethod
    def clean_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("access_password")
    @classmethod
    def validate_access_password_size(cls, value: str | None) -> str | None:
        if value is not None and len(value.encode("utf-8")) > 72:
            raise ValueError("Access password must not exceed 72 UTF-8 bytes")
        return value

    @field_validator("expires_at")
    @classmethod
    def future_expiry(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if normalized <= datetime.now(timezone.utc):
            raise ValueError("Expiry must be in the future")
        return normalized

    @model_validator(mode="after")
    def valid_access_policy(self):
        if self.access_mode == "password" and not self.access_password:
            raise ValueError("A password is required for password-protected QR codes")
        if self.access_mode != "password" and self.access_password:
            raise ValueError("An access password can only be used with password protection")
        if self.access_mode == "private" and not self.allowed_emails:
            raise ValueError("At least one allowed email is required for private sharing")
        if self.access_mode != "private" and self.allowed_emails:
            raise ValueError("Allowed emails can only be used with private sharing")
        return self


class UrlQrRequest(BaseQrRequest):
    type: Literal["url"]
    url: HttpUrl
    dynamic: bool = True

    @model_validator(mode="after")
    def direct_url_has_no_server_controls(self):
        if not self.dynamic:
            if self.access_mode != "public":
                raise ValueError("Protected URL QR codes require dynamic mode")
            if self.expires_at is not None or self.max_scans is not None:
                raise ValueError("Expiry and scan limits require dynamic mode")
        return self


class TextQrRequest(BaseQrRequest):
    type: Literal["text"]
    text: str = Field(min_length=1, max_length=4000)


class EmailQrRequest(BaseQrRequest):
    type: Literal["email"]
    email: EmailStr
    subject: str | None = Field(default=None, max_length=200)
    body: str | None = Field(default=None, max_length=2000)


class PhoneQrRequest(BaseQrRequest):
    type: Literal["phone"]
    phone: str = Field(min_length=3, max_length=32, pattern=r"^\+?[0-9().\- ]+$")


class WifiQrRequest(BaseQrRequest):
    type: Literal["wifi"]
    ssid: str = Field(min_length=1, max_length=64)
    password: str = Field(default="", max_length=128)
    security: Literal["WPA", "WEP", "nopass"] = "WPA"
    hidden: bool = False


class ContactQrRequest(BaseQrRequest):
    type: Literal["contact"]
    full_name: str = Field(min_length=1, max_length=120)
    organization: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    url: HttpUrl | None = None
    address: str | None = Field(default=None, max_length=300)


class LocationQrRequest(BaseQrRequest):
    type: Literal["location"]
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    name: str | None = Field(default=None, max_length=120)


QrGenerationRequest = Annotated[
    UrlQrRequest | TextQrRequest | EmailQrRequest | PhoneQrRequest | WifiQrRequest | ContactQrRequest | LocationQrRequest,
    Field(discriminator="type"),
]


class QrGenerationUpdateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=80)
    destination_url: HttpUrl | None = None
    is_active: bool | None = None
    is_favorite: bool | None = None
    expires_at: datetime | None = None
    max_scans: int | None = Field(default=None, ge=1, le=10_000_000)
    design: QrDesignRequest | None = None
    logo_data_url: str | None = Field(default=None, max_length=3_000_000)
    remove_logo: bool | None = None
    access_mode: Literal["public", "password", "authenticated", "private"] | None = None
    access_password: str | None = Field(default=None, min_length=8, max_length=72)
    allowed_emails: list[EmailStr] | None = Field(default=None, max_length=25)

    @field_validator("label")
    @classmethod
    def clean_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("access_password")
    @classmethod
    def validate_access_password_size(cls, value: str | None) -> str | None:
        if value is not None and len(value.encode("utf-8")) > 72:
            raise ValueError("Access password must not exceed 72 UTF-8 bytes")
        return value

    @field_validator("expires_at")
    @classmethod
    def future_expiry(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if normalized <= datetime.now(timezone.utc):
            raise ValueError("Expiry must be in the future")
        return normalized

    @model_validator(mode="after")
    def contains_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class QrGenerationResponse(BaseModel):
    id: str
    type: str
    label: str | None
    payload_preview: str
    slug: str
    dynamic_url: str | None
    destination_url: str | None
    access_mode: str
    allowed_emails: list[str]
    is_encrypted: bool
    status: str
    is_active: bool
    is_favorite: bool
    expires_at: datetime | None
    max_scans: int | None
    scan_count: int
    design: QrDesignRequest
    has_logo: bool
    downloads: dict[str, str]
    created_at: datetime
    updated_at: datetime
    encoding: Literal["UTF-8"] = "UTF-8"


class QrGenerationListResponse(PaginationFields):
    items: list[QrGenerationResponse]
