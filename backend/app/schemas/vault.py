from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class VaultPolicyResponse(BaseModel):
    slug: str
    label: str
    access_mode: str
    requires_authentication: bool
    status: str


class VaultUnlockRequest(BaseModel):
    password: str | None = Field(default=None, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password_size(cls, value: str | None) -> str | None:
        if value is not None and len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class VaultGrantResponse(BaseModel):
    redirect_url: str
    expires_at: datetime
