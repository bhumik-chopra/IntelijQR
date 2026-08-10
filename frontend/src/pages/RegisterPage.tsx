import React, { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Mail, Lock, Eye, EyeOff, User, ArrowRight, Check, X } from "lucide-react";
import { AuthLayout } from "../components/layout";
import { Button, Input } from "../components/ui";
import { useAuth } from "../features/auth";
import { useLocale } from "../features/i18n";
import { cn } from "../lib/cn";

/* Password strength checker */
interface StrengthRule {
  label: string;
  test: (p: string) => boolean;
}

const strengthRules: StrengthRule[] = [
  { label: "At least 8 characters", test: (p) => p.length >= 8 },
  { label: "Uppercase letter", test: (p) => /[A-Z]/.test(p) },
  { label: "Lowercase letter", test: (p) => /[a-z]/.test(p) },
  { label: "Number", test: (p) => /\d/.test(p) },
  { label: "Special character", test: (p) => /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(p) },
];

function getStrengthScore(password: string): number {
  return strengthRules.filter((r) => r.test(password)).length;
}

const strengthConfig = [
  { label: "", color: "bg-white/10" },
  { label: "Weak", color: "bg-red-500" },
  { label: "Fair", color: "bg-amber-500" },
  { label: "Good", color: "bg-yellow-400" },
  { label: "Strong", color: "bg-emerald-500" },
  { label: "Very Strong", color: "bg-emerald-400" },
];

const PasswordStrength: React.FC<{ password: string }> = ({ password }) => {
  const score = getStrengthScore(password);
  if (!password) return null;

  return (
    <div className="mt-3 space-y-2.5">
      {/* Bars */}
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={cn(
              "h-1 flex-1 rounded-full transition-all duration-300",
              i <= score ? strengthConfig[score].color : "bg-white/8"
            )}
          />
        ))}
      </div>

      {/* Label */}
      {score > 0 && (
        <p className={cn("text-xs font-medium", score >= 4 ? "text-emerald-400" : score >= 3 ? "text-yellow-400" : "text-red-400")}>
          {strengthConfig[score].label}
        </p>
      )}

      {/* Rules */}
      <div className="grid grid-cols-2 gap-1">
        {strengthRules.map((rule) => {
          const passed = rule.test(password);
          return (
            <div key={rule.label} className="flex items-center gap-1.5">
              {passed ? (
                <Check className="w-3 h-3 text-emerald-400 flex-shrink-0" />
              ) : (
                <X className="w-3 h-3 text-slate-700 flex-shrink-0" />
              )}
              <span className={cn("text-[10px]", passed ? "text-slate-400" : "text-slate-700")}>
                {rule.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const RegisterPage: React.FC = () => {
  const { isAuthenticated, isInitializing, register } = useAuth();
  const navigate = useNavigate();
  const { t } = useLocale();

  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<typeof form & { general: string }>>({});

  const validate = () => {
    const e: typeof errors = {};
    if (form.name.trim().length < 2) e.name = "Enter at least 2 characters";
    if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) e.email = "Enter a valid email address";
    if (getStrengthScore(form.password) < 3)
      e.password = "Password is too weak";
    if (new TextEncoder().encode(form.password).length > 72)
      e.password = "Password must be no more than 72 bytes";
    return e;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setErrors({});
    setLoading(true);
    try {
      await register({
        name: form.name.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
      });
      navigate("/login", { replace: true, state: { registrationSuccess: true } });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Registration failed. Please try again.";
      setErrors({ general: msg });
    } finally {
      setLoading(false);
    }
  };

  if (!isInitializing && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <AuthLayout
      title={t("register.title")}
      subtitle={t("register.subtitle")}
    >
      <form id="register-form" onSubmit={handleSubmit} className="space-y-4" noValidate>
        {errors.general && (
          <div
            role="alert"
            className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400"
          >
            <X className="w-4 h-4 flex-shrink-0" />
            {errors.general}
          </div>
        )}

        <Input
          id="register-name"
          label={t("register.name")}
          type="text"
          placeholder="Jane Smith"
          autoComplete="name"
          icon={<User className="w-4 h-4" />}
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          error={errors.name}
          required
        />

        <Input
          id="register-email"
          label={t("register.email")}
          type="email"
          placeholder="you@company.com"
          autoComplete="email"
          icon={<Mail className="w-4 h-4" />}
          value={form.email}
          onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
          error={errors.email}
          required
        />

        <div>
          <Input
            id="register-password"
            label={t("register.password")}
            type={showPassword ? "text" : "password"}
            placeholder={t("register.passwordPlaceholder")}
            autoComplete="new-password"
            icon={<Lock className="w-4 h-4" />}
            iconRight={showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            onIconRightClick={() => setShowPassword((v) => !v)}
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            error={errors.password}
            required
          />
          <PasswordStrength password={form.password} />
        </div>

        <Button
          id="register-submit"
          type="submit"
          fullWidth
          loading={loading}
          iconRight={!loading ? <ArrowRight className="w-4 h-4" /> : undefined}
          className="h-11 mt-1"
        >
          {t("register.submit")}
        </Button>

      </form>

      <p className="text-center text-sm text-slate-600 mt-6">
        {t("register.hasAccount")}{" "}
        <Link
          to="/login"
          id="register-to-login"
          className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
        >
          {t("register.signIn")}
        </Link>
      </p>
    </AuthLayout>
  );
};
