export type ShareAccessMode = "public" | "password" | "authenticated" | "private";
export interface ShareFileRecord { id: string; slug: string; filename: string; media_type: string; size: number; qr_generation_id: string;
  access_mode: ShareAccessMode; allowed_emails: string[]; expires_at: string | null; max_downloads: number | null;
  download_count: number; is_active: boolean; status: string; share_url: string; qr_downloads: Record<"png" | "svg" | "pdf", string>;
  created_at: string; updated_at: string; }
export type ShareList = PaginatedResponse<ShareFileRecord>;
export interface SharePolicy { slug: string; filename: string; media_type: string; size: number; access_mode: ShareAccessMode; requires_authentication: boolean; status: string; }
export interface ShareGrant { download_url: string; expires_at: string; }
export interface ShareDownloadEvent { id: string; device_type: string; browser: string; operating_system: string; country: string; city: string; downloaded_at: string; }
export type ShareDownloadList = PaginatedResponse<ShareDownloadEvent>;
export interface ShareUpdate { access_mode?: ShareAccessMode; access_password?: string; allowed_emails?: string[]; expires_at?: string | null; max_downloads?: number | null; is_active?: boolean; }
import type { PaginatedResponse } from "../../../lib/api/types";
