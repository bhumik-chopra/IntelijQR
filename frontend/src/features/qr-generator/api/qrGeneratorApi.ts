import { apiClient } from "../../../lib/api/client";
import type {
  QrDownloadFormat,
  QrGeneration,
  QrGenerationFilters,
  QrGenerationInput,
  QrGenerationList,
  QrGenerationUpdate,
} from "../types/qrGenerator";


export const qrGeneratorApi = {
  generate(input: QrGenerationInput): Promise<QrGeneration> {
    return apiClient.post<QrGeneration>("/qr/generations", input);
  },

  list(filters: QrGenerationFilters = {}): Promise<QrGenerationList> {
    const query = new URLSearchParams();
    query.set("limit", String(filters.limit ?? 50));
    if (filters.search?.trim()) query.set("search", filters.search.trim());
    if (filters.type) query.set("type", filters.type);
    if (filters.status) query.set("status", filters.status);
    if (filters.favorite !== undefined) query.set("favorite", String(filters.favorite));
    return apiClient.get<QrGenerationList>(`/qr/generations?${query}`);
  },

  get(generationId: string): Promise<QrGeneration> {
    return apiClient.get<QrGeneration>(`/qr/generations/${encodeURIComponent(generationId)}`);
  },

  update(generationId: string, changes: QrGenerationUpdate): Promise<QrGeneration> {
    return apiClient.patch<QrGeneration>(`/qr/generations/${encodeURIComponent(generationId)}`, changes);
  },

  remove(generationId: string): Promise<void> {
    return apiClient.delete<void>(`/qr/generations/${encodeURIComponent(generationId)}`);
  },

  download(generationId: string, format: QrDownloadFormat): Promise<Blob> {
    return apiClient.download(`/qr/generations/${encodeURIComponent(generationId)}/files/${format}`);
  },

  async saveDownload(generationId: string, format: QrDownloadFormat): Promise<void> {
    const blob = await this.download(generationId, format);
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = `intelliqr-${generationId}.${format}`;
    anchor.click();
    URL.revokeObjectURL(objectUrl);
  },
};
