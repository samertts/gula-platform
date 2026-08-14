import { Link, useLocation } from "react-router-dom";
import {
  BellRing,
  ClipboardList,
  FlaskConical,
  LayoutDashboard,
  Menu,
  UserCircle,
  Users,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { hasPermission } from "@/permissions";
import { useAuth } from "@/contexts/AuthContext";
import { useLocale } from "@/contexts/LocaleContext";

interface MobileBottomNavProps {
  onOpenMenu: () => void;
}

interface MobileNavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  permission?: string;
  roles?: string[];
}

const primaryItems: MobileNavItem[] = [
  { label: "الرئيسية", path: "/dashboard", icon: LayoutDashboard },
  { label: "المرضى", path: "/patients", icon: Users, permission: "patients:read" },
  { label: "الطلبات", path: "/orders", icon: ClipboardList, permission: "orders:read" },
  { label: "النتائج", path: "/results", icon: FlaskConical, permission: "results:read" },
  { label: "التنبيهات", path: "/alerts", icon: BellRing, permission: "results:read" },
];

const citizenItems: MobileNavItem[] = [
  { label: "الرئيسية", path: "/dashboard", icon: LayoutDashboard },
  { label: "مساحتي", path: "/citizen", icon: UserCircle, roles: ["citizen"] },
  { label: "التنبيهات", path: "/notifications", icon: BellRing },
];

function canUseItem(item: MobileNavItem, role: string) {
  if (item.roles && !item.roles.includes(role)) return false;
  if (item.permission && !hasPermission(role, item.permission)) return false;
  return true;
}

export function MobileBottomNav({ onOpenMenu }: MobileBottomNavProps) {
  const { user } = useAuth();
  const { isRTL } = useLocale();
  const location = useLocation();
  const role = user?.role ?? "citizen";
  const isCitizen = role === "citizen";
  const items = (isCitizen ? citizenItems : primaryItems)
    .filter((item) => canUseItem(item, role))
    .slice(0, 4);

  return (
    <nav
      aria-label={isRTL ? "التنقل السريع" : "Quick navigation"}
      className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200/80 bg-white/95 px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 shadow-[0_-14px_32px_-26px_rgba(15,23,42,0.6)] backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/95 md:hidden"
    >
      <div className="mx-auto grid max-w-lg grid-cols-5 gap-1">
        {items.map((item) => {
          const Icon = item.icon;
          const active = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);
          return (
            <Link
              key={item.path}
              to={item.path}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-h-12 min-w-0 flex-col items-center justify-center gap-1 rounded-xl px-1 text-[10px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
                active
                  ? "bg-teal-50 text-[#0D9488] ring-1 ring-teal-100 dark:bg-teal-950/35 dark:text-teal-200 dark:ring-teal-900/60"
                  : "text-muted-foreground hover:bg-slate-100 hover:text-[#0F172A] dark:hover:bg-white/10 dark:hover:text-white",
              )}
            >
              <Icon className="h-4.5 w-4.5 shrink-0" aria-hidden="true" />
              <span className="max-w-full truncate">{item.label}</span>
            </Link>
          );
        })}
        <button
          type="button"
          onClick={onOpenMenu}
          className="flex min-h-12 min-w-0 flex-col items-center justify-center gap-1 rounded-xl px-1 text-[10px] font-semibold text-muted-foreground transition-colors hover:bg-slate-100 hover:text-[#0F172A] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:hover:bg-white/10 dark:hover:text-white"
          aria-label={isRTL ? "فتح جميع الأقسام" : "Open all sections"}
        >
          <Menu className="h-4.5 w-4.5" aria-hidden="true" />
          <span>{isRTL ? "المزيد" : "More"}</span>
        </button>
      </div>
    </nav>
  );
}
