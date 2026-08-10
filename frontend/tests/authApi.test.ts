import { afterEach, describe, expect, it, vi } from "vitest";

import { authApi } from "../src/features/auth/api/authApi";
import { clearAccessToken } from "../src/lib/api/client";
import type { AuthResponse } from "../src/features/auth/types/auth";


const authResponse: AuthResponse = {
  access_token: "access-token",
  token_type: "bearer",
  expires_in: 900,
  user: {
    id: "user-id",
    name: "IntelliQR User",
    email: "user@example.com",
    role: "user",
    status: "active",
    created_at: "2026-08-07T00:00:00Z",
  last_login_at: null,
  locale: "en",
  },
};


afterEach(() => {
  vi.restoreAllMocks();
  clearAccessToken();
});


describe("authApi", () => {
  it("logs in with cookies enabled and keeps the access token in memory", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(authResponse), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(authResponse.user), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

    await authApi.login({ email: "user@example.com", password: "password123" });
    await authApi.getCurrentUser();

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/auth/login");
    expect(fetchMock.mock.calls[0]?.[1]?.credentials).toBe("include");
    const profileHeaders = new Headers(fetchMock.mock.calls[1]?.[1]?.headers);
    expect(profileHeaders.get("Authorization")).toBe("Bearer access-token");
  });

  it("clears local authentication state even when logout fails", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(authResponse), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockRejectedValueOnce(new Error("offline"));

    await authApi.login({ email: "user@example.com", password: "password123" });
    await expect(authApi.logout()).rejects.toThrow("offline");
  });

  it("shows an actionable message when the backend cannot be reached", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new TypeError("Failed to fetch"));

    await expect(
      authApi.login({ email: "user@example.com", password: "password123" }),
    ).rejects.toThrow(
      "Cannot reach the IntelliQR backend. Make sure the backend server is running.",
    );
  });

  it("updates profile fields and submits a password rotation", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify(authResponse), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ ...authResponse.user, name: "Updated User" }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ message: "Password changed" }), { status: 200, headers: { "Content-Type": "application/json" } }));
    await authApi.login({ email: "user@example.com", password: "password123" });
    expect((await authApi.updateProfile("Updated User")).name).toBe("Updated User");
    await authApi.changePassword("password123", "new-password123");
    expect(JSON.parse(String(fetchMock.mock.calls[1]?.[1]?.body))).toEqual({ name: "Updated User" });
    expect(JSON.parse(String(fetchMock.mock.calls[2]?.[1]?.body))).toEqual({ current_password: "password123", new_password: "new-password123" });
  });

  it("persists the selected account locale", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify(authResponse), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ ...authResponse.user, locale: "gu" }), { status: 200, headers: { "Content-Type": "application/json" } }));
    await authApi.login({ email: "user@example.com", password: "password123" });
    expect((await authApi.updateLocale("gu")).locale).toBe("gu");
    expect(JSON.parse(String(fetchMock.mock.calls[1]?.[1]?.body))).toEqual({ locale: "gu" });
  });
});
