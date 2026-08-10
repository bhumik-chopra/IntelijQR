import { apiClient } from "../../../lib/api/client";
import type { QrScan, QrScanList, QrScanSource } from "../types/qrScanner";


export const qrScannerApi = {
  decode(file: Blob, source: QrScanSource, filename = "qr-scan.png"): Promise<QrScanList> {
    const data = new FormData();
    data.append("file", file, filename);
    data.append("source", source);
    return apiClient.postForm<QrScanList>("/qr/scans/decode", data);
  },

  analyze(content: string, source: QrScanSource = "webcam"): Promise<QrScan> {
    return apiClient.post<QrScan>("/qr/scans/analyze", { content, source });
  },

  history(limit = 50): Promise<QrScanList> {
    return apiClient.get<QrScanList>(`/qr/scans?limit=${limit}`);
  },

  remove(scanId: string): Promise<void> {
    return apiClient.delete<void>(`/qr/scans/${encodeURIComponent(scanId)}`);
  },
};
