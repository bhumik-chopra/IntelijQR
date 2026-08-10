import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import { authApi } from "../api/authApi";
import type {
  AuthUser,
  LoginInput,
  RegisterInput,
} from "../types/auth";
import { useLocale } from "../../i18n/hooks/useLocale";

export interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  register: (input: RegisterInput) => Promise<void>;
  login: (input: LoginInput) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const { locale, setLocale } = useLocale();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    let active = true;
    authApi
      .restoreSession()
      .then((result) => {
        if (active) { setUser(result.user); setLocale(result.user.locale); }
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setIsInitializing(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    await authApi.register({ ...input, locale });
    try {
      await authApi.logout();
    } catch {
      // Registration succeeded; the API client still clears its in-memory token.
    }
    setUser(null);
  }, [locale]);

  const login = useCallback(async (input: LoginInput) => {
    const result = await authApi.login(input);
    setUser(result.user);
    setLocale(result.user.locale);
  }, [setLocale]);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    setUser(await authApi.getCurrentUser());
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isInitializing,
      register,
      login,
      logout,
      refreshUser,
    }),
    [user, isInitializing, register, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
