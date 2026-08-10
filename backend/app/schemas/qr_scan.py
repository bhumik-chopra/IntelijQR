from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.qr_scan import QrContentType, QrScanSource
from app.schemas.common import PaginationFields


class QrScanAnalyzeRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    source: QrScanSource = "webcam"

    @field_validator("content")
    @classmethod
    def reject_blank_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Decoded QR content cannot be blank")
        return value.strip()


class QrSecurityAssessment(BaseModel):
    checked: bool
    is_safe: bool
    score: int = Field(ge=0, le=100)
    level: Literal["low", "medium", "high", "critical"]
    normalized_url: str | None
    checks: list[str]
    warnings: list[str]


class QrScanResponse(BaseModel):
    id: str
    content: str
    content_type: QrContentType
    source: QrScanSource
    metadata: dict
    security: QrSecurityAssessment | None
    created_at: datetime


class QrScanListResponse(PaginationFields):
    items: list[QrScanResponse]
