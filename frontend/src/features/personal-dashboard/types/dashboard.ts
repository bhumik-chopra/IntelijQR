export interface DashboardActivity { id: string; type: string; title: string; detail: string; occurred_at: string; }
export interface DownloadHistoryItem { id: string; resource_type: string; resource_id: string; filename: string; file_format: string; downloaded_at: string; }
export interface DashboardSummary { qr_codes: number; favourite_qr_codes: number; total_redirect_scans: number; scanner_history: number;
  shared_files: number; shared_file_downloads: number; bulk_jobs: number; exports: number;
  recent_activity: DashboardActivity[]; download_history: DownloadHistoryItem[]; }
