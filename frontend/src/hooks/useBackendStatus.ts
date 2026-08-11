import { useCallback, useEffect, useRef, useState } from "react";

export type BackendStatus = "checking" | "online" | "offline";

interface BackendStatusState {
  status: BackendStatus;
  lastChecked: Date | null;
  checkNow: () => Promise<void>;
}

export function useBackendStatus(): BackendStatusState {
  const [status, setStatus] = useState<BackendStatus>("checking");
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const mounted = useRef(true);

  const probe = useCallback(async (showChecking = false) => {
    if (showChecking && mounted.current) setStatus("checking");
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 4000);
    try {
      const response = await fetch("/api/v1/health", {
        cache: "no-store",
        credentials: "include",
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("Backend health check failed");
      const result = (await response.json()) as { status?: string };
      if (mounted.current) setStatus(result.status === "ok" ? "online" : "offline");
    } catch {
      if (mounted.current) setStatus("offline");
    } finally {
      window.clearTimeout(timeout);
      if (mounted.current) setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void probe();
    const interval = window.setInterval(() => void probe(), 12_000);
    const handleOnline = () => void probe(true);
    const handleOffline = () => {
      setStatus("offline");
      setLastChecked(new Date());
    };
    const handleVisibility = () => {
      if (document.visibilityState === "visible") void probe();
    };
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    document.addEventListener("visibilitychange", handleVisibility);
    return () => {
      mounted.current = false;
      window.clearInterval(interval);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [probe]);

  const checkNow = useCallback(() => probe(true), [probe]);
  return { status, lastChecked, checkNow };
}
