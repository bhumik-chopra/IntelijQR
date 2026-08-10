import {
  apiClient,
  clearAccessToken,
  restoreSession,
  setAccessToken,
} from "../../../lib/api/client";
import type {
  AuthResponse,
  AuthUser,
  LoginInput,
  RegisterInput,
} from "../types/auth";

function rememberAuthentication(result: AuthResponse): AuthResponse {
  setAccessToken(result.access_token);
  return result;
}

export const authApi = {
  async register(input: RegisterInput): Promise<AuthResponse> {
    const result = await apiClient.post<AuthResponse>("/auth/register", input, {
      authenticate: false,
      retryAfterRefresh: false,
    });
    return rememberAuthentication(result);
  },

  async login(input: LoginInput): Promise<AuthResponse> {
    const result = await apiClient.post<AuthResponse>("/auth/login", input, {
      authenticate: false,
      retryAfterRefresh: false,
    });
    return rememberAuthentication(result);
  },

  restoreSession,

  getCurrentUser(): Promise<AuthUser> {
    return apiClient.get<AuthUser>("/users/me");
  },

  updateProfile(name: string): Promise<AuthUser> {
    return apiClient.patch<AuthUser>("/users/me", { name });
  },

  updateLocale(locale: AuthUser["locale"]): Promise<AuthUser> {
    return apiClient.patch<AuthUser>("/users/me/locale", { locale });
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post<{ message: string }>("/users/me/password", { current_password: currentPassword, new_password: newPassword });
    clearAccessToken();
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post<{ message: string }>("/auth/logout", undefined, {
        authenticate: false,
        retryAfterRefresh: false,
      });
    } finally {
      clearAccessToken();
    }
  },
};
