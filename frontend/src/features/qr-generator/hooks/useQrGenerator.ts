import { useCallback, useState } from "react";

import { qrGeneratorApi } from "../api/qrGeneratorApi";
import type {
  QrDownloadFormat,
  QrGeneration,
  QrGenerationInput,
} from "../types/qrGenerator";


export function useQrGenerator() {
  const [generation, setGeneration] = useState<QrGeneration | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const generate = useCallback(async (input: QrGenerationInput) => {
    setIsGenerating(true);
    setError(null);
    try {
      const result = await qrGeneratorApi.generate(input);
      setGeneration(result);
      return result;
    } catch (caught) {
      const nextError = caught instanceof Error ? caught : new Error("QR generation failed");
      setError(nextError);
      throw nextError;
    } finally {
      setIsGenerating(false);
    }
  }, []);

  const download = useCallback(
    async (format: QrDownloadFormat) => {
      if (!generation) throw new Error("Generate a QR code before downloading it");
      await qrGeneratorApi.saveDownload(generation.id, format);
    },
    [generation],
  );

  const reset = useCallback(() => {
    setGeneration(null);
    setError(null);
  }, []);

  return { generation, isGenerating, error, generate, download, reset };
}

