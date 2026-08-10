import { afterEach, describe, expect, it, vi } from "vitest";

import { shareVaultApi } from "../src/features/share-vault/api/shareVaultApi";
import { clearAccessToken, setAccessToken } from "../src/lib/api/client";


afterEach(() => { clearAccessToken(); vi.restoreAllMocks(); });

describe("shareVaultApi", () => {
  it("uploads protected files with multipart access controls", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ id: "share-id", filename: "report.pdf" }), { status: 201, headers: { "Content-Type": "application/json" } }));
    await shareVaultApi.create({ file: new File(["%PDF-test"], "report.pdf", { type: "application/pdf" }), accessMode: "password", password: "safe-password", maxDownloads: 5 });
    const body = fetchMock.mock.calls[0]?.[1]?.body as FormData;
    expect(body.get("access_mode")).toBe("password"); expect(body.get("access_password")).toBe("safe-password"); expect(body.get("max_downloads")).toBe("5");
  });

  it("loads recipient policy without exposing the authenticated token", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ slug: "slug", filename: "report.pdf", access_mode: "private" }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const policy = await shareVaultApi.policy("slug");
    expect(policy.access_mode).toBe("private"); expect(new Headers(fetchMock.mock.calls[0]?.[1]?.headers).has("Authorization")).toBe(false);
  });
});
