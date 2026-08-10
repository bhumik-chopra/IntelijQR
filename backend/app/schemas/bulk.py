from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import PaginationFields


class BulkRowError(BaseModel):
    row: int
    message: str


class BulkJobResponse(BaseModel):
    id: str
    filename: str
    status: str
    total_rows: int
    processed_rows: int
    succeeded_rows: int
    failed_rows: int
    progress_percentage: float
    formats: list[str]
    errors: list[BulkRowError]
    download_url: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class BulkJobListResponse(PaginationFields):
    items: list[BulkJobResponse]
