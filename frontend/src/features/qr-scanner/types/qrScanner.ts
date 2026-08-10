export type QrScanSource = "upload" | "webcam";
export type QrContentType =
  | "website" | "email" | "contact" | "phone" | "wifi" | "payment"
  | "event" | "pdf" | "image" | "social_media" | "location" | "text";

export interface QrSecurityAssessment {
  checked: boolean;
  is_safe: boolean;
  score: number;
  level: "low" | "medium" | "high" | "critical";
  normalized_url: string | null;
  checks: string[];
  warnings: string[];
}

export interface QrScan {
  id: string;
  content: string;
  content_type: QrContentType;
  source: QrScanSource;
  metadata: Record<string, unknown>;
  security: QrSecurityAssessment | null;
  created_at: string;
}

export type QrScanList = PaginatedResponse<QrScan>;
import type { PaginatedResponse } from "../../../lib/api/types";
