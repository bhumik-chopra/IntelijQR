import { afterEach, describe, expect, it, vi } from "vitest";

import { adminApi } from "../src/features/admin";
import { clearAccessToken, setAccessToken } from "../src/lib/api/client";


afterEach(() => { clearAccessToken(); vi.restoreAllMocks(); });

describe("adminApi", () => {
  it("loads filtered, paginated users with bearer authentication", async () => {
    setAccessToken("admin-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      items: [], total: 0, limit: 20, offset: 20, has_more: false,
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    await adminApi.users({ limit: 20, offset: 20, role: "user", status: "active", search: "ada" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/admin/users?");
    expect(String(url)).toContain("offset=20");
    expect(String(url)).toContain("search=ada");
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer admin-token");
  });

  it("updates only the selected access field", async () => {
    setAccessToken("admin-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      id: "member-id", role: "user", status: "disabled",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    await adminApi.updateUser("member-id", { status: "disabled" });
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe("PATCH");
    expect(fetchMock.mock.calls[0]?.[1]?.body).toBe(JSON.stringify({ status: "disabled" }));
  });
});
