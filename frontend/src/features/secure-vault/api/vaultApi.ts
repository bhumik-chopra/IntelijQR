import { apiClient } from "../../../lib/api/client";
import type { VaultGrant, VaultPolicy } from "../types/vault";


export const vaultApi = {
  policy(slug: string): Promise<VaultPolicy> {
    return apiClient.get<VaultPolicy>(`/qr/access/${encodeURIComponent(slug)}`, { authenticate: false });
  },
  unlock(slug: string, password?: string): Promise<VaultGrant> {
    return apiClient.post<VaultGrant>(`/qr/access/${encodeURIComponent(slug)}/unlock`, { password: password || null });
  },
};
