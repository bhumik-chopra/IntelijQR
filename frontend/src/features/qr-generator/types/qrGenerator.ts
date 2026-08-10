export type QrPayloadType = "url" | "text" | "email" | "phone" | "wifi" | "contact" | "location";
export type QrStatus = "active" | "paused" | "expired" | "scan_limit_reached";
export type QrAccessMode = "public" | "password" | "authenticated" | "private";

export interface QrDesign {
  foreground_color: string;
  background_color: string;
  gradient_enabled: boolean;
  gradient_color: string;
  gradient_direction: "horizontal" | "vertical" | "diagonal";
  module_style: "square" | "rounded" | "dots";
  frame_style: "none" | "square" | "rounded";
  frame_text?: string | null;
  error_correction: "L" | "M" | "Q" | "H";
  size: number;
  margin: number;
}

interface BaseQrInput {
  label?: string;
  expires_at?: string;
  max_scans?: number;
  design?: QrDesign;
  logo_data_url?: string;
  access_mode?: QrAccessMode;
  access_password?: string;
  allowed_emails?: string[];
}

export interface UrlQrInput extends BaseQrInput { type: "url"; url: string; }
export interface TextQrInput extends BaseQrInput { type: "text"; text: string; }
export interface EmailQrInput extends BaseQrInput { type: "email"; email: string; subject?: string; body?: string; }
export interface PhoneQrInput extends BaseQrInput { type: "phone"; phone: string; }
export interface WifiQrInput extends BaseQrInput { type: "wifi"; ssid: string; password?: string; security?: "WPA" | "WEP" | "nopass"; hidden?: boolean; }
export interface ContactQrInput extends BaseQrInput { type: "contact"; full_name: string; organization?: string; title?: string; phone?: string; email?: string; url?: string; address?: string; }
export interface LocationQrInput extends BaseQrInput { type: "location"; latitude: number; longitude: number; name?: string; }

export type QrGenerationInput = UrlQrInput | TextQrInput | EmailQrInput | PhoneQrInput | WifiQrInput | ContactQrInput | LocationQrInput;
export type QrDownloadFormat = "png" | "svg" | "pdf";

export interface QrGeneration {
  id: string;
  type: QrPayloadType;
  label: string | null;
  payload_preview: string;
  slug: string;
  dynamic_url: string | null;
  destination_url: string | null;
  access_mode: QrAccessMode;
  allowed_emails: string[];
  is_encrypted: boolean;
  status: QrStatus;
  is_active: boolean;
  is_favorite: boolean;
  expires_at: string | null;
  max_scans: number | null;
  scan_count: number;
  design: QrDesign;
  has_logo: boolean;
  downloads: Record<QrDownloadFormat, string>;
  created_at: string;
  updated_at: string;
  encoding: "UTF-8";
}

export interface QrGenerationUpdate {
  label?: string | null;
  destination_url?: string;
  is_active?: boolean;
  is_favorite?: boolean;
  expires_at?: string | null;
  max_scans?: number | null;
  design?: QrDesign;
  logo_data_url?: string;
  remove_logo?: boolean;
  access_mode?: QrAccessMode;
  access_password?: string;
  allowed_emails?: string[];
}

export interface QrGenerationFilters {
  limit?: number;
  offset?: number;
  search?: string;
  type?: QrPayloadType;
  status?: QrStatus;
  favorite?: boolean;
}

export type QrGenerationList = PaginatedResponse<QrGeneration>;
import type { PaginatedResponse } from "../../../lib/api/types";
