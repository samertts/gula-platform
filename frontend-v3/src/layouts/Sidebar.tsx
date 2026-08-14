import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { cn, getRoleLabel } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { useLocale } from "@/contexts/LocaleContext";
import { NAV_ITEMS, hasPermission } from "@/permissions";
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
  { key: "main", label: "الرئيسية" },
  { key: "lab", label: "المختبر" },
  { key: "admin", label: "الإدارة" },
  { key: "tools", label: "الأدوات" },
  { key: "niam", label: "الهوية الوطنية" },
  { key: "enterprise", label: "المؤسسي" },
  { key: "clinical", label: "السريري" },
  { key: "national", label: "الوطنية" },
  { key: "systems", label: "الأنظمة" },
  { key: "settings", label: "الإعدادات" },
] as const;

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  const { user, logout, demoMode } = useAuth();
  const { isRTL } = useLocale();
  const { t } = useTranslation();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const renderItems = (groupKey: keyof typeof NAV_ITEMS) => {
    const items = NAV_ITEMS[groupKey] ?? [];
    return items
      .filter(
        (item) =>
          !item.permissions ||
          !demoMode ||
          item.permissions.some((permission) => hasPermission(user?.role ?? "citizen", permission)),
      )
      .map((item) => {
        const Icon = iconMap[item.icon] || Activity;
        const active = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);
        const label = item.label.startsWith("nav.") ? t(item.label) : item.label;
        return (
          <Link
            key={item.path}
            to={item.path}
            onClick={onClose}
            aria-current={active ? "page" : undefined}
            title={collapsed ? label : undefined}
            className={cn(
              "group flex min-h-10 items-center gap-3 rounded-xl px-3 text-sm transition-colors",
              active
                ? "bg-primary/10 font-semibold text-primary shadow-sm"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
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
        aria-label="التنقل الرئيسي"
        className={cn(
          "fixed inset-y-0 right-0 z-50 flex w-72 flex-col border-l bg-card shadow-xl transition-[transform,visibility] duration-200 md:static md:z-auto md:visible md:pointer-events-auto md:shadow-none",
          mobileOpen ? "translate-x-0 visible pointer-events-auto" : "translate-x-full invisible pointer-events-none md:translate-x-0",
          collapsed && "md:w-[72px]",
        )}
      >
        <div className={cn("flex h-16 shrink-0 items-center border-b px-4", collapsed && "justify-center px-2")}>
          <Link to="/dashboard" onClick={onClose} className="flex items-center">
            <GulaBrand compact={collapsed} />
          </Link>
          {!collapsed && <span className="mr-auto text-[10px] font-medium text-muted-foreground">مركز العمليات</span>}
          <Button
            variant="ghost"
            size="icon"
            className={cn("mr-2 hidden md:inline-flex", collapsed && "mr-0")}
            onClick={() => setCollapsed((value) => !value)}
            aria-label={collapsed ? "توسيع القائمة" : "طي القائمة"}
          >
            {collapsed ? (isRTL ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />) : (isRTL ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />)}
          </Button>
        </div>

        <div className={cn("flex shrink-0 flex-col gap-2 border-b p-3", collapsed && "items-center px-2")}>
          {demoMode && !collapsed && <DemoEnvironmentBadge />}
          <div className={cn("flex items-center gap-2", collapsed && "justify-center")}>
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
              {user?.name?.charAt(0) || "م"}
            </span>
            {!collapsed && (
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold">{user?.name || "مستخدم GULA"}</p>
                <p className="truncate text-[10px] text-muted-foreground">{demoMode ? `${getRoleLabel(user?.role || "citizen")} · قراءة فقط` : getRoleLabel(user?.role || "citizen")}</p>
              </div>
            )}
          </div>
          {demoMode && !collapsed && <p className="rounded-lg bg-amber-500/10 px-2.5 py-1.5 text-[10px] leading-5 text-amber-700 dark:text-amber-200">الجلسة اصطناعية؛ عمليات الكتابة والتكاملات الخارجية محظورة.</p>}
        </div>

        <nav className="flex-1 space-y-4 overflow-y-auto p-3" aria-label="أقسام المنصة">
          {navigationGroups.map((group) => {
            const items = renderItems(group.key);
            if (!items.length) return null;
            return (
              <section key={group.key} aria-label={group.label} className="space-y-1">
                {!collapsed && <h2 className="px-3 pb-1 text-[10px] font-semibold tracking-wide text-muted-foreground">{group.label}</h2>}
                {items}
              </section>
            );
          })}
        </nav>

        <div className={cn("shrink-0 border-t p-3", collapsed && "px-2")}>
          <Button variant="ghost" size={collapsed ? "icon" : "default"} className={cn("w-full justify-start gap-3", collapsed && "justify-center")} onClick={() => void logout()} title={collapsed ? t("nav.logout") : undefined}>
            <LogOut className="h-4 w-4" />
            {!collapsed && <span>{t("nav.logout")}</span>}
          </Button>
        </div>
      </aside>
      {mobileOpen && <button type="button" aria-label="إغلاق القائمة" onClick={onClose} className="fixed inset-0 z-40 bg-slate-950/40 md:hidden" />}
    </>
  );
}
