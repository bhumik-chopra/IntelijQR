import { useCallback, useEffect, useState } from "react";
import { shareVaultApi, type CreateShareInput } from "../api/shareVaultApi";
import type { ShareFileRecord, ShareUpdate } from "../types/shareVault";


export function useShares() {
  const [items, setItems] = useState<ShareFileRecord[]>([]); const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false); const [error, setError] = useState<Error | null>(null);
  const load = useCallback(async () => { try { setItems((await shareVaultApi.list()).items); setError(null); } catch (caught) { setError(caught instanceof Error ? caught : new Error("Could not load shared files")); } finally { setIsLoading(false); } }, []);
  useEffect(() => { void load(); }, [load]);
  const create = useCallback(async (input: CreateShareInput) => { setIsCreating(true); setError(null); try { const item = await shareVaultApi.create(input); setItems((current) => [item, ...current]); return item; } catch (caught) { const next = caught instanceof Error ? caught : new Error("File upload failed"); setError(next); throw next; } finally { setIsCreating(false); } }, []);
  const update = useCallback(async (id: string, changes: ShareUpdate) => { const item = await shareVaultApi.update(id, changes); setItems((current) => current.map((entry) => entry.id === id ? item : entry)); }, []);
  const remove = useCallback(async (id: string) => { await shareVaultApi.remove(id); setItems((current) => current.filter((entry) => entry.id !== id)); }, []);
  return { items, isLoading, isCreating, error, create, update, remove, reload: load };
}
