import { useCallback, useEffect, useState } from "react";

import { analyticsApi } from "../api/analyticsApi";
import type { AnalyticsOverview, AnalyticsPeriod } from "../types/analytics";


export function useAnalytics(period: AnalyticsPeriod, qrId?: string) {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const reload = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setData(await analyticsApi.overview(period, qrId));
    } catch (caught) {
      setError(caught instanceof Error ? caught : new Error("Could not load analytics"));
    } finally {
      setIsLoading(false);
    }
  }, [period, qrId]);

  useEffect(() => { void reload(); }, [reload]);
  return { data, isLoading, error, reload };
}
