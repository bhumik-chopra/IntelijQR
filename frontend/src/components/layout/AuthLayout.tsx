import React from "react";
import { Link } from "react-router-dom";
import { QrCode } from "lucide-react";
import { cn } from "../../lib/cn";
import { LanguageSelector, useLocale } from "../../features/i18n";

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  className?: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title,
  subtitle,
  className,
}) => {
  const { t } = useLocale();
  return (
    <div className="min-h-screen flex bg-[#08080F] overflow-hidden">
      {/* Left Panel – Branding */}
      <div className="hidden lg:flex flex-col w-[480px] xl:w-[560px] flex-shrink-0 relative overflow-hidden bg-[#0A0A14] border-r border-white/6">
        {/* Radial gradient background */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-32 -left-32 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-violet-600/20 to-transparent blur-3xl" />
          <div className="absolute -bottom-32 -right-32 w-[500px] h-[500px] rounded-full bg-gradient-to-tl from-blue-500/15 to-transparent blur-3xl" />
        </div>

        {/* Logo */}
        <div className="relative z-10 p-10">
          <Link to="/" className="flex items-center gap-3 group w-fit" id="auth-logo-link">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-violet-600 to-blue-500 flex items-center justify-center shadow-lg shadow-violet-900/40 group-hover:shadow-violet-700/50 transition-shadow">
              <QrCode className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">
              Intelli<span className="text-gradient">QR</span>
            </span>
          </Link>
        </div>

        {/* Hero content */}
        <div className="relative z-10 flex-1 flex flex-col justify-center px-10 pb-10">
          {/* Animated QR illustration */}
          <div className="mb-10 relative">
            <div className="w-32 h-32 mx-auto relative">
              {/* Outer ring */}
              <div
                className="absolute inset-0 rounded-full border border-violet-500/20"
                style={{ animation: "spin-slow 20s linear infinite" }}
              />
              {/* Middle ring */}
              <div
                className="absolute inset-4 rounded-full border border-blue-500/25"
                style={{ animation: "spin-slow 15s linear infinite reverse" }}
              />
              {/* Core */}
              <div className="absolute inset-8 rounded-2xl bg-gradient-to-br from-violet-600 to-blue-500 flex items-center justify-center shadow-[0_0_30px_rgba(124,58,237,0.5)]">
                <QrCode className="w-6 h-6 text-white" />
              </div>
              {/* Orbiting dots */}
              <div
                className="absolute top-1/2 left-1/2 w-3 h-3 -mt-1.5 -ml-1.5 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(167,139,250,0.8)]"
                style={{ animation: "orbit 8s linear infinite" }}
              />
              <div
                className="absolute top-1/2 left-1/2 w-2 h-2 -mt-1 -ml-1 rounded-full bg-blue-400 shadow-[0_0_6px_rgba(96,165,250,0.8)]"
                style={{ animation: "counter-orbit 12s linear infinite" }}
              />
            </div>
          </div>

          <h2 className="text-3xl font-bold text-white mb-4 leading-tight">
            {t("auth.hero.title")}
            <br />
            <span className="text-gradient">{t("auth.hero.accent")}</span>
          </h2>
          <p className="text-slate-500 text-base leading-relaxed">
            {t("auth.hero.description")}
          </p>
        </div>
      </div>

      {/* Right Panel – Form */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 sm:p-10 relative">
        <div className="absolute right-5 top-5 z-20"><LanguageSelector compact /></div>
        {/* Background pattern */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 right-0 w-[400px] h-[400px] rounded-full bg-gradient-to-bl from-violet-600/8 to-transparent blur-3xl" />
          <div className="absolute bottom-0 left-0 w-[300px] h-[300px] rounded-full bg-gradient-to-tr from-blue-500/8 to-transparent blur-3xl" />
        </div>

        {/* Mobile logo */}
        <div className="lg:hidden mb-8 flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-blue-500 flex items-center justify-center">
            <QrCode className="w-4.5 h-4.5 text-white" />
          </div>
          <span className="text-lg font-bold text-white">
            Intelli<span className="text-gradient">QR</span>
          </span>
        </div>

        {/* Form card */}
        <div
          className={cn(
            "relative z-10 w-full max-w-[420px]",
            "bg-white/3 border border-white/8 rounded-3xl p-8",
            "shadow-[0_8px_60px_rgba(0,0,0,0.5)]",
            "animate-fade-in-scale",
            className
          )}
        >
          <div className="mb-7">
            <h1 className="text-2xl font-bold text-white">{title}</h1>
            {subtitle && (
              <p className="text-slate-500 text-sm mt-1.5">{subtitle}</p>
            )}
          </div>
          {children}
        </div>
      </div>
    </div>
  );
};
