export type BulkJobStatus = "queued" | "processing" | "completed" | "partial" | "failed";
export type BulkFormat = "png" | "svg" | "pdf";

export interface BulkRowError { row: number; message: string; }
export interface BulkJob {
  id: string; filename: string; status: BulkJobStatus; total_rows: number; processed_rows: number;
  succeeded_rows: number; failed_rows: number; progress_percentage: number; formats: BulkFormat[];
  errors: BulkRowError[]; download_url: string | null; created_at: string; updated_at: string; completed_at: string | null;
}
export type BulkJobList = PaginatedResponse<BulkJob>;
import type { PaginatedResponse } from "../../../lib/api/types";
