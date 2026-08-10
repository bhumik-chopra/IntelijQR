import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../../lib/api/client";
import { notificationApi } from "../api/notificationApi";
import type { NotificationList, NotificationPreferences, NotificationPreferencesUpdate } from "../types/notification";


export function useNotificationUnread() {
  const [unread, setUnread] = useState(0);
  const refresh = useCallback(async () => {
    try { setUnread(await notificationApi.unreadCount()); } catch { setUnread(0); }
  }, []);
  useEffect(() => { void refresh(); const timer = window.setInterval(() => void refresh(), 30_000); return () => window.clearInterval(timer); }, [refresh]);
  return { unread, refresh };
}

export function useNotifications(unreadOnly: boolean) {
  const [data, setData] = useState<NotificationList | null>(null);
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { const [items, prefs] = await Promise.all([notificationApi.list(50, 0, unreadOnly), notificationApi.preferences()]); setData(items); setPreferences(prefs); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Notifications could not be loaded"); }
    finally { setLoading(false); }
  }, [unreadOnly]);
  useEffect(() => { void load(); }, [load]);
  const action = useCallback(async (operation: () => Promise<unknown>) => { setError(null); try { await operation(); await load(); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Notification update failed"); } }, [load]);
  const savePreferences = useCallback(async (payload: NotificationPreferencesUpdate) => { setSaving(true); setError(null);
    try { setPreferences(await notificationApi.updatePreferences(payload)); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Preferences could not be saved"); }
    finally { setSaving(false); } }, []);
  return { data, preferences, loading, saving, error, reload: load, markRead: (id: string) => action(() => notificationApi.markRead(id)),
    markAllRead: () => action(notificationApi.markAllRead), deleteNotification: (id: string) => action(() => notificationApi.delete(id)), savePreferences };
}
