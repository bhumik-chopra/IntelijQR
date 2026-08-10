import { afterEach, describe, expect, it, vi } from "vitest";
import { dashboardApi } from "../src/features/personal-dashboard/api/dashboardApi";
import { clearAccessToken, setAccessToken } from "../src/lib/api/client";

afterEach(() => { clearAccessToken(); vi.restoreAllMocks(); });

describe("dashboardApi", () => {
  it("loads the authenticated cross-feature personal summary", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      qr_codes: 3, favourite_qr_codes: 1, total_redirect_scans: 10, scanner_history: 2, shared_files: 1,
      shared_file_downloads: 4, bulk_jobs: 1, exports: 5, recent_activity: [], download_history: [],
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const summary = await dashboardApi.summary();
    expect(summary.total_redirect_scans).toBe(10);
    expect(new Headers(fetchMock.mock.calls[0]?.[1]?.headers).get("Authorization")).toBe("Bearer access-token");
  });
});
