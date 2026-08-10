import { afterEach, describe, expect, it, vi } from "vitest";

import { bulkForgeApi } from "../src/features/bulk-forge/api/bulkForgeApi";
import { clearAccessToken, setAccessToken } from "../src/lib/api/client";
import type { BulkJob } from "../src/features/bulk-forge/types/bulkForge";


const job: BulkJob = { id: "job-id", filename: "batch.csv", status: "queued", total_rows: 2, processed_rows: 0,
  succeeded_rows: 0, failed_rows: 0, progress_percentage: 0, formats: ["png", "svg"], errors: [], download_url: null,
  created_at: "2026-08-07T00:00:00Z", updated_at: "2026-08-07T00:00:00Z", completed_at: null };

afterEach(() => { clearAccessToken(); vi.restoreAllMocks(); });

describe("bulkForgeApi", () => {
  it("uploads a spreadsheet and selected formats as multipart data", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(job), { status: 202, headers: { "Content-Type": "application/json" } }));
    const result = await bulkForgeApi.create(new File(["type,url\nurl,https://example.com"], "batch.csv", { type: "text/csv" }), ["png", "svg"]);
    const body = fetchMock.mock.calls[0]?.[1]?.body as FormData;
    expect(result.id).toBe("job-id"); expect(body.get("formats")).toBe("png,svg"); expect(body.get("file")).toBeInstanceOf(File);
  });

  it("loads user-owned batch history", async () => {
    setAccessToken("access-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ items: [job], total: 1 }), { status: 200, headers: { "Content-Type": "application/json" } }));
    expect((await bulkForgeApi.list()).total).toBe(1);
  });
});
