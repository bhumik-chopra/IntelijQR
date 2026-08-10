import { useCallback, useEffect, useState } from "react";

import { qrGeneratorApi } from "../api/qrGeneratorApi";
import type { QrGeneration, QrGenerationFilters } from "../types/qrGenerator";


export function useQrGenerations(filters: QrGenerationFilters = {}) {
  const [items, setItems] = useState<QrGeneration[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { limit = 50, search = "", type, status, favorite } = filters;

  const reload = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await qrGeneratorApi.list({ limit, search, type, status, favorite });
      setItems(result.items);
      setTotal(result.total);
    } catch (caught) {
      const nextError = caught instanceof Error ? caught : new Error("Could not load QR history");
      setError(nextError);
      throw nextError;
    } finally {
      setIsLoading(false);
    }
  }, [favorite, limit, search, status, type]);

  useEffect(() => { void reload().catch(() => undefined); }, [reload]);

  return { items, total, isLoading, error, reload };
}
