import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../../lib/api/client";
import { adminApi } from "../api/adminApi";
import type { AdminOverview, AdminUserFilters, AdminUserList, AdminUserUpdate } from "../types/admin";


export function useAdminDashboard(filters: AdminUserFilters) {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [users, setUsers] = useState<AdminUserList | null>(null);
  const [loading, setLoading] = useState(true);
  const [mutatingUserId, setMutatingUserId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextOverview, nextUsers] = await Promise.all([adminApi.overview(), adminApi.users(filters)]);
      setOverview(nextOverview);
      setUsers(nextUsers);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Admin data could not be loaded");
    } finally {
      setLoading(false);
    }
  }, [filters.limit, filters.offset, filters.role, filters.search, filters.status]);

  useEffect(() => { void load(); }, [load]);

  const updateUser = useCallback(async (userId: string, payload: AdminUserUpdate) => {
    setMutatingUserId(userId);
    setError(null);
    try {
      await adminApi.updateUser(userId, payload);
      await load();
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "User access could not be updated");
    } finally {
      setMutatingUserId(null);
    }
  }, [load]);

  return { overview, users, loading, mutatingUserId, error, reload: load, updateUser };
}
