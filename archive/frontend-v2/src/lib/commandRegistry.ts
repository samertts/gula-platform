/**
 * Central registry of command-palette actions.
 *
 * Every command points to a real route declared in `App.tsx` (no broken
 * destinations). Commands self-filter by the user's wing/role using the same
 * mapping the Sidebar uses, so the palette never offers actions the user
 * cannot reach.
 */
import {
  Activity,
  BrainCircuit,
  Building2,
  Calendar,
  Code2,
  FlaskConical,
  Globe,
  History,
  Image as ImageIcon,
  Keyboard as KeyboardIcon,
  LayoutDashboard as LayoutDashboardIcon,
  Microscope,
  Pill,
  Server,
  Settings,
  ShieldCheck,
  TestTube,
  User,
  Users,
} from 'lucide-react';
import type { NavigateFunction } from 'react-router-dom';

import type { Translation } from '../translations';
import type { UserProfile, UserWing } from '../types/domain';
import {
  filterByWings,
  scoreCommand as scoreCommandCore,
  searchCommands as searchCommandsCore,
  wingsForProfile as wingsForProfileCore,
  type SearchableCommand,
} from './commandRegistryCore';

export type CommandCategory =
  | 'navigation'
  | 'patients'
  | 'lab'
  | 'citizen'
  | 'ministry'
  | 'admin'
  | 'tools'
  | 'help';

export interface CommandContext {
  navigate: NavigateFunction;
  t: Translation;
  profile: UserProfile | null;
  /** Open the keyboard-shortcuts overlay. */
  openShortcuts: () => void;
}

export interface CommandDefinition {
  id: string;
  label: (t: Translation) => string;
  hint?: (t: Translation) => string;
  category: CommandCategory;
  /** Lucide icon component. */
  icon: typeof Activity;
  /** Sequence of single-key tokens that activate the command, e.g. ['G','D']. */
  shortcut?: readonly string[];
  /** Wings allowed to see this command. Empty/omitted means any. */
  wings?: readonly UserWing[];
  /** Free-text keywords to make fuzzy search forgiving. */
  keywords?: readonly string[];
  run: (ctx: CommandContext) => void;
}

/**
 * Re-export of the core helper. The core module is React-free so it can be
 * unit-tested with plain Node.
 */
export const wingsForProfile = wingsForProfileCore;

