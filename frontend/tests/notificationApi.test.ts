import { afterEach, describe, expect, it, vi } from "vitest";

import { notificationApi } from "../src/features/notifications";
import { clearAccessToken, setAccessToken } from "../src/lib/api/client";


afterEach(() => { clearAccessToken(); vi.restoreAllMocks(); });

describe("notificationApi", () => {
  it("loads unread notifications through the authenticated API", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      items: [], total: 0, limit: 30, offset: 0, has_more: false, unread_count: 2,
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const result = await notificationApi.list(30, 0, true);
    expect(result.unread_count).toBe(2);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("unread_only=true");
    expect(new Headers(fetchMock.mock.calls[0]?.[1]?.headers).get("Authorization")).toBe("Bearer access-token");
  });

  it("updates local delivery preferences", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      in_app_enabled: true, email_enabled: false, local_smtp_available: false,
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const payload = { in_app_enabled: true, email_enabled: false, security_alerts: true, qr_activity: true, share_activity: true, bulk_activity: true };
    await notificationApi.updatePreferences(payload);
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe("PATCH");
    expect(fetchMock.mock.calls[0]?.[1]?.body).toBe(JSON.stringify(payload));
  });
});
