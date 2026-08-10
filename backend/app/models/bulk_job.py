from dataclasses import dataclass
from datetime import datetime
from typing import Literal


BulkJobStatus = Literal["queued", "processing", "completed", "partial", "failed"]


@dataclass(frozen=True, slots=True)
class BulkJob:
    id: str
    user_id: str
    filename: str
    status: BulkJobStatus
    total_rows: int
    processed_rows: int
    succeeded_rows: int
    failed_rows: int
    formats: list[str]
    errors: list[dict]
    zip_path: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
