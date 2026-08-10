import { apiClient } from "../../../lib/api/client";
import type { AuthUser } from "../../auth/types/auth";
import type { AdminOverview, AdminUserFilters, AdminUserList, AdminUserUpdate } from "../types/admin";


export const adminApi = {
  overview: () => apiClient.get<AdminOverview>("/admin/overview"),
  users: (filters: AdminUserFilters = {}) => {
    const query = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== "") query.set(key, String(value));
    });
    const suffix = query.size ? `?${query.toString()}` : "";
    return apiClient.get<AdminUserList>(`/admin/users${suffix}`);
  },
  updateUser: (userId: string, payload: AdminUserUpdate) =>
    apiClient.patch<AuthUser>(`/admin/users/${userId}`, payload),
};
