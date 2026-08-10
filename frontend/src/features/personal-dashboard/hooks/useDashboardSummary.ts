import { useCallback, useEffect, useState } from "react";
import { dashboardApi } from "../api/dashboardApi";
import type { DashboardSummary } from "../types/dashboard";

export function useDashboardSummary() {
  const [data, setData] = useState<DashboardSummary | null>(null); const [isLoading, setIsLoading] = useState(true); const [error, setError] = useState<Error | null>(null);
  const reload = useCallback(async () => { setIsLoading(true); try { setData(await dashboardApi.summary()); setError(null); } catch (caught) { setError(caught instanceof Error ? caught : new Error("Could not load dashboard summary")); } finally { setIsLoading(false); } }, []);
  useEffect(() => { void reload(); }, [reload]); return { data, isLoading, error, reload };
}
