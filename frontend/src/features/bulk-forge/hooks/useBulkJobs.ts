import { useCallback, useEffect, useState } from "react";
import { bulkForgeApi } from "../api/bulkForgeApi";
import type { BulkFormat, BulkJob } from "../types/bulkForge";


export function useBulkJobs() {
  const [jobs, setJobs] = useState<BulkJob[]>([]); const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false); const [error, setError] = useState<Error | null>(null);
  const load = useCallback(async () => { try { setJobs((await bulkForgeApi.list()).items); setError(null); } catch (caught) { setError(caught instanceof Error ? caught : new Error("Could not load bulk jobs")); } finally { setIsLoading(false); } }, []);
  useEffect(() => { void load(); }, [load]);
  const hasActive = jobs.some((job) => job.status === "queued" || job.status === "processing");
  useEffect(() => { if (!hasActive) return; const timer = window.setInterval(() => void load(), 1500); return () => window.clearInterval(timer); }, [hasActive, load]);
  const create = useCallback(async (file: File, formats: BulkFormat[]) => { setIsUploading(true); setError(null); try { const job = await bulkForgeApi.create(file, formats); setJobs((current) => [job, ...current]); return job; } catch (caught) { const next = caught instanceof Error ? caught : new Error("Bulk upload failed"); setError(next); throw next; } finally { setIsUploading(false); } }, []);
  const remove = useCallback(async (id: string) => { await bulkForgeApi.remove(id); setJobs((current) => current.filter((job) => job.id !== id)); }, []);
  return { jobs, isLoading, isUploading, error, create, remove, reload: load };
}
