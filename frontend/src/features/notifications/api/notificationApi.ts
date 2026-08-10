import { apiClient } from "../../../lib/api/client";
import type { NotificationList, NotificationPreferences, NotificationPreferencesUpdate } from "../types/notification";


export const notificationApi = {
  list: (limit = 30, offset = 0, unreadOnly = false) => apiClient.get<NotificationList>(
    `/notifications?limit=${limit}&offset=${offset}&unread_only=${unreadOnly}`),
  unreadCount: async () => (await apiClient.get<{ unread_count: number }>("/notifications/unread-count")).unread_count,
  markRead: (id: string) => apiClient.post<{ message: string }>(`/notifications/${id}/read`),
  markAllRead: () => apiClient.post<{ message: string }>("/notifications/read-all"),
  delete: (id: string) => apiClient.delete<void>(`/notifications/${id}`),
  preferences: () => apiClient.get<NotificationPreferences>("/notifications/preferences"),
  updatePreferences: (payload: NotificationPreferencesUpdate) =>
    apiClient.patch<NotificationPreferences>("/notifications/preferences", payload),
};
