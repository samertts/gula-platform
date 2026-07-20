import type { UserRole } from '@/types/backend';
import {
  LayoutDashboard, Users, FlaskConical, TestTubes, ClipboardList,
  Microscope, Shield, Settings, Building2, Stethoscope, Activity,
  Bell, FileText, BarChart3, UserCog, Database, Wifi, Truck,
  ShieldAlert, Ban, Fingerprint, HeartPulse, Syringe, Pill,
  Ambulance,Radiation, Brain, Search, PlusCircle, FileSpreadsheet,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  labelKey: string;
  icon: LucideIcon;
  path: string;
  roles?: UserRole[];
  children?: NavItem[];
  badge?: string;
}

export const NAV_ITEMS: NavItem[] = [
  { labelKey: 'dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { labelKey: 'patients', icon: Users, path: '/patients', roles: ['master_admin', 'admin', 'lab_admin', 'doctor', 'staff', 'lab_staff'] },
  { labelKey: 'orders', icon: ClipboardList, path: '/orders', roles: ['master_admin', 'admin', 'lab_admin', 'doctor', 'staff', 'lab_staff', 'technician'] },
  { labelKey: 'results', icon: TestTubes, path: '/results', roles: ['master_admin', 'admin', 'lab_admin', 'doctor', 'staff', 'lab_staff', 'technician'] },
  { labelKey: 'samples', icon: FlaskConical, path: '/samples', roles: ['master_admin', 'admin', 'lab_admin', 'staff', 'lab_staff', 'technician'] },
  { labelKey: 'qualityControl', icon: Shield, path: '/quality-control', roles: ['master_admin', 'admin', 'lab_admin', 'staff'] },
  { labelKey: 'Dashboard', icon: Activity, path: '/analytics', roles: ['master_admin', 'admin', 'lab_admin', 'doctor'] },
  { labelKey: 'reports', icon: FileText, path: '/reports', roles: ['master_admin', 'admin', 'lab_admin'] },
  {
    labelKey: 'administration',
    icon: Settings,
    path: '/admin',
    roles: ['master_admin', 'admin', 'lab_admin', 'ministry_admin', 'province_admin'],
    children: [
      { labelKey: 'users', icon: UserCog, path: '/admin/users' },
      { labelKey: 'labs', icon: Building2, path: '/admin/labs' },
      { labelKey: 'auditLog', icon: FileSpreadsheet, path: '/admin/audit-log' },
      { labelKey: 'systemHealth', icon: Activity, path: '/admin/system' },
      { labelKey: 'subscription', icon: Database, path: '/admin/tiers' },
    ],
  },
  {
    labelKey: 'integrations',
    icon: Wifi,
    path: '/integrations',
    roles: ['master_admin', 'admin'],
    children: [
      { labelKey: 'edgeDevices', icon: Truck, path: '/integrations/edge-devices' },
      { labelKey: 'apiKeys', icon: Fingerprint, path: '/integrations/api-keys' },
    ],
  },
  {
    labelKey: 'clinical',
    icon: Stethoscope,
    path: '/clinical',
    roles: ['master_admin', 'admin', 'lab_admin', 'doctor'],
    children: [
      { labelKey: 'clinicalNotes', icon: FileText, path: '/clinical/notes' },
      { labelKey: 'ehr', icon: HeartPulse, path: '/clinical/ehr' },
    ],
  },
  {
    labelKey: 'security',
    icon: ShieldAlert,
    path: '/security',
    roles: ['master_admin', 'admin'],
    children: [
      { labelKey: 'securityLogs', icon: Ban, path: '/security/logs' },
      { labelKey: 'mfa', icon: Fingerprint, path: '/security/mfa' },
      { labelKey: 'sessionManagement', icon: UserCog, path: '/security/sessions' },
    ],
  },
];

export function filterNavByRole(items: NavItem[], role: UserRole): NavItem[] {
  return items
    .filter((item) => !item.roles || item.roles.includes(role))
    .map((item) => ({
      ...item,
      children: item.children ? filterNavByRole(item.children, role) : undefined,
    }));
}
