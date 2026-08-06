import { Link, useLocation } from "react-router";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { useLocale } from "@/contexts/LocaleContext";
import { NAV_ITEMS, hasPermission } from "@/permissions";
import {
  LayoutDashboard, Users, ClipboardList, FlaskConical, TestTube,
  Building2, ShieldCheck, BellRing, Shield, BarChart3, FileCheck,
  Brain, CreditCard, Fingerprint, Crown, UserCircle, Settings, Lock, Bell,
  Building, Server, DollarSign, Database,
  Scale, Globe, Workflow, Clock, Power,
  ChevronLeft, ChevronRight, LogOut,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui";
import { useState } from "react";

const iconMap: Record<string, LucideIcon> = {
  LayoutDashboard, Users, ClipboardList, FlaskConical, TestTube,
  Building2, ShieldCheck, BellRing, Shield, BarChart3, FileCheck,
  Brain, CreditCard, Fingerprint, Crown, UserCircle, Settings, Lock, Bell,
  Building, Server, DollarSign, Database,
  Scale, Globe, Workflow, Clock, Power,
};

export function Sidebar() {
  const { user, logout } = useAuth();
  const { isRTL } = useLocale();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const renderItems = (items: typeof NAV_ITEMS.main = []) =>
    (items ?? [])
      .filter((item) => !item.permissions || item.permissions.some((p) => hasPermission(user?.role ?? "citizen", p)))
      .map((item) => {
        const Icon = iconMap[item.icon] || LayoutDashboard;
        const active = location.pathname.startsWith(item.path);
        return (
          <Link
            key={item.path}
            to={item.path}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              active
                ? "bg-primary/10 text-primary font-medium"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </Link>
        );
      });

  return (
    <aside
      className={cn(
        "flex flex-col border-l bg-card transition-all duration-300",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-14 items-center border-b px-4">
        <Link to="/" className={cn("flex items-center gap-2 font-bold", collapsed && "justify-center")}>
          <FlaskConical className="h-5 w-5 text-primary" />
          {!collapsed && <span className="truncate">غولا</span>}
        </Link>
        <Button
          variant="ghost"
          size="icon"
          className="mr-auto"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? (isRTL ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />) : (isRTL ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />)}
        </Button>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            الرئيسية
          </p>
          {renderItems(NAV_ITEMS.main)}
        </div>

        {!collapsed && <hr className="my-3" />}
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            المختبر
          </p>
          {renderItems(NAV_ITEMS.lab)}
        </div>

        {!collapsed && <hr className="my-3" />}
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            الإدارة
          </p>
          {renderItems(NAV_ITEMS.admin)}
        </div>

        {!collapsed && <hr className="my-3" />}
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            أدوات
          </p>
          {renderItems(NAV_ITEMS.tools)}
        </div>

        {!collapsed && <hr className="my-3" />}
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            الهوية الوطنية
          </p>
          {renderItems(NAV_ITEMS.niam)}
        </div>

        {!collapsed && <hr className="my-3" />}
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            المؤسسي
          </p>
          {renderItems(NAV_ITEMS.enterprise)}
        </div>

        {!collapsed && <hr className="my-3" />}
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            السريرية
          </p>
          {renderItems(NAV_ITEMS.clinical)}
        </div>

        {!collapsed && <hr className="my-3" />}
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            الوطنية
          </p>
          {renderItems(NAV_ITEMS.national)}
        </div>

        {!collapsed && <hr className="my-3" />}
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            الأنظمة
          </p>
          {renderItems(NAV_ITEMS.systems)}
        </div>

        {!collapsed && <hr className="my-3" />}
        <div className="space-y-1">
          <p className={cn("px-3 text-xs font-semibold text-muted-foreground", collapsed && "sr-only")}>
            الإعدادات
          </p>
          {renderItems(NAV_ITEMS.settings)}
        </div>
      </nav>

      <div className="border-t p-3">
        <div className={cn("flex items-center gap-3", collapsed && "justify-center")}>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
            {user?.name?.charAt(0) || "U"}
          </div>
          {!collapsed && (
            <div className="flex-1 truncate">
              <p className="text-sm font-medium truncate">{user?.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
          )}
          <Button variant="ghost" size="icon" onClick={logout}>
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
}
