import type {
  ApiErrorPayload,
  AuthResponse,
} from "../../features/auth/types/auth";

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;
// In local development, Vite proxies this relative path to FastAPI. Keeping the
// browser request same-origin ensures the HttpOnly refresh cookie works whether
// the site was opened with localhost or 127.0.0.1.
const API_BASE_URL = (configuredBaseUrl ?? "/api/v1").replace(
  /\/$/,
  "",
);

let accessToken: string | null = null;
let refreshPromise: Promise<AuthResponse> | null = null;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
    public readonly details?: unknown,
    public readonly requestId?: string | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  authenticate?: boolean;
  retryAfterRefresh?: boolean;
  responseType?: "json" | "blob";
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function clearAccessToken(): void {
  accessToken = null;
}

async function parseResponse<T>(response: Response, responseType: "json" | "blob" = "json"): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    const data = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new ApiError(
      data.error?.message ?? data.detail ?? "Request failed",
      response.status,
      data.error?.code ?? "request_failed",
      data.error?.details,
      data.error?.request_id,
    );
  }
  if (responseType === "blob") {
    return (await response.blob()) as T;
  }
  return (await response.json()) as T;
}

async function rawRequest<T>(
  path: string,
  init: RequestInit,
  responseType: "json" | "blob" = "json",
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
    });
  } catch (error) {
    const originalMessage = error instanceof Error ? error.message : "";
    const message = /failed to fetch|networkerror|load failed/i.test(originalMessage)
      ? "Cannot reach the IntelliQR backend. Make sure the backend server is running."
      : originalMessage || "Network request failed";
    throw new ApiError(
      message,
      0,
      "network_error",
    );
  }
  return parseResponse<T>(response, responseType);
}

export async function restoreSession(): Promise<AuthResponse> {
  if (!refreshPromise) {
    refreshPromise = rawRequest<AuthResponse>("/auth/refresh", { method: "POST" })
      .then((result) => {
        setAccessToken(result.access_token);
        return result;
      })
      .catch((error: unknown) => {
        clearAccessToken();
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
): Promise<T> {
  const authenticate = options.authenticate ?? true;
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (authenticate && accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  try {
    return await rawRequest<T>(path, { ...init, headers }, options.responseType);
  } catch (error) {
    const shouldRefresh =
      error instanceof ApiError &&
      error.status === 401 &&
      authenticate &&
      (options.retryAfterRefresh ?? true);
    if (!shouldRefresh) {
      throw error;
    }

    await restoreSession();
    const retryHeaders = new Headers(headers);
    if (accessToken) {
      retryHeaders.set("Authorization", `Bearer ${accessToken}`);
    }
    return rawRequest<T>(path, { ...init, headers: retryHeaders }, options.responseType);
  }
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { method: "GET" }, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(
      path,
      {
        method: "POST",
        body: body === undefined ? undefined : JSON.stringify(body),
      },
      options,
    ),
  postForm: <T>(path: string, body: FormData, options?: RequestOptions) =>
    request<T>(path, { method: "POST", body }, options),
  patch: <T>(path: string, body: unknown, options?: RequestOptions) =>
    request<T>(
      path,
      { method: "PATCH", body: JSON.stringify(body) },
      options,
    ),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { method: "DELETE" }, options),
  download: (path: string) =>
    request<Blob>(path, { method: "GET" }, { responseType: "blob" }),
};
