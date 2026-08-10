import { afterEach, describe, expect, it, vi } from "vitest";

import { qrScannerApi } from "../src/features/qr-scanner/api/qrScannerApi";
import { clearAccessToken, setAccessToken } from "../src/lib/api/client";
import type { QrScan } from "../src/features/qr-scanner/types/qrScanner";


const scan: QrScan = {
  id: "scan-id",
  content: "https://example.com",
  content_type: "website",
  source: "upload",
  metadata: { host: "example.com", scheme: "https" },
  security: {
    checked: true,
    is_safe: true,
    score: 0,
    level: "low",
    normalized_url: "https://example.com",
    checks: ["Uses HTTPS encryption"],
    warnings: [],
  },
  created_at: "2026-08-07T00:00:00Z",
};


afterEach(() => {
  clearAccessToken();
  vi.restoreAllMocks();
});


describe("qrScannerApi", () => {
  it("uploads a QR image as authenticated multipart data", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [scan], total: 1 }), { status: 201, headers: { "Content-Type": "application/json" } }),
    );

    const result = await qrScannerApi.decode(new Blob(["image"], { type: "image/png" }), "upload", "code.png");

    expect(result.items[0]?.content_type).toBe("website");
    const request = fetchMock.mock.calls[0]?.[1];
    expect(request?.body).toBeInstanceOf(FormData);
    expect(new Headers(request?.headers).get("Authorization")).toBe("Bearer access-token");
    expect(new Headers(request?.headers).has("Content-Type")).toBe(false);
  });

  it("loads and deletes scan history", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [scan], total: 1 }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));

    const history = await qrScannerApi.history(25);
    await qrScannerApi.remove("scan-id");

    expect(history.total).toBe(1);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("limit=25");
    expect(fetchMock.mock.calls[1]?.[1]?.method).toBe("DELETE");
  });
});
