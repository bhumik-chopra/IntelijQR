export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: "user" | "admin";
  status: "active" | "disabled";
  created_at: string;
  last_login_at: string | null;
}

export interface RegisterInput {
  name: string;
  email: string;
  password: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
    request_id?: string | null;
  };
  detail?: string;
}

