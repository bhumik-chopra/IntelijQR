import { apiClient } from "../../../lib/api/client";
import type { ShareAccessMode, ShareDownloadList, ShareFileRecord, ShareGrant, ShareList, SharePolicy, ShareUpdate } from "../types/shareVault";


export interface CreateShareInput { file: File; accessMode: ShareAccessMode; password?: string; allowedEmails?: string; expiresAt?: string; maxDownloads?: number; }
export const shareVaultApi = {
  create(input: CreateShareInput): Promise<ShareFileRecord> {
    const data = new FormData(); data.append("file", input.file); data.append("access_mode", input.accessMode);
    if (input.password) data.append("access_password", input.password); if (input.allowedEmails) data.append("allowed_emails", input.allowedEmails);
    if (input.expiresAt) data.append("expires_at", new Date(input.expiresAt).toISOString()); if (input.maxDownloads) data.append("max_downloads", String(input.maxDownloads));
    return apiClient.postForm<ShareFileRecord>("/shares", data);
  },
  list(): Promise<ShareList> { return apiClient.get<ShareList>("/shares?limit=50"); },
  update(id: string, changes: ShareUpdate): Promise<ShareFileRecord> { return apiClient.patch<ShareFileRecord>(`/shares/${encodeURIComponent(id)}`, changes); },
  remove(id: string): Promise<void> { return apiClient.delete<void>(`/shares/${encodeURIComponent(id)}`); },
  downloads(id: string): Promise<ShareDownloadList> { return apiClient.get<ShareDownloadList>(`/shares/${encodeURIComponent(id)}/downloads?limit=50`); },
  policy(slug: string): Promise<SharePolicy> { return apiClient.get<SharePolicy>(`/shares/access/${encodeURIComponent(slug)}/policy`, { authenticate: false }); },
  grant(slug: string, password?: string): Promise<ShareGrant> { return apiClient.post<ShareGrant>(`/shares/access/${encodeURIComponent(slug)}/grant`, { password: password || null }); },
  async downloadGranted(path: string, filename: string): Promise<void> {
    const blob = await apiClient.download(path); const url = URL.createObjectURL(blob); const anchor = document.createElement("a");
    anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url);
  },
};