const ALL_COMMANDS: readonly CommandDefinition[] = [
  // ── Navigation ────────────────────────────────────────────────────────
  {
    id: 'nav.dashboard',
    label: (t) => t.goToDashboard ?? t.dashboard,
    category: 'navigation',
    icon: LayoutDashboardIcon,
    shortcut: ['G', 'D'],
    keywords: ['home', 'overview', 'start'],
    run: ({ navigate }) => navigate('/'),
  },
  {
    id: 'nav.patients',
    label: (t) => t.healthRecords,
    category: 'patients',
    icon: User,
    shortcut: ['G', 'P'],
    wings: ['doctor', 'admin'],
    keywords: ['patient', 'records', 'people'],
    run: ({ navigate }) => navigate('/patients'),
  },
  {
    id: 'nav.appointments',
    label: (t) => t.appointments,
    category: 'navigation',
    icon: Calendar,
    shortcut: ['G', 'A'],
    keywords: ['schedule', 'calendar'],
    run: ({ navigate }) => navigate('/appointments'),
  },
  {
    id: 'nav.intelligence',
    label: (t) => t.medicalIntelligence,
    category: 'tools',
    icon: BrainCircuit,
    shortcut: ['G', 'I'],
    wings: ['doctor', 'admin'],
    keywords: ['ai', 'intelligence', 'reasoning'],
    run: ({ navigate }) => navigate('/intelligence'),
  },
  {
    id: 'nav.lab',
    label: (t) => t.labWing,
    category: 'lab',
    icon: Microscope,
    shortcut: ['G', 'L'],
    wings: ['lab', 'admin', 'regulator'],
    keywords: ['laboratory', 'lims'],
    run: ({ navigate }) => navigate('/lab/dashboard'),
  },
  {
    id: 'nav.lab.queue',
    label: (t) => t.workQueue,
    category: 'lab',
    icon: TestTube,
    wings: ['lab', 'admin'],
    keywords: ['tasks', 'queue', 'pending'],
    run: ({ navigate }) => navigate('/lab/queue'),
  },
  {
    id: 'nav.lab.samples',
    label: (t) => t.sampleTracking,
    category: 'lab',
    icon: FlaskConical,
    wings: ['lab', 'admin'],
    keywords: ['specimen', 'tracking'],
    run: ({ navigate }) => navigate('/lab/samples'),
  },
  {
    id: 'nav.lab.qc',
    label: (t) => t.qcControl,
    category: 'lab',
    icon: ShieldCheck,
    wings: ['lab', 'admin', 'regulator'],
    keywords: ['quality', 'qc', 'standards'],
    run: ({ navigate }) => navigate('/lab/qc'),
  },
  {
    id: 'nav.lab.devices',
    label: (t) => t.deviceManagement,
    category: 'lab',
    icon: Microscope,
    wings: ['lab', 'admin'],
    run: ({ navigate }) => navigate('/lab/devices'),
  },
  {
    id: 'nav.lab.imaging',
    label: () => 'Imaging Lab',
    category: 'lab',
    icon: ImageIcon,
    wings: ['lab', 'admin'],
    keywords: ['image', 'radiology'],
    run: ({ navigate }) => navigate('/lab/imaging'),
  },

  // ── Citizen ───────────────────────────────────────────────────────────
  {
    id: 'nav.citizen.dashboard',
    label: (t) => t.citizenWing,
    category: 'citizen',
    icon: User,
    wings: ['citizen', 'admin'],
    run: ({ navigate }) => navigate('/citizen/dashboard'),
  },
  {
    id: 'nav.citizen.results',
    label: (t) => t.labResults,
    category: 'citizen',
    icon: TestTube,
    wings: ['citizen', 'admin'],
    keywords: ['results', 'reports'],
    run: ({ navigate }) => navigate('/citizen/results'),
  },
  {
    id: 'nav.citizen.medications',
    label: (t) => t.medicineCabinet,
    category: 'citizen',
    icon: Pill,
    wings: ['citizen', 'admin'],
    keywords: ['drugs', 'prescriptions'],
    run: ({ navigate }) => navigate('/citizen/medications'),
  },
  {
    id: 'nav.citizen.family',
    label: (t) => t.familyManagement,
    category: 'citizen',
    icon: Users,
    wings: ['citizen', 'admin'],
    run: ({ navigate }) => navigate('/citizen/family'),
  },
  {
    id: 'nav.citizen.assistant',
    label: () => 'AI Assistant',
    category: 'citizen',
    icon: BrainCircuit,
    wings: ['citizen', 'admin'],
    keywords: ['help', 'chat', 'ai'],
    run: ({ navigate }) => navigate('/citizen/assistant'),
  },

  // ── Ministry / Admin ──────────────────────────────────────────────────
  {
    id: 'nav.ministry.dashboard',
    label: (t) => t.ministryWing,
    category: 'ministry',
    icon: Building2,
    wings: ['ministry', 'admin'],
    run: ({ navigate }) => navigate('/ministry/dashboard'),
  },
  {
    id: 'nav.ministry.epi',
    label: () => 'Epidemiology',
    category: 'ministry',
    icon: Activity,
    wings: ['ministry', 'admin'],
    keywords: ['outbreak', 'surveillance'],
    run: ({ navigate }) => navigate('/ministry/epidemiology'),
  },
  {
    id: 'nav.ministry.analytics',
    label: (t) => t.analytics,
    category: 'ministry',
    icon: BrainCircuit,
    wings: ['ministry', 'researcher', 'admin'],
    run: ({ navigate }) => navigate('/ministry/analytics'),
  },
  {
    id: 'nav.admin.audit',
    label: (t) => t.auditLogs,
    category: 'admin',
    icon: History,
    wings: ['admin', 'regulator'],
    keywords: ['audit', 'logs', 'compliance'],
    run: ({ navigate }) => navigate('/admin/audit'),
  },
  {
    id: 'nav.admin.infrastructure',
    label: (t) => t.clusterHealth,
    category: 'admin',
    icon: Server,
    wings: ['admin'],
    run: ({ navigate }) => navigate('/admin/infrastructure'),
  },
  {
    id: 'nav.admin.architecture',
    label: (t) => t.systemsArchitecture,
    category: 'admin',
    icon: Code2,
    wings: ['admin', 'system'],
    run: ({ navigate }) => navigate('/admin/architecture'),
  },
  {
    id: 'nav.admin.integrations',
    label: (t) => t.connectedApis,
    category: 'admin',
    icon: Globe,
    wings: ['admin'],
    run: ({ navigate }) => navigate('/admin/integrations'),
  },

  // ── Help / shared ────────────────────────────────────────────────────
  {
    id: 'help.shortcuts',
    label: () => 'Keyboard Shortcuts',
    category: 'help',
    icon: KeyboardIcon,
    shortcut: ['?'],
    keywords: ['help', 'keys', 'cheatsheet'],
    run: ({ openShortcuts }) => openShortcuts(),
  },
  {
    id: 'nav.settings',
    label: (t) => t.settings,
    category: 'navigation',
    icon: Settings,
    shortcut: ['G', 'S'],
    run: ({ navigate }) => navigate('/settings'),
  },
];

/**
 * Filter commands by the active user's wings. Always returns help/global
 * commands (those without a wings restriction).
 */
export function commandsForProfile(
  profile: UserProfile | null,
): CommandDefinition[] {
  return filterByWings(ALL_COMMANDS as readonly CommandDefinition[], wingsForProfile(profile));
}

export function scoreCommand(cmd: CommandDefinition, t: Translation, query: string): number {
  return scoreCommandCore(cmd as unknown as SearchableCommand, t, query);
}

export function searchCommands(
  commands: readonly CommandDefinition[],
  t: Translation,
  query: string,
): CommandDefinition[] {
  return searchCommandsCore(commands as unknown as readonly SearchableCommand[], t, query) as CommandDefinition[];
}

export const ALL_COMMANDS_FOR_TESTS = ALL_COMMANDS;
