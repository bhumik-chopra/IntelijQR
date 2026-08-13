import React from "react";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { BarChart3, Bell, ChevronDown, Layers3, LayoutDashboard, LogOut, Moon, QrCode, ScanLine, Share2, ShieldCheck, Sun, UserRound } from "lucide-react";
import { Link, NavLink, useNavigate } from "react-router-dom";

import { authApi, useAuth } from "../../features/auth";
import { LanguageSelector, useLocale, type Locale } from "../../features/i18n";
import { useTheme } from "../../hooks/useTheme";
import { useNotificationUnread } from "../../features/notifications";
import { cn } from "../../lib/cn";
import { Avatar, Badge } from "../ui";
import { BackendStatus } from "../BackendStatus";

interface NavbarProps {
  title?: string;
  breadcrumbs?: { label: string; href?: string }[];
}

export const Navbar: React.FC<NavbarProps> = ({ title, breadcrumbs }) => {
  const { user, logout, refreshUser } = useAuth();
  const { t } = useLocale();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const { unread } = useNotificationUnread();

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      navigate("/login", { replace: true });
    }
  };
  const persistLocale = async (locale: Locale) => {
    if (!user) return;
    try { await authApi.updateLocale(locale); await refreshUser(); } catch { /* The local selection remains usable. */ }
  };

  return (
    <header className="app-navbar sticky top-0 z-40 flex h-16 items-center border-b border-white/6 bg-[#0A0A14]/80 px-4 backdrop-blur-xl sm:px-6">
      <div className="flex min-w-0 flex-1 items-center gap-2">
        {breadcrumbs ? (
          <nav aria-label="Breadcrumb" className="hidden items-center gap-1.5 text-sm sm:flex">
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={`${crumb.label}-${index}`}>
                {index > 0 && <span className="text-slate-700">/</span>}
                {crumb.href && index < breadcrumbs.length - 1 ? (
                  <Link
                    to={crumb.href}
                    className="text-slate-600 transition-colors hover:text-slate-400"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span
                    className={cn(
                      index === breadcrumbs.length - 1
                        ? "font-medium text-slate-200"
                        : "text-slate-600",
                    )}
                  >
                    {crumb.label}
                  </span>
                )}
              </React.Fragment>
            ))}
          </nav>
        ) : (
          <h1 className="truncate text-base font-semibold text-slate-200">{title}</h1>
        )}

        <nav aria-label="Mobile navigation" className="flex min-w-0 items-center gap-1 overflow-x-auto sm:hidden">
          <NavLink
            to="/dashboard"
            aria-label={t("nav.dashboard")}
            className={({ isActive }) => cn("rounded-lg p-2", isActive ? "bg-violet-500/15 text-violet-300" : "text-slate-500")}
          >
            <LayoutDashboard className="h-4 w-4" />
          </NavLink>
          <NavLink
            to="/generator"
            aria-label={t("nav.generator")}
            className={({ isActive }) => cn("rounded-lg p-2", isActive ? "bg-violet-500/15 text-violet-300" : "text-slate-500")}
          >
            <QrCode className="h-4 w-4" />
          </NavLink>
          <NavLink
            to="/scanner"
            aria-label={t("nav.scanner")}
            className={({ isActive }) => cn("rounded-lg p-2", isActive ? "bg-violet-500/15 text-violet-300" : "text-slate-500")}
          >
            <ScanLine className="h-4 w-4" />
          </NavLink>
          <NavLink
            to="/analytics"
            aria-label={t("nav.analytics")}
            className={({ isActive }) => cn("rounded-lg p-2", isActive ? "bg-violet-500/15 text-violet-300" : "text-slate-500")}
          >
            <BarChart3 className="h-4 w-4" />
          </NavLink>
          <NavLink
            to="/bulk"
            aria-label={t("nav.bulk")}
            className={({ isActive }) => cn("rounded-lg p-2", isActive ? "bg-violet-500/15 text-violet-300" : "text-slate-500")}
          >
            <Layers3 className="h-4 w-4" />
          </NavLink>
          <NavLink
            to="/share-vault"
            aria-label={t("nav.share")}
            className={({ isActive }) => cn("rounded-lg p-2", isActive ? "bg-violet-500/15 text-violet-300" : "text-slate-500")}
          >
            <Share2 className="h-4 w-4" />
          </NavLink>
          {user?.role === "admin" && <NavLink
            to="/admin"
            aria-label={t("nav.admin")}
            className={({ isActive }) => cn("rounded-lg p-2", isActive ? "bg-violet-500/15 text-violet-300" : "text-slate-500")}
          >
            <ShieldCheck className="h-4 w-4" />
          </NavLink>}
        </nav>
      </div>

      <div className="flex items-center gap-1.5 sm:gap-2">
        <BackendStatus compact />
        <div className="hidden md:block"><LanguageSelector compact onLocaleChange={(locale) => void persistLocale(locale)} /></div>
        <Link to="/notifications" aria-label={`${unread} unread notifications`} className="relative flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 transition-colors hover:bg-white/6 hover:text-white">
          <Bell className="h-4 w-4" />
          {unread > 0 && <span className="absolute right-0.5 top-0.5 flex min-h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-bold text-white">{unread > 99 ? "99+" : unread}</span>}
        </Link>
        <button
          id="navbar-theme-toggle"
          type="button"
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 transition-colors hover:bg-white/6 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/60"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button
              id="navbar-user-menu"
              className="flex h-9 cursor-pointer items-center gap-2.5 rounded-xl px-2 transition-all hover:bg-white/6 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/60"
              aria-label="User menu"
            >
              <Avatar name={user?.name ?? "User"} size="sm" />
              {user && (
                <span className="hidden max-w-[120px] truncate text-sm font-medium text-slate-300 md:block">
                  {user.name}
                </span>
              )}
              <ChevronDown className="h-3.5 w-3.5 text-slate-600" />
            </button>
          </DropdownMenu.Trigger>

          <DropdownMenu.Portal>
            <DropdownMenu.Content
              align="end"
              sideOffset={8}
              className="z-50 min-w-[220px] animate-fade-in-scale rounded-2xl border border-white/8 bg-[#141428] p-1.5 shadow-[0_8px_40px_rgba(0,0,0,0.6)]"
            >
              <div className="mb-1 border-b border-white/6 px-3 py-3">
                <p className="truncate text-sm font-semibold text-slate-200">{user?.name ?? "User"}</p>
                <p className="truncate text-xs text-slate-500">{user?.email ?? ""}</p>
                <Badge variant="purple" className="mt-1.5 text-[10px]">
                  {user?.role === "admin" ? "Admin" : "Member"}
                </Badge>
              </div>

              <DropdownMenu.Item
                id="navbar-menu-profile"
                onSelect={() => navigate("/profile")}
                className="flex cursor-pointer items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-300 outline-none transition-colors hover:bg-white/6 hover:text-white"
              >
                <UserRound className="h-4 w-4" />
                {t("nav.profile")}
              </DropdownMenu.Item>

              {user?.role === "admin" && <DropdownMenu.Item
                id="navbar-menu-administration"
                onSelect={() => navigate("/admin")}
                className="flex cursor-pointer items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-violet-300 outline-none transition-colors hover:bg-violet-500/8 hover:text-violet-200"
              >
                <ShieldCheck className="h-4 w-4" />
                {t("nav.admin")}
              </DropdownMenu.Item>}

              <DropdownMenu.Item
                id="navbar-menu-logout"
                onSelect={() => void handleLogout()}
                className="flex cursor-pointer items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-red-400 outline-none transition-colors hover:bg-red-500/8 hover:text-red-300"
              >
                <LogOut className="h-4 w-4" />
                {t("nav.logout")}
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    </header>
  );
};
