import { afterEach, describe, expect, it, vi } from "vitest";

import { vaultApi } from "../src/features/secure-vault/api/vaultApi";
import { clearAccessToken, setAccessToken } from "../src/lib/api/client";


afterEach(() => { clearAccessToken(); vi.restoreAllMocks(); });


describe("vaultApi", () => {
  it("loads a public access policy without sending a bearer token", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      slug: "secure-slug", label: "Private campaign", access_mode: "password", requires_authentication: false, status: "active",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const policy = await vaultApi.policy("secure-slug");

    expect(policy.access_mode).toBe("password");
    expect(new Headers(fetchMock.mock.calls[0]?.[1]?.headers).has("Authorization")).toBe(false);
  });

  it("submits an authenticated unlock request and receives a short-lived redirect", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      redirect_url: "http://127.0.0.1:8000/r/secure-slug?grant=token", expires_at: "2026-08-07T00:05:00Z",
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const grant = await vaultApi.unlock("secure-slug", "correct-password");

    expect(grant.redirect_url).toContain("grant=token");
    expect(new Headers(fetchMock.mock.calls[0]?.[1]?.headers).get("Authorization")).toBe("Bearer access-token");
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toEqual({ password: "correct-password" });
  });
});
