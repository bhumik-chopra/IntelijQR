import React, { useState } from "react";
import { ArrowRight, CheckCircle2, Eye, EyeOff, Lock, Mail } from "lucide-react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { AuthLayout } from "../components/layout";
import { Badge, Button, Input } from "../components/ui";
import { useAuth } from "../features/auth";
import { useLocale } from "../features/i18n";

interface LoginLocationState {
  from?: { pathname?: string };
  registrationSuccess?: boolean;
  passwordChanged?: boolean;
}

export const LoginPage: React.FC = () => {
  const { isAuthenticated, isInitializing, login } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const locationState = location.state as LoginLocationState | null;
  const { t } = useLocale();

  const [form, setForm] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const email = form.email.trim().toLowerCase();
    if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
      setError(t("login.emailError"));
      return;
    }
    if (!form.password) {
      setError(t("login.passwordError"));
      return;
    }

    setLoading(true);
    try {
      await login({ email, password: form.password });
      const destination = locationState?.from?.pathname;
      navigate(destination?.startsWith("/") ? destination : "/dashboard", {
        replace: true,
      });
    } catch (requestError: unknown) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Invalid email or password. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  if (!isInitializing && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <AuthLayout title={t("login.title")} subtitle={t("login.subtitle")}>
      <form id="login-form" onSubmit={handleSubmit} className="space-y-5" noValidate>
        {locationState?.registrationSuccess && (
          <Badge variant="success" className="flex w-full justify-center gap-2 py-2.5">
            <CheckCircle2 className="h-4 w-4" /> {t("login.registered")}
          </Badge>
        )}
        {locationState?.passwordChanged && (
          <Badge variant="success" className="flex w-full justify-center gap-2 py-2.5">
            <CheckCircle2 className="h-4 w-4" /> {t("login.changed")}
          </Badge>
        )}

        <Input
          id="login-email"
          label={t("login.email")}
          type="email"
          placeholder="you@company.com"
          autoComplete="email"
          icon={<Mail className="h-4 w-4" />}
          value={form.email}
          onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
          required
        />

        <Input
          id="login-password"
          label={t("login.password")}
          type={showPassword ? "text" : "password"}
          placeholder={t("login.passwordPlaceholder")}
          autoComplete="current-password"
          icon={<Lock className="h-4 w-4" />}
          iconRight={showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          onIconRightClick={() => setShowPassword((visible) => !visible)}
          value={form.password}
          onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
          error={error ?? undefined}
          required
        />

        <Button
          id="login-submit"
          type="submit"
          fullWidth
          loading={loading}
          iconRight={!loading ? <ArrowRight className="h-4 w-4" /> : undefined}
          className="mt-2 h-11"
        >
          {t("login.submit")}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        {t("login.noAccount")}{" "}
        <Link
          to="/register"
          id="login-to-register"
          className="font-medium text-violet-400 transition-colors hover:text-violet-300"
        >
          {t("login.create")}
        </Link>
      </p>
    </AuthLayout>
  );
};
