from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import PaginationFields
from app.schemas.user import UserResponse


class AdminStats(BaseModel):
    users: int
    active_users: int
    active_admins: int
    qr_codes: int
    dynamic_scans: int
    decoded_scans: int
    shared_files: int
    share_downloads: int
    bulk_jobs: int


class AdminAuditEvent(BaseModel):
    id: str
    admin_user_id: str
    action: str
    target_type: str
    target_id: str
    details: dict
    created_at: datetime


class AdminOverviewResponse(BaseModel):
    stats: AdminStats
    recent_audit: list[AdminAuditEvent]


class AdminUserListResponse(PaginationFields):
    items: list[UserResponse]


class AdminUserUpdateRequest(BaseModel):
    role: Literal["user", "admin"] | None = None
    status: Literal["active", "disabled"] | None = None

    @model_validator(mode="after")
    def contains_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self
