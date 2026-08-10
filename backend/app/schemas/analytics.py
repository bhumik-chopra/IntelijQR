from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnalyticsPoint(BaseModel):
    date: str
    scans: int
    unique_visitors: int


class AnalyticsBreakdown(BaseModel):
    label: str
    value: int
    percentage: float = Field(ge=0, le=100)


class TopQrCode(BaseModel):
    id: str
    label: str
    scans: int
    unique_visitors: int


class RecentScanEvent(BaseModel):
    id: str
    generation_id: str
    qr_label: str
    device_type: str
    browser: str
    operating_system: str
    country: str
    city: str
    scanned_at: datetime


class AnalyticsOverviewResponse(BaseModel):
    period: Literal["7d", "30d", "90d", "12m"]
    starts_at: datetime
    ends_at: datetime
    total_scans: int
    unique_visitors: int
    previous_total_scans: int
    scan_change_percentage: float | None
    series: list[AnalyticsPoint]
    devices: list[AnalyticsBreakdown]
    browsers: list[AnalyticsBreakdown]
    operating_systems: list[AnalyticsBreakdown]
    countries: list[AnalyticsBreakdown]
    cities: list[AnalyticsBreakdown]
    top_qr_codes: list[TopQrCode]
    recent_scans: list[RecentScanEvent]
