import React, { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  QrCode,
  ScanLine,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  Layers3,
  Share2,
  ShieldCheck,
  Bell,
} from "lucide-react";
import { cn } from "../../lib/cn";
import { useAuth } from "../../features/auth";
import { useLocale } from "../../features/i18n";

interface NavItem {
  label: string;
  icon: React.ElementType;
  href: string;
  adminOnly?: boolean;
  translationKey: string;
}

const navGroups: { title?: string; items: NavItem[] }[] = [
  {
    items: [
      { label: "Dashboard", translationKey: "nav.dashboard", icon: LayoutDashboard, href: "/dashboard" },
      { label: "Generator", translationKey: "nav.generator", icon: QrCode, href: "/generator" },
      { label: "Scanner", translationKey: "nav.scanner", icon: ScanLine, href: "/scanner" },
      { label: "Analytics", translationKey: "nav.analytics", icon: BarChart3, href: "/analytics" },
      { label: "BulkForge", translationKey: "nav.bulk", icon: Layers3, href: "/bulk" },
      { label: "ShareVault", translationKey: "nav.share", icon: Share2, href: "/share-vault" },
      { label: "Notifications", translationKey: "nav.notifications", icon: Bell, href: "/notifications" },
      { label: "Administration", translationKey: "nav.admin", icon: ShieldCheck, href: "/admin", adminOnly: true },
    ],
  },
];

interface SidebarProps {
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { user } = useAuth();
  const { t } = useLocale();

  return (
    <aside
      className={cn(
        "app-sidebar relative hidden md:flex flex-col h-screen",
        "bg-[#0A0A14] border-r border-white/6",
        "transition-all duration-300 ease-in-out",
        collapsed ? "w-[68px]" : "w-[240px]",
        className
      )}
    >
      {/* Logo */}
      <NavLink
        to="/dashboard"
        aria-label="Go to dashboard"
        className={cn(
          "flex items-center h-16 px-4 border-b border-white/6",
          "transition-all duration-300",
          collapsed ? "justify-center" : "gap-3"
        )}
      >
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600 to-blue-500 flex items-center justify-center shadow-lg shadow-violet-900/40">
          <QrCode className="w-4 h-4 text-white" />
        </div>
        {!collapsed && (
          <span className="font-bold text-base text-white tracking-tight whitespace-nowrap overflow-hidden">
            Intelli<span className="text-gradient">QR</span>
          </span>
        )}
      </NavLink>

      {/* Nav Groups */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden px-2 py-2 space-y-5">
        {navGroups.map((group, gi) => (
          <div key={gi}>
            {group.title && !collapsed && (
              <p className="px-2 mb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
                {group.title}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.filter((item) => !item.adminOnly || user?.role === "admin").map((item) => {
                const isActive =
                  location.pathname === item.href ||
                  (item.href !== "/" && location.pathname.startsWith(item.href));
                const Icon = item.icon;

                return (
                  <li key={item.href}>
                    <NavLink
                      to={item.href}
                      id={`sidebar-nav-${item.label.toLowerCase().replace(/\s+/g, "-")}`}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 rounded-xl text-sm",
                        "transition-all duration-150 group relative",
                        "focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50",
                        collapsed ? "justify-center px-0 py-2.5" : "",
                        isActive
                          ? "app-nav-active bg-violet-500/12 text-violet-300 font-medium"
                          : "app-nav-item text-slate-500 hover:text-slate-200 hover:bg-white/4 font-normal"
                      )}
                    >
                      {/* Active indicator */}
                      {isActive && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-gradient-to-b from-violet-500 to-blue-500 rounded-full" />
                      )}

                      <Icon
                        className={cn(
                          "flex-shrink-0 w-4 h-4 transition-colors duration-150",
                          isActive ? "text-violet-400" : "text-slate-600 group-hover:text-slate-400"
                        )}
                      />

                      {!collapsed && <span className="flex-1 truncate">{t(item.translationKey)}</span>}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-white/6">
        <button
          id="sidebar-collapse-toggle"
          onClick={() => setCollapsed((c) => !c)}
          className={cn(
            "w-full flex items-center gap-2 px-2 py-2 rounded-xl",
            "text-slate-600 hover:text-slate-300 hover:bg-white/4",
            "text-xs transition-all duration-150",
            collapsed ? "justify-center" : ""
          )}
          aria-label={collapsed ? t("nav.expand") : t("nav.collapse")}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span>{t("nav.collapse")}</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
};
