import React from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { useLocale } from "../../features/i18n";

interface DashboardLayoutProps {
  title?: string;
  breadcrumbs?: { label: string; href?: string }[];
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  title,
  breadcrumbs,
}) => {
  const location = useLocation();
  const { t } = useLocale();
  const pageLabel = location.pathname === "/generator"
    ? t("nav.generator")
    : location.pathname === "/scanner"
      ? t("nav.scanner")
      : location.pathname === "/analytics"
        ? t("nav.analytics")
        : location.pathname === "/bulk"
          ? t("nav.bulk")
          : location.pathname === "/share-vault"
            ? t("nav.share")
            : location.pathname === "/profile"
              ? t("nav.profile")
              : location.pathname === "/admin"
                ? t("nav.admin")
                : location.pathname === "/notifications"
                  ? t("nav.notifications")
      : t("nav.dashboard");
  const resolvedBreadcrumbs =
    breadcrumbs ?? [
      { label: "IntelliQR" },
      {
        label: pageLabel,
        href: location.pathname,
      },
    ];

  return (
    <div className="flex h-screen overflow-hidden bg-[#0A0A14]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar title={title} breadcrumbs={resolvedBreadcrumbs} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
