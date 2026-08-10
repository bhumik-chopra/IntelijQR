import type { PaginatedResponse } from "../../../lib/api/types";

export type NotificationSeverity = "info" | "success" | "warning" | "critical";
export interface NotificationItem { id: string; event_type: string; category: string; severity: NotificationSeverity;
  title: string; message: string; action_url: string | null; metadata: Record<string, unknown>; is_read: boolean; created_at: string; }
export interface NotificationList extends PaginatedResponse<NotificationItem> { unread_count: number; }
export interface NotificationPreferences { in_app_enabled: boolean; email_enabled: boolean; security_alerts: boolean;
  qr_activity: boolean; share_activity: boolean; bulk_activity: boolean; local_smtp_available: boolean; }
export type NotificationPreferencesUpdate = Omit<NotificationPreferences, "local_smtp_available">;
