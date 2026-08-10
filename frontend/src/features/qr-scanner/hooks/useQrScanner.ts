import { useCallback, useEffect, useState } from "react";

import { qrScannerApi } from "../api/qrScannerApi";
import type { QrScan, QrScanSource } from "../types/qrScanner";


export function useQrScanner() {
  const [results, setResults] = useState<QrScan[]>([]);
  const [history, setHistory] = useState<QrScan[]>([]);
  const [total, setTotal] = useState(0);
  const [isScanning, setIsScanning] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadHistory = useCallback(async () => {
    setIsLoadingHistory(true);
    try {
      const response = await qrScannerApi.history();
      setHistory(response.items);
      setTotal(response.total);
    } catch (caught) {
      setError(caught instanceof Error ? caught : new Error("Could not load scan history"));
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const scanImage = useCallback(async (file: Blob, source: QrScanSource, filename?: string) => {
    setIsScanning(true);
    setError(null);
    try {
      const response = await qrScannerApi.decode(file, source, filename);
      setResults(response.items);
      setHistory((current) => [...response.items, ...current]);
      setTotal((current) => current + response.total);
      return response.items;
    } catch (caught) {
      const nextError = caught instanceof Error ? caught : new Error("QR scan failed");
      setError(nextError);
      throw nextError;
    } finally {
      setIsScanning(false);
    }
  }, []);

  const remove = useCallback(async (scanId: string) => {
    await qrScannerApi.remove(scanId);
    setHistory((current) => current.filter((item) => item.id !== scanId));
    setResults((current) => current.filter((item) => item.id !== scanId));
    setTotal((current) => Math.max(0, current - 1));
  }, []);

  const clearError = useCallback(() => setError(null), []);
  return { results, history, total, isScanning, isLoadingHistory, error, scanImage, remove, loadHistory, clearError };
}
