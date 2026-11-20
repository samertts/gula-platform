import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { cn, getRoleLabel } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import type { UserRole } from "@/types";
import { useLocale } from "@/contexts/LocaleContext";
import { NAV_ITEMS, hasPermission } from "@/permissions";
import { hasReflectedPermission } from "@/permissions/liveCapabilities";
import {
  Activity,
  BarChart3,
  Bell,
  BellRing,
  Brain,
  Building,
  Building2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  CreditCard,
  Database,
  DollarSign,
  FileCheck,
  FlaskConical,
  Globe,
  LayoutDashboard,
  Lock,
  LogOut,
  Scale,
  Server,
  Settings,
  Shield,
  ShieldCheck,
  TestTube,
  UserCircle,
  Users,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui";
import { DemoEnvironmentBadge, GulaBrand } from "@/components/shared/GulaBrand";
import { prefetchRoute } from "@/routes/prefetch";

const iconMap: Record<string, LucideIcon> = {
  Activity,
  BarChart3,
  Bell,
  BellRing,
  Brain,
  Building,
  Building2,
  ClipboardList,
  CreditCard,
  Database,
  DollarSign,
  FileCheck,
  FlaskConical,
  Globe,
  LayoutDashboard,
  Lock,
  Scale,
  Server,
  Settings,
  Shield,
  ShieldCheck,
  TestTube,
  UserCircle,
  Users,
  Workflow,
};

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

const navigationGroups = [
  "main",
  "lab",
  "admin",
  "tools",
  "niam",
  "enterprise",
  "clinical",
  "national",
  "systems",
  "settings",
] as const;

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  const { user, logout, demoMode, effectivePermissions } = useAuth();
  const { isRTL } = useLocale();
  const { t } = useTranslation();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const renderItems = (groupKey: keyof typeof NAV_ITEMS) => {
    const items = NAV_ITEMS[groupKey] ?? [];
    return items
      .filter((item) => {
        if (
          item.institutionalOnly &&
          (!user?.lab_id || user.role === "citizen")
        )
          return false;
        if (item.roles && !item.roles.includes(user?.role as UserRole))
          return false;
        if (!item.permissions) return true;
        if (demoMode) {
          return item.permissions.some((permission) =>
            hasPermission(user?.role ?? "citizen", permission),
          );
        }
        // Live capabilities are UX hints only. The server remains the authorization boundary.
        return hasReflectedPermission(effectivePermissions, item.permissions);
      })
      .map((item) => {
        const Icon = iconMap[item.icon] || Activity;
        const active =
          location.pathname === item.path ||
          location.pathname.startsWith(`${item.path}/`);
        const label = item.label.startsWith("nav.")
          ? t(item.label)
          : item.label;
        return (
          <Link
            key={item.path}
            to={item.path}
            onClick={onClose}
            onPointerEnter={() => prefetchRoute(item.path)}
            onFocus={() => prefetchRoute(item.path)}
            aria-current={active ? "page" : undefined}
            title={collapsed ? label : undefined}
            className={cn(
              "group flex min-h-10 items-center gap-3 rounded-xl px-3 text-sm transition-colors",
              active
                ? "bg-teal-50 font-semibold text-[#0D9488] shadow-sm ring-1 ring-teal-100 dark:bg-teal-950/35 dark:text-teal-200 dark:ring-teal-900/60"
                : "text-muted-foreground hover:bg-slate-100 hover:text-[#0F172A] dark:hover:bg-white/[0.06] dark:hover:text-white",
              collapsed && "justify-center px-0",
            )}
          >
            <Icon className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </Link>
        );
      });
  };

  return (
    <>
      <aside
        aria-label={t("mobileNav.mainNavigation")}
        className={cn(
          "fixed inset-y-0 right-0 z-50 flex w-72 flex-col border-l border-slate-200/80 bg-white/95 shadow-[0_24px_70px_-36px_rgba(15,23,42,0.72)] backdrop-blur-xl transition-[transform,visibility] duration-200 dark:border-white/10 dark:bg-slate-950/95 lg:static lg:z-auto lg:visible lg:pointer-events-auto lg:shadow-none",
          mobileOpen
            ? "translate-x-0 visible pointer-events-auto"
            : "translate-x-full invisible pointer-events-none lg:translate-x-0",
          collapsed && "lg:w-[72px]",
        )}
      >
        <div
          className={cn(
            "flex h-16 shrink-0 items-center border-b px-4",
            collapsed && "justify-center px-2",
          )}
        >
          <Link to="/dashboard" onClick={onClose} className="flex items-center">
            <GulaBrand compact={collapsed} />
          </Link>
          {!collapsed && (
            <span className="mr-auto text-[10px] font-medium text-muted-foreground">
              {t("mobileNav.operationsCenter")}
            </span>
          )}
          <Button
            variant="ghost"
            size="icon"
            className={cn("mr-2 hidden lg:inline-flex", collapsed && "mr-0")}
            onClick={() => setCollapsed((value) => !value)}
            aria-label={
              collapsed
                ? t("mobileNav.expandSidebar")
                : t("mobileNav.collapseSidebar")
            }
          >
            {collapsed ? (
              isRTL ? (
                <ChevronLeft className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )
            ) : isRTL ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        <div
          className={cn(
            "flex shrink-0 flex-col gap-2 border-b p-3",
            collapsed && "items-center px-2",
          )}
        >
          {demoMode && !collapsed && <DemoEnvironmentBadge />}
          <div
            className={cn(
              "flex items-center gap-2",
              collapsed && "justify-center",
            )}
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-teal-50 text-xs font-bold text-[#0D9488] dark:bg-teal-950/40 dark:text-teal-200">
              {user?.name?.charAt(0) || t("mobileNav.userFallback").charAt(0)}
            </span>
            {!collapsed && (
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold">
                  {user?.name || t("mobileNav.userFallback")}
                </p>
                <p className="truncate text-[10px] text-muted-foreground">
                  {demoMode
                    ? `${getRoleLabel(user?.role || "citizen")} · ${t("mobileNav.readOnly")}`
                    : getRoleLabel(user?.role || "citizen")}
                </p>
              </div>
            )}
          </div>
          {demoMode && !collapsed && (
            <p className="rounded-xl border border-amber-500/20 bg-amber-500/10 px-2.5 py-1.5 text-[10px] leading-5 text-amber-800 dark:text-amber-200">
              {t("mobileNav.syntheticReadOnly")}
            </p>
          )}
        </div>

        <nav
          className="flex-1 space-y-4 overflow-y-auto p-3"
          aria-label={t("mobileNav.operationsCenter")}
        >
          {navigationGroups.map((groupKey) => {
            const items = renderItems(groupKey);
            if (!items.length) return null;
            return (
              <section
                key={groupKey}
                aria-label={t(`mobileNav.groups.${groupKey}`)}
                className="space-y-1"
              >
                {!collapsed && (
                  <h2 className="px-3 pb-1 text-[10px] font-semibold tracking-wide text-muted-foreground">
                    {t(`mobileNav.groups.${groupKey}`)}
                  </h2>
                )}
                {items}
              </section>
            );
          })}
        </nav>

        <div className={cn("shrink-0 border-t p-3", collapsed && "px-2")}>
          <Button
            variant="ghost"
            size={collapsed ? "icon" : "default"}
            className={cn(
              "w-full justify-start gap-3",
              collapsed && "justify-center",
            )}
            onClick={() => void logout()}
            title={collapsed ? t("nav.logout") : undefined}
          >
            <LogOut className="h-4 w-4" />
            {!collapsed && <span>{t("nav.logout")}</span>}
          </Button>
        </div>
      </aside>
      {mobileOpen && (
        <button
          type="button"
          aria-label={t("mobileNav.closeSections")}
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden"
        />
      )}
    </>
  );
}
