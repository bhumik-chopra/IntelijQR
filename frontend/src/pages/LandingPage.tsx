import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Contact,
  Download,
  FileText,
  History,
  MapPin,
  QrCode,
  Shield,
  Wifi,
} from "lucide-react";

import { Badge, Button, Spinner } from "../components/ui";
import { useAuth } from "../features/auth";
import { LanguageSelector, useLocale } from "../features/i18n";
import { cn } from "../lib/cn";
import { BackendStatus } from "../components/BackendStatus";


const features = [
  {
    icon: QrCode,
    title: "landing.feature.types",
    description: "landing.feature.typesDesc",
  },
  {
    icon: Download,
    title: "landing.feature.formats",
    description: "landing.feature.formatsDesc",
  },
  {
    icon: Shield,
    title: "landing.feature.local",
    description: "landing.feature.localDesc",
  },
  {
    icon: History,
    title: "landing.feature.history",
    description: "landing.feature.historyDesc",
  },
  {
    icon: Wifi,
    title: "landing.feature.unicode",
    description: "landing.feature.unicodeDesc",
  },
  {
    icon: Contact,
    title: "landing.feature.structured",
    description: "landing.feature.structuredDesc",
  },
];


export const LandingPage: React.FC = () => {
  const { isAuthenticated, isInitializing } = useAuth();
  const { t } = useLocale();

  return (
  <div className="min-h-screen overflow-x-hidden bg-[#08080F] text-slate-200">
    <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#08080F]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2.5" id="landing-logo">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-blue-500">
            <QrCode className="h-4 w-4 text-white" />
          </div>
          <span className="font-bold text-white">
            Intelli<span className="text-gradient">QR</span>
          </span>
        </Link>

        <a href="#features" className="hidden text-sm text-slate-500 transition-colors hover:text-slate-200 md:block">
          {t("common.features")}
        </a>

        <div className="flex items-center gap-2 sm:gap-3">
          <BackendStatus compact />
          <LanguageSelector compact />
          {isInitializing ? (
            <Spinner size="sm" />
          ) : isAuthenticated ? (
            <Link to="/dashboard">
              <Button size="sm" iconRight={<ArrowRight className="h-3.5 w-3.5" />}>
                {t("nav.dashboard")}
              </Button>
            </Link>
          ) : (
            <>
              <Link to="/login">
                <Button variant="ghost" size="sm">{t("common.login")}</Button>
              </Link>
              <Link to="/register">
                <Button size="sm">{t("common.register")}</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>

    <main>
      <section className="relative flex min-h-[82vh] items-center overflow-hidden px-6 py-24">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-0 h-[500px] w-[900px] -translate-x-1/2 rounded-full bg-gradient-to-b from-violet-600/15 to-transparent blur-3xl" />
        </div>

        <div className="relative z-10 mx-auto grid w-full max-w-6xl items-center gap-16 lg:grid-cols-2">
          <div>
            <Badge variant="purple" className="mb-6">{t("landing.badge")}</Badge>
            <h1 className="mb-6 text-5xl font-bold leading-[1.08] tracking-tight text-white sm:text-6xl">
              {t("landing.title")}
            </h1>
            <p className="mb-9 max-w-xl text-lg leading-relaxed text-slate-500">
              {t("landing.description")}
            </p>
            <Link to={isAuthenticated ? "/dashboard" : "/register"}>
              <Button
                size="lg"
                iconRight={<ArrowRight className="h-4 w-4" />}
                className="shadow-[0_0_40px_rgba(124,58,237,0.35)]"
              >
                {isAuthenticated ? t("landing.open") : t("landing.start")}
              </Button>
            </Link>
          </div>

          <div className="relative mx-auto flex aspect-square w-full max-w-md items-center justify-center">
            <div className="absolute inset-10 rounded-full bg-gradient-to-br from-violet-600/20 to-blue-500/20 blur-3xl" />
            <div className="relative w-full rounded-3xl border border-white/10 bg-[#141428] p-8 shadow-[0_20px_80px_rgba(0,0,0,0.6)]">
              <div className="mb-8 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-blue-500">
                  <QrCode className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-white">IntelliQR Generator</p>
                  <p className="text-xs text-slate-600">Local files · Protected history</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { icon: FileText, label: "Text and URL" },
                  { icon: Wifi, label: "Wi-Fi" },
                  { icon: Contact, label: "vCard" },
                  { icon: MapPin, label: "Location" },
                ].map(({ icon: Icon, label }) => (
                  <div
                    key={label}
                    className={cn(
                      "flex items-center gap-2 rounded-xl border border-white/6 bg-white/3 p-3",
                      "text-sm text-slate-400",
                    )}
                  >
                    <Icon className="h-4 w-4 text-violet-400" />
                    {label}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="border-y border-white/5 bg-white/[0.01] px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-14 text-center">
            <Badge variant="info" className="mb-4">{t("landing.capabilities")}</Badge>
            <h2 className="text-4xl font-bold tracking-tight text-white">{t("landing.workflows")}</h2>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, description }) => (
              <div key={title} className="rounded-2xl border border-white/6 bg-[#0F0F1F] p-6">
                <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl border border-violet-500/20 bg-violet-500/10">
                  <Icon className="h-5 w-5 text-violet-400" />
                </div>
                <h3 className="mb-2 font-semibold text-white">{t(title)}</h3>
                <p className="text-sm leading-relaxed text-slate-500">{t(description)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>

    <footer className="border-t border-white/6 px-6 py-10">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6">
        <span className="font-bold text-white">IntelliQR</span>
        <p className="text-sm text-slate-700">{t("landing.footer")}</p>
      </div>
    </footer>
  </div>
  );
};
