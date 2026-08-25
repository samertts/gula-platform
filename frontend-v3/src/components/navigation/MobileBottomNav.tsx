import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  BellRing,
  Building,
  ClipboardList,
  FlaskConical,
  LayoutDashboard,
  Menu,
  UserCircle,
  Users,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { hasPermission, NAV_ITEMS } from "@/permissions";
import {
  hasReflectedPermission,
  type ReflectedPermissions,
} from "@/permissions/liveCapabilities";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui";

interface MobileBottomNavProps {
  onOpenMenu: () => void;
  isMenuOpen?: boolean;
}

interface MobileNavItem {
  labelKey: string;
  path: string;
  icon: LucideIcon;
  permissions?: string[];
  roles?: readonly string[];
}

const canonicalNavItems = Object.values(NAV_ITEMS).flat();

function fromCanonical(
  path: string,
  icon: LucideIcon,
  roles?: string[],
): MobileNavItem {
  const item = canonicalNavItems.find((candidate) => candidate.path === path);
  if (!item)
    throw new Error(
      `Mobile navigation path is missing from NAV_ITEMS: ${path}`,
    );
  return {
    labelKey: item.label,
    path: item.path,
    icon,
    permissions: item.permissions,
    roles: roles ?? item.roles,
  };
}

const clinicalItems: MobileNavItem[] = [
  fromCanonical("/dashboard", LayoutDashboard),
  fromCanonical("/patient-management", Users),
  fromCanonical("/orders", ClipboardList),
  fromCanonical("/results", FlaskConical),
  fromCanonical("/alerts", BellRing),
];

const clinicItems: MobileNavItem[] = [
  fromCanonical("/dashboard", LayoutDashboard),
  fromCanonical("/patient-management", Users),
  fromCanonical("/hospital", Building),
  fromCanonical("/reports", ClipboardList),
  fromCanonical("/alerts", BellRing),
];

const citizenItems: MobileNavItem[] = [
  fromCanonical("/dashboard", LayoutDashboard),
  fromCanonical("/my-record", UserCircle),
  fromCanonical("/citizen", UserCircle, ["citizen"]),
  fromCanonical("/notifications", BellRing),
];

function canUseItem(
  item: MobileNavItem,
  role: string,
  demoMode: boolean,
  effectivePermissions: ReflectedPermissions,
) {
  if (item.roles && !item.roles.includes(role)) return false;
  if (!item.permissions?.length) return true;
  if (demoMode)
    return item.permissions.some((permission) =>
      hasPermission(role, permission),
    );
  return hasReflectedPermission(effectivePermissions, item.permissions);
}

function isRouteActive(pathname: string, path: string) {
  const current = pathname.replace(/\/+$/, "") || "/";
  const target = path.replace(/\/+$/, "") || "/";
  return current === target || current.startsWith(`${target}/`);
}

export function MobileBottomNav({
  onOpenMenu,
  isMenuOpen = false,
}: MobileBottomNavProps) {
  const { user, demoMode, effectivePermissions } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const role = user?.role ?? "citizen";
  const isCitizen = role === "citizen";
  const isClinicOperator = ["admin", "master_admin", "lab_admin", "ministry_admin", "province_admin"].includes(role);
  const roleItems = isCitizen ? citizenItems : isClinicOperator ? clinicItems : clinicalItems;
  const items = roleItems
    .filter((item) => canUseItem(item, role, demoMode, effectivePermissions))
    .slice(0, 4);

  return (
    <nav
      aria-label={t("mobileNav.quickNavigation")}
      className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200/80 bg-white/95 px-2 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2 shadow-[0_-14px_32px_-26px_rgba(15,23,42,0.6)] backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/95 md:hidden"
    >
      <div className="mx-auto grid max-w-lg grid-cols-5 gap-1">
        {items.map((item) => {
          const Icon = item.icon;
          const active = isRouteActive(location.pathname, item.path);
          const label = item.labelKey.startsWith("nav.")
            ? t(item.labelKey)
            : item.labelKey;
          return (
            <Link
              key={item.path}
              to={item.path}
              aria-current={active ? "page" : undefined}
              aria-label={
                active ? `${label} — ${t("mobileNav.current")}` : label
              }
              className={cn(
                "relative flex min-h-12 min-w-0 flex-col items-center justify-center gap-1 rounded-xl px-1 text-[10px] font-semibold motion-safe:transition-[background-color,color,box-shadow,transform] motion-safe:duration-150 motion-safe:ease-out motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 motion-safe:active:scale-[0.98]",
                active
                  ? "bg-teal-50 text-[#0D9488] ring-1 ring-teal-100 after:absolute after:inset-x-4 after:top-1 after:h-0.5 after:rounded-full after:bg-[#0D9488] dark:bg-teal-950/35 dark:text-teal-200 dark:ring-teal-900/60 dark:after:bg-teal-300"
                  : "text-muted-foreground hover:bg-slate-100 hover:text-[#0F172A] dark:hover:bg-white/10 dark:hover:text-white",
              )}
            >
              <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
              <span className="max-w-full truncate">{label}</span>
            </Link>
          );
        })}
        <Button
          type="button"
          variant="ghost"
          size="default"
          onClick={onOpenMenu}
          aria-expanded={isMenuOpen}
          aria-label={t("mobileNav.openAllSections")}
          title={t("mobileNav.openAllSections")}
          className="flex h-auto min-h-12 min-w-0 w-full flex-col items-center justify-center gap-1 rounded-xl px-1 py-1 text-[10px] font-semibold text-muted-foreground motion-safe:active:scale-[0.98] motion-reduce:transition-none hover:bg-slate-100 hover:text-[#0F172A] focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:hover:bg-white/10 dark:hover:text-white"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
          <span>{t("mobileNav.more")}</span>
        </Button>
      </div>
    </nav>
  );
}
