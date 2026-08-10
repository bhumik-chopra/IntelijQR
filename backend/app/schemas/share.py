from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.schemas.common import PaginationFields


class ShareUpdateRequest(BaseModel):
    access_mode: Literal["public", "password", "authenticated", "private"] | None = None
    access_password: str | None = Field(default=None, min_length=8, max_length=72)
    allowed_emails: list[EmailStr] | None = Field(default=None, max_length=25)
    expires_at: datetime | None = None
    max_downloads: int | None = Field(default=None, ge=1, le=1_000_000)
    is_active: bool | None = None

    @field_validator("expires_at")
    @classmethod
    def future_expiry(cls, value):
        if value is not None and (value if value.tzinfo else value.replace(tzinfo=timezone.utc)) <= datetime.now(timezone.utc):
            raise ValueError("Expiry must be in the future")
        return value

    @model_validator(mode="after")
    def contains_change(self):
        if not self.model_fields_set: raise ValueError("At least one field must be provided")
        return self


class ShareFileResponse(BaseModel):
    id: str; slug: str; filename: str; media_type: str; size: int; qr_generation_id: str
    access_mode: str; allowed_emails: list[str]; expires_at: datetime | None; max_downloads: int | None
    download_count: int; is_active: bool; status: str; share_url: str; qr_downloads: dict[str, str]
    created_at: datetime; updated_at: datetime


class ShareFileListResponse(PaginationFields):
    items: list[ShareFileResponse]


class ShareAccessPolicyResponse(BaseModel):
    slug: str; filename: str; media_type: str; size: int; access_mode: str; requires_authentication: bool; status: str


class ShareGrantRequest(BaseModel):
    password: str | None = Field(default=None, max_length=72)


class ShareGrantResponse(BaseModel):
    download_url: str; expires_at: datetime


class ShareDownloadEventResponse(BaseModel):
    id: str; device_type: str; browser: str; operating_system: str; country: str; city: str; downloaded_at: datetime


class ShareDownloadListResponse(PaginationFields):
    items: list[ShareDownloadEventResponse]
