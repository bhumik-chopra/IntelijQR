import type { AuthUser } from "../../auth/types/auth";
import type { PaginatedResponse } from "../../../lib/api/types";

export interface AdminStats {
  users: number;
  active_users: number;
  active_admins: number;
  qr_codes: number;
  dynamic_scans: number;
  decoded_scans: number;
  shared_files: number;
  share_downloads: number;
  bulk_jobs: number;
}

export interface AdminAuditEvent {
  id: string;
  admin_user_id: string;
  action: string;
  target_type: string;
  target_id: string;
  details: Record<string, string>;
  created_at: string;
}

export interface AdminOverview { stats: AdminStats; recent_audit: AdminAuditEvent[]; }
export type AdminUserList = PaginatedResponse<AuthUser>;
export interface AdminUserFilters { limit?: number; offset?: number; search?: string; role?: AuthUser["role"]; status?: AuthUser["status"]; }
export interface AdminUserUpdate { role?: AuthUser["role"]; status?: AuthUser["status"]; }
