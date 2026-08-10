import { afterEach, describe, expect, it, vi } from "vitest";

import { qrGeneratorApi } from "../src/features/qr-generator/api/qrGeneratorApi";
import { clearAccessToken, setAccessToken } from "../src/lib/api/client";
import type { QrGeneration } from "../src/features/qr-generator/types/qrGenerator";


const generation: QrGeneration = {
  id: "generation-id",
  type: "url",
  label: "Website",
  payload_preview: "https://example.com/",
  slug: "abc123",
  dynamic_url: "http://127.0.0.1:8000/r/abc123",
  destination_url: "https://example.com/",
  access_mode: "public",
  allowed_emails: [],
  is_encrypted: false,
  status: "active",
  is_active: true,
  is_favorite: false,
  expires_at: null,
  max_scans: null,
  scan_count: 0,
  design: {
    foreground_color: "#111827",
    background_color: "#FFFFFF",
    gradient_enabled: false,
    gradient_color: "#7C3AED",
    gradient_direction: "diagonal",
    module_style: "square",
    frame_style: "none",
    frame_text: null,
    error_correction: "H",
    size: 1024,
    margin: 4,
  },
  has_logo: false,
  downloads: {
    png: "/api/v1/qr/generations/generation-id/files/png",
    svg: "/api/v1/qr/generations/generation-id/files/svg",
    pdf: "/api/v1/qr/generations/generation-id/files/pdf",
  },
  created_at: "2026-08-07T00:00:00Z",
  updated_at: "2026-08-07T00:00:00Z",
  encoding: "UTF-8",
};


afterEach(() => {
  clearAccessToken();
  vi.restoreAllMocks();
});


describe("qrGeneratorApi", () => {
  it("generates a typed QR payload with authentication", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(generation), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const result = await qrGeneratorApi.generate({
      type: "url",
      label: "Website",
      url: "https://example.com",
    });

    expect(result.id).toBe("generation-id");
    const request = fetchMock.mock.calls[0]?.[1];
    expect(new Headers(request?.headers).get("Authorization")).toBe("Bearer access-token");
    expect(JSON.parse(String(request?.body))).toMatchObject({ type: "url" });
  });

  it("downloads binary QR files", async () => {
    setAccessToken("access-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(new Uint8Array([0x25, 0x50, 0x44, 0x46]), {
        status: 200,
        headers: { "Content-Type": "application/pdf" },
      }),
    );

    const file = await qrGeneratorApi.download("generation-id", "pdf");

    expect(file.size).toBe(4);
    expect(file.type).toBe("application/pdf");
  });

  it("updates dynamic controls and deletes a QR code", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ ...generation, is_active: false, status: "paused" }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));

    const updated = await qrGeneratorApi.update("generation-id", { is_active: false });
    await qrGeneratorApi.remove("generation-id");

    expect(updated.status).toBe("paused");
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe("PATCH");
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toEqual({ is_active: false });
    expect(fetchMock.mock.calls[1]?.[1]?.method).toBe("DELETE");
  });

  it("builds server-side search and filter queries", async () => {
    setAccessToken("access-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [generation], total: 1 }), { status: 200, headers: { "Content-Type": "application/json" } }),
    );

    const result = await qrGeneratorApi.list({ search: "Website", type: "url", status: "active", favorite: true });

    expect(result.total).toBe(1);
    const requestedUrl = String(fetchMock.mock.calls[0]?.[0]);
    expect(requestedUrl).toContain("search=Website");
    expect(requestedUrl).toContain("type=url");
    expect(requestedUrl).toContain("status=active");
    expect(requestedUrl).toContain("favorite=true");
  });
});
