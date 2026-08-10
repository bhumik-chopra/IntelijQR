from datetime import datetime
from pydantic import BaseModel


class DashboardActivity(BaseModel):
    id: str; type: str; title: str; detail: str; occurred_at: datetime


class DownloadHistoryItem(BaseModel):
    id: str; resource_type: str; resource_id: str; filename: str; file_format: str; downloaded_at: datetime


class DashboardSummaryResponse(BaseModel):
    qr_codes: int; favourite_qr_codes: int; total_redirect_scans: int; scanner_history: int
    shared_files: int; shared_file_downloads: int; bulk_jobs: int; exports: int
    recent_activity: list[DashboardActivity]; download_history: list[DownloadHistoryItem]
