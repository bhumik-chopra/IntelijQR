import { apiClient } from "../../../lib/api/client";
import type { BulkFormat, BulkJob, BulkJobList } from "../types/bulkForge";


export const bulkForgeApi = {
  create(file: File, formats: BulkFormat[]): Promise<BulkJob> {
    const data = new FormData(); data.append("file", file); data.append("formats", formats.join(","));
    return apiClient.postForm<BulkJob>("/bulk/jobs", data);
  },
  list(): Promise<BulkJobList> { return apiClient.get<BulkJobList>("/bulk/jobs?limit=50"); },
  get(id: string): Promise<BulkJob> { return apiClient.get<BulkJob>(`/bulk/jobs/${encodeURIComponent(id)}`); },
  remove(id: string): Promise<void> { return apiClient.delete<void>(`/bulk/jobs/${encodeURIComponent(id)}`); },
  async download(id: string): Promise<void> {
    const blob = await apiClient.download(`/bulk/jobs/${encodeURIComponent(id)}/download`);
    const url = URL.createObjectURL(blob); const anchor = document.createElement("a");
    anchor.href = url; anchor.download = `intelliqr-bulk-${id}.zip`; anchor.click(); URL.revokeObjectURL(url);
  },
};
