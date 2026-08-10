import { afterEach, describe, expect, it, vi } from "vitest";

import { analyticsApi } from "../src/features/analytics/api/analyticsApi";
import { clearAccessToken, setAccessToken } from "../src/lib/api/client";
import type { AnalyticsOverview } from "../src/features/analytics/types/analytics";


const overview: AnalyticsOverview = {
  period: "30d", starts_at: "2026-07-08T00:00:00Z", ends_at: "2026-08-07T00:00:00Z",
  total_scans: 4, unique_visitors: 3, previous_total_scans: 2, scan_change_percentage: 100,
  series: [{ date: "2026-08-07", scans: 4, unique_visitors: 3 }],
  devices: [{ label: "mobile", value: 3, percentage: 75 }], browsers: [], operating_systems: [],
  countries: [], cities: [], top_qr_codes: [], recent_scans: [],
};


afterEach(() => { clearAccessToken(); vi.restoreAllMocks(); });


describe("analyticsApi", () => {
  it("requests authenticated analytics with period and QR filters", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(overview), { status: 200, headers: { "Content-Type": "application/json" } }),
    );

    const result = await analyticsApi.overview("30d", "qr-id");

    expect(result.total_scans).toBe(4);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("period=30d&qr_id=qr-id");
    expect(new Headers(fetchMock.mock.calls[0]?.[1]?.headers).get("Authorization")).toBe("Bearer access-token");
  });
});
