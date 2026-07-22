import { memo, useMemo, useState, useRef, useCallback, useEffect } from 'react';
import {
  LayoutDashboard, Users, Stethoscope, Microscope, FlaskConical,
  Calendar, FileText, Activity, Pill, BrainCircuit, Building2,
  Shield, Settings, Search, Heart, ClipboardList, TestTube,
  Box, ShieldCheck, Image, Globe, BarChart3, Server, Code2,
  History, Clock, Star, Pin, X, Menu,
  ChevronLeft, User,
  LogOut, ChevronDown, ChevronUp,
  Sparkles, Hash,
  Bot, Home, Command,
  Notebook, ListTodo,
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import { cn } from '../lib/utils';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { signOut } from 'firebase/auth';
import { auth } from '../firebase-auth';
import { UserWing, UserRole } from '../types/domain';
import { useNavigationStore } from '../stores/navigationStore';
import {Avatar, Tooltip, Kbd} from './ui';
interface NavItem {
  to: string;
  icon: any;
  label: string;
  description?: string;
  keywords?: string[];
  roles?: UserRole[];
  badge?: number;
  wing?: UserWing;
}
interface NavGroup {
  id: string;
  icon: any;
  label: string;
  items: NavItem[];
  roles?: UserRole[];
  wing?: UserWing;
}
const ROLE_WING_MAP: Record<UserRole, UserWing[]> = {
  master_admin: ['admin', 'ministry', 'doctor', 'lab', 'citizen', 'researcher', 'regulator', 'system'],
  admin: ['admin', 'ministry', 'doctor', 'lab', 'citizen', 'researcher', 'regulator'],
  ministry_admin: ['ministry', 'citizen'],
  ministry_analyst: ['ministry', 'citizen', 'researcher'],
  ministry_inspector: ['ministry', 'citizen', 'regulator'],
  physician: ['doctor', 'citizen'],
  technician: ['lab', 'citizen'],
  pathologist: ['lab', 'citizen'],
  lab_admin: ['lab', 'citizen'],
  researcher: ['researcher', 'citizen'],
  regulator: ['regulator', 'citizen'],
  auditor: ['regulator', 'citizen'],
  integration_service: ['admin', 'system'],
  citizen: ['citizen'],
};
const ICON_MAP: Record<string, any> = {
  LayoutDashboard, Users, Stethoscope, Microscope, FlaskConical,
  Calendar, FileText, Activity, Pill, BrainCircuit, Building2,
  Shield, Settings, Heart, ClipboardList, TestTube,
  Box, ShieldCheck, Image, Globe, BarChart3, Server, Code2,
  History, Clock, Star, Pin, User, Home, Hash,
  Sparkles, Bot, Notebook, ListTodo,
};
function resolveIcon(name: string): any {
  return ICON_MAP[name] || LayoutDashboard;
}
function buildNavGroups(t: any, role: UserRole): NavGroup[] {
  const wings = ROLE_WING_MAP[role] || ['citizen'];
  const has = (...w: UserWing[]) => w.some(w2 => wings.includes(w2));
  const groups: NavGroup[] = [
    {
      id: 'home',
      icon: 'LayoutDashboard',
      label: String(t.dashboard || 'Dashboard'),
      items: [
        { to: '/', icon: LayoutDashboard, label: String(t.home || 'Home'), description: String(t.roleAdaptive || 'Adaptive dashboard'), keywords: ['home', 'dashboard', 'start'], wing: 'doctor' },
      ],
    },
    {
      id: 'patients',
      icon: 'Users',
      label: String(t.patients || 'Patients'),
      roles: ['master_admin', 'admin', 'physician', 'lab_admin', 'technician', 'pathologist'],
      items: [
        ...(has('doctor', 'admin') ? [{ to: '/patients', icon: Users, label: String(t.patientRegistry || 'Patient Registry'), description: String(t.healthRecords || 'Health Records'), keywords: ['patients', 'registry', 'records'], wing: 'doctor' as UserWing }] : []),
        ...(has('citizen') ? [{ to: '/citizen/register', icon: User, label: String(t.registerPatient || 'Register Patient'), description: String(t.newRegistration || 'New Registration'), keywords: ['register', 'new', 'patient'], wing: 'citizen' as UserWing }] : []),
        ...(has('citizen') ? [{ to: '/citizen/family', icon: Users, label: String(t.familyManagement || 'Family'), description: String(t.familyNetwork || 'Family Network'), keywords: ['family', 'dependents'], wing: 'citizen' as UserWing }] : []),
      ].filter(Boolean) as NavItem[],
    },
    {
      id: 'clinical',
      icon: 'Stethoscope',
      label: String(t.clinical || 'Clinical'),
      roles: ['master_admin', 'admin', 'physician', 'lab_admin', 'technician', 'pathologist', 'citizen'],
      items: [
        ...(has('doctor', 'admin', 'lab') ? [{ to: '/lab/queue', icon: ClipboardList, label: String(t.workQueue || 'Work Queue'), description: String(t.processing || 'Processing'), keywords: ['queue', 'tasks', 'pending'], wing: 'lab' as UserWing }] : []),
        ...(has('doctor', 'admin', 'lab', 'citizen') ? [{ to: '/appointments', icon: Calendar, label: String(t.appointments || 'Appointments'), description: String(t.schedules || 'Schedules'), keywords: ['appointments', 'schedule', 'booking'], wing: 'doctor' as UserWing }] : []),
        ...(has('doctor', 'admin') ? [{ to: '/intelligence', icon: BrainCircuit, label: String(t.medicalIntelligence || 'AI Intelligence'), description: String(t.aiSupport || 'AI Support'), keywords: ['ai', 'intelligence', 'insights'], wing: 'doctor' as UserWing }] : []),
        ...(has('citizen') ? [{ to: '/citizen/history', icon: History, label: String(t.medicalHistory || 'Medical History'), description: String(t.records || 'Records'), keywords: ['history', 'records', 'past'], wing: 'citizen' as UserWing }] : []),
      ].filter(Boolean) as NavItem[],
    },
    {
      id: 'lab',
      icon: 'Microscope',
      label: String(t.labOperations || 'Lab Operations'),
      roles: ['master_admin', 'admin', 'lab_admin', 'technician', 'pathologist'],
      items: [
        { to: '/lab/dashboard', icon: LayoutDashboard, label: String(t.dashboard || 'Dashboard'), description: String(t.limsOverview || 'LIMS Overview'), keywords: ['lab', 'dashboard', 'lims'], wing: 'lab' },
        { to: '/lab/queue', icon: TestTube, label: String(t.workQueue || 'Work Queue'), description: String(t.processing || 'Processing'), keywords: ['queue', 'samples', 'tests'], wing: 'lab' },
        { to: '/lab/samples', icon: Box, label: String(t.sampleTracking || 'Samples'), description: String(t.tracking || 'Tracking'), keywords: ['samples', 'specimens', 'tracking'], wing: 'lab' },
        { to: '/lab/devices', icon: Server, label: String(t.deviceManagement || 'Devices'), description: String(t.connectivity || 'Connectivity'), keywords: ['devices', 'analyzers', 'instruments'], wing: 'lab' },
        { to: '/lab/inventory', icon: Box, label: String(t.inventory || 'Inventory'), description: String(t.supplies || 'Supplies'), keywords: ['inventory', 'stock', 'reagents'], wing: 'lab' },
        { to: '/lab/qc', icon: ShieldCheck, label: String(t.qualityControl || 'Quality Control'), description: String(t.standardization || 'Standardization'), keywords: ['qc', 'quality', 'control'], wing: 'lab' },
        { to: '/lab/imaging', icon: Image, label: String(t.imagingLab || 'Imaging Lab'), description: String(t.diagnostics || 'Diagnostics'), keywords: ['imaging', 'radiology', 'scan'], wing: 'lab' },
      ],
    },
    {
      id: 'health',
      icon: 'Heart',
      label: String(t.myHealth || 'My Health'),
      roles: ['citizen'],
      items: [
        { to: '/citizen/dashboard', icon: LayoutDashboard, label: String(t.dashboard || 'Dashboard'), description: String(t.healthOS || 'Health OS'), keywords: ['health', 'dashboard', 'overview'], wing: 'citizen' },
        { to: '/citizen/profile', icon: Activity, label: String(t.healthTrends || 'Health Trends'), description: String(t.vitals || 'Vitals'), keywords: ['trends', 'vitals', 'health'], wing: 'citizen' },
        { to: '/citizen/results', icon: FlaskConical, label: String(t.labResults || 'Lab Results'), description: String(t.interpretation || 'Interpretation'), keywords: ['results', 'lab', 'tests'], wing: 'citizen' },
        { to: '/citizen/medications', icon: Pill, label: String(t.medications || 'Medications'), description: String(t.medicineCabinet || 'Medicine Cabinet'), keywords: ['medications', 'drugs', 'prescriptions'], wing: 'citizen' },
        { to: '/citizen/assistant', icon: BrainCircuit, label: String(t.aiAssistant || 'AI Assistant'), description: String(t.healthCoach || 'Health Coach'), keywords: ['ai', 'assistant', 'help'], wing: 'citizen' },
        { to: '/citizen/consent', icon: Shield, label: String(t.consentManagement || 'Consent'), description: String(t.privacy || 'Privacy'), keywords: ['consent', 'privacy', 'sharing'], wing: 'citizen' },
        { to: '/citizen/verification', icon: ShieldCheck, label: String(t.identityVerification || 'Verification'), description: String(t.identity || 'Identity'), keywords: ['verify', 'identity', 'biometric'], wing: 'citizen' },
      ],
    },
    {
      id: 'ministry',
      icon: 'Building2',
      label: String(t.ministry || 'Ministry'),
      roles: ['master_admin', 'ministry_admin', 'ministry_analyst', 'ministry_inspector', 'admin'],
      items: [
        { to: '/ministry/dashboard', icon: Globe, label: String(t.populationHealth || 'Population Health'), description: String(t.nationalOverview || 'National Overview'), keywords: ['population', 'national', 'health'], wing: 'ministry' },
        { to: '/ministry/epidemiology', icon: Activity, label: String(t.epidemiology || 'Epidemiology'), description: String(t.surveillance || 'Surveillance'), keywords: ['epidemiology', 'outbreak', 'disease'], wing: 'ministry' },
        { to: '/ministry/analytics', icon: BarChart3, label: String(t.analytics || 'Analytics'), description: String(t.research || 'Research'), keywords: ['analytics', 'research', 'data'], wing: 'ministry' },
        { to: '/ministry/audit', icon: Shield, label: String(t.dataSovereignty || 'Data Sovereignty'), description: String(t.compliance || 'Compliance'), keywords: ['audit', 'sovereignty', 'compliance'], wing: 'ministry' },
      ],
    },
    {
      id: 'admin',
      icon: 'Shield',
      label: String(t.administration || 'Administration'),
      roles: ['master_admin', 'admin', 'integration_service'],
      items: [
        { to: '/admin/infrastructure', icon: Server, label: String(t.infrastructure || 'Infrastructure'), description: String(t.clusterHealth || 'Cluster Health'), keywords: ['infrastructure', 'cluster', 'servers'], wing: 'admin' },
        { to: '/admin/integrations', icon: Globe, label: String(t.integrations || 'Integrations'), description: String(t.connectedApis || 'Connected APIs'), keywords: ['integrations', 'api', 'connections'], wing: 'admin' },
        { to: '/admin/audit', icon: History, label: String(t.auditLogs || 'Audit Logs'), description: String(t.compliance || 'Compliance'), keywords: ['audit', 'logs', 'compliance'], wing: 'admin' },
        { to: '/settings', icon: Settings, label: String(t.settings || 'Settings'), description: String(t.preferences || 'Preferences'), keywords: ['settings', 'preferences', 'config'], wing: 'admin' },
      ],
    },
    {
      id: 'system',
      icon: 'Code2',
      label: String(t.system || 'System'),
      roles: ['master_admin'],
      items: [
        { to: '/admin/architecture', icon: Code2, label: String(t.architecture || 'Architecture'), description: String(t.systemOverview || 'System Overview'), keywords: ['architecture', 'system', 'overview'], wing: 'system' },
        { to: '/research/analytics', icon: BarChart3, label: String(t.research || 'Research'), description: String(t.analytics || 'Analytics'), keywords: ['research', 'analytics'], wing: 'researcher' },
      ],
    },
    {
      id: 'shortcuts',
      icon: 'Zap',
      label: 'Quick Access',
      roles: [],
      items: [
        { to: '/settings', icon: Settings, label: String(t.settings || 'Settings'), keywords: ['settings'], wing: 'admin' },
      ],
    },
  ];
  return groups.filter(g => {
    if (!g.roles || g.roles.length === 0) return true;
    return g.roles.includes(role);
  });
}
function QuickSearch({ expanded, searchQuery, setSearchQuery, results, onNavigate, onClear, t }: {
  expanded: boolean;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  results: NavItem[];
  onNavigate: (to: string) => void;
  onClear: () => void;
  t: any;
}) {
  if (!expanded) return null;
  return (
    <div className="px-3 pt-3">
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={String(t.searchNav || 'Search menu...')}
          className="w-full pl-9 pr-8 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 transition-all outline-none placeholder:text-slate-400"
        />
        {searchQuery && (
          <button onClick={onClear} className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-slate-400 hover:text-slate-600">
            <X size={12} />
          </button>
        )}
      </div>
      <AnimatePresence>
        {searchQuery && results.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden pt-2"
          >
            <div className="space-y-0.5 bg-indigo-50 rounded-xl p-1.5 border border-indigo-100">
              {results.slice(0, 6).map(item => {
                const IconComp = item.icon;
                return (
                  <button
                    key={item.to}
                    onClick={() => onNavigate(item.to)}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-slate-700 hover:bg-white hover:text-indigo-600 transition-all"
                  >
                    <IconComp size={14} className="text-slate-400" />
                    <span>{item.label}</span>
                    {item.description && (
                      <span className="text-[9px] text-slate-400 ml-auto">{item.description}</span>
                    )}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
export const Sidebar = memo(function Sidebar() {
  const { t, dir } = useLanguage();
  const { profile } = useAuth();
  const { unreadCount } = useNotifications();
  const { state, dispatch, isPinned, getAdaptiveOrder } = useNavigationStore();
  const navigate = useNavigate();
  const location = useLocation();
  const isRtl = dir === 'rtl';
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const [_dragPath, setDragPath] = useState<string | null>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const role = (profile?.role || 'citizen') as UserRole;
  const navGroups = useMemo(() => buildNavGroups(t, role), [t, role]);
  const isCollapsed = state.isCollapsed;
  const expanded = isCollapsed ? isHovering : true;
  const searchQuery = state.searchQuery;
  useEffect(() => {
    window.dispatchEvent(new CustomEvent('sidebar-expanded', { detail: expanded }));
  }, [expanded]);
  useEffect(() => {
    if (navGroups.length > 0 && !state.expandedGroups[navGroups[0]!.id]) {
      dispatch({ type: 'TOGGLE_GROUP', payload: navGroups[0]!.id });
    }
  }, [navGroups]);
  useEffect(() => {
    dispatch({ type: 'TRACK_VISIT', payload: location.pathname });
  }, [location.pathname]);
  const allItems = useMemo(() => navGroups.flatMap(g => g.items), [navGroups]);
  const pinnedItems = useMemo(
    () => allItems.filter(i => state.pinned.includes(i.to)),
    [allItems, state.pinned]
  );
  const recentItems = useMemo(
    () => state.recent.map(p => allItems.find(i => i.to === p)).filter(Boolean) as NavItem[],
    [state.recent, allItems]
  );
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase();
    return allItems.filter(i =>
      i.label.toLowerCase().includes(q) ||
      (i.description && i.description.toLowerCase().includes(q)) ||
      (i.keywords && i.keywords.some(k => k.toLowerCase().includes(q)))
    ).slice(0, 8);
  }, [searchQuery, allItems]);
  const handleNavClick = useCallback((to: string) => {
    navigate(to);
    setIsMobileOpen(false);
  }, [navigate]);
  const handleLogout = useCallback(async () => {
    await signOut(auth);
    navigate('/');
  }, [navigate]);
  const toggleGroup = useCallback((id: string) => {
    dispatch({ type: 'TOGGLE_GROUP', payload: id });
  }, [dispatch]);
  const navLinkClass = ({ isActive }: { isActive: boolean }) => cn(
    'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative',
    isActive
      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
      : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
  );
  const renderNavItem = (item: NavItem, _index: number) => {
    const IconComp = item.icon;
    const isItemPinned = isPinned(item.to);
    return (
      <NavLink
        key={item.to}
        to={item.to}
        onClick={() => handleNavClick(item.to)}
        className={navLinkClass}
        draggable
        onDragStart={() => setDragPath(item.to)}
        onDragEnd={() => setDragPath(null)}
      >
        {({ isActive }) => (
          <>
            <div className="relative shrink-0">
              <IconComp size={expanded ? 18 : 20} className={cn(isActive ? 'text-white' : 'text-slate-400 group-hover:text-indigo-600')} />
              {item.badge && item.badge > 0 && (
                <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-red-500 border-2 border-white rounded-full text-[7px] font-black text-white flex items-center justify-center">
                  {item.badge > 9 ? '9+' : item.badge}
                </span>
              )}
            </div>
            {expanded && (
              <>
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="text-sm font-bold truncate">{item.label}</span>
                  {item.description && (
                    <span className={cn('text-[9px] font-bold uppercase tracking-wider truncate', isActive ? 'text-indigo-200' : 'text-slate-400')}>
                      {item.description}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-0.5 shrink-0">
                  <button
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); dispatch({ type: 'TOGGLE_PINNED', payload: item.to }); }}
                    className={cn('p-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/10', isItemPinned && 'opacity-100')}
                  >
                    <Pin size={12} className={isItemPinned ? 'fill-current text-amber-400' : ''} />
                  </button>
                  <button
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); dispatch({ type: 'TOGGLE_FAVORITE', payload: item.to }); }}
                    className={cn('p-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/10 hidden md:block', state.favorites.includes(item.to) && 'opacity-100')}
                  >
                    <Star size={12} className={state.favorites.includes(item.to) ? 'fill-current text-amber-400' : ''} />
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </NavLink>
    );
  };
  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo + collapse toggle */}
      <div className={cn('flex items-center px-4 h-16 border-b border-slate-100', expanded ? 'justify-between' : 'justify-center')}>
        {expanded ? (
          <>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">
                <span className="text-sm font-black text-white font-headline">G</span>
              </div>
              <div className="flex flex-col">
                <span className="text-base font-black text-slate-900 uppercase tracking-tighter leading-none font-headline">{t.appName || 'GULA'}</span>
                <span className="text-[8px] font-black uppercase tracking-widest text-indigo-600 opacity-70">{t.medicalIntelligence || 'MEDICAL'}</span>
              </div>
            </div>
            <button
              onClick={() => dispatch({ type: 'SET_COLLAPSED', payload: true })}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all"
            >
              <ChevronLeft size={16} className={isRtl ? 'rotate-180' : ''} />
            </button>
          </>
        ) : (
          <button
            onClick={() => { dispatch({ type: 'SET_COLLAPSED', payload: false }); setIsHovering(false); }}
            className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200 hover:scale-105 transition-transform"
          >
            <span className="text-sm font-black text-white font-headline">G</span>
          </button>
        )}
      </div>
      {/* Intelligent Search */}
      <QuickSearch
        expanded={expanded}
        searchQuery={searchQuery}
        setSearchQuery={(q) => dispatch({ type: 'SET_SEARCH', payload: q })}
        results={searchResults}
        onNavigate={handleNavClick}
        onClear={() => dispatch({ type: 'SET_SEARCH', payload: '' })}
        t={t}
      />
      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-1 custom-scrollbar">
        {/* Pinned items section */}
        {expanded && pinnedItems.length > 0 && (
          <div className="mb-3">
            <div className="flex items-center gap-1.5 px-3 py-1.5">
              <Pin size={10} className="text-amber-500" />
              <span className="text-[9px] font-black uppercase tracking-widest text-amber-600">{t.pinned || 'Pinned'}</span>
            </div>
            <div className="space-y-0.5">
              {pinnedItems.map(item => renderNavItem(item, 0))}
            </div>
            <div className="border-t border-slate-100 my-3" />
          </div>
        )}
        {/* Recent items */}
        {expanded && recentItems.length > 0 && pinnedItems.length === 0 && (
          <div className="mb-3">
            <div className="flex items-center gap-1.5 px-3 py-1.5">
              <History size={10} className="text-slate-400" />
              <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">{t.recent || 'Recent'}</span>
            </div>
            <div className="space-y-0.5">
              {recentItems.slice(0, 3).map(item => renderNavItem(item, 0))}
            </div>
            <div className="border-t border-slate-100 my-3" />
          </div>
        )}
        {/* Nav groups with adaptive ordering */}
        {navGroups.map((group) => {
          const ordered = expanded ? getAdaptiveOrder(group.items) : group.items;
          const IconComp = resolveIcon(group.icon);
          return (
            <div key={group.id}>
              {expanded ? (
                <>
                  <button
                    onClick={() => toggleGroup(group.id)}
                    className={cn(
                      'w-full flex items-center justify-between px-3 py-2 rounded-lg transition-all',
                      state.expandedGroups[group.id] ? 'text-indigo-700 bg-indigo-50/50' : 'text-slate-500 hover:bg-slate-50'
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <IconComp size={16} className="shrink-0" />
                      <span className="text-[10px] font-black uppercase tracking-widest">{group.label}</span>
                    </div>
                    {state.expandedGroups[group.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                  <AnimatePresence>
                    {state.expandedGroups[group.id] && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden space-y-0.5 pl-2 mt-0.5"
                      >
                        {ordered.map((item, i) => renderNavItem(item as NavItem, i))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </>
              ) : (
                <Tooltip content={group.label} side={isRtl ? 'left' : 'right'}>
                  <div className="flex justify-center py-2">
                    <button
                      onClick={() => { toggleGroup(group.id); if (group.items[0]) handleNavClick(group.items[0].to); }}
                      className={cn(
                        'relative p-2 rounded-xl transition-all',
                        group.items.some(i => location.pathname === i.to) ? 'bg-indigo-100 text-indigo-600' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600'
                      )}
                    >
                      <IconComp size={20} />
                      {group.id === 'lab' && unreadCount > 0 && (
                        <span className="absolute -top-1 -right-1 inline-flex items-center justify-center min-w-[14px] h-[14px] px-1 rounded-full text-[7px] font-black leading-none bg-red-100 text-red-700">{unreadCount > 9 ? '9+' : unreadCount}</span>
                      )}
                    </button>
                  </div>
                </Tooltip>
              )}
            </div>
          );
        })}
      </nav>
      {/* Quick actions footer */}
      {expanded && (
        <div className="px-3 pb-2 space-y-1">
          <button
            onClick={() => window.dispatchEvent(new CustomEvent('open-command-palette'))}
            className="w-full flex items-center gap-3 px-3 py-2.5 bg-slate-50 hover:bg-indigo-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-500 hover:text-indigo-600 transition-all"
          >
            <Command size={14} />
            <span>{t.commandPalette || 'Command Palette'}</span>
            <Kbd className="ml-auto">⌘K</Kbd>
          </button>
        </div>
      )}
      {/* User profile footer */}
      <div className={cn('border-t border-slate-100 p-3', expanded ? 'block' : 'flex justify-center')}>
        <div className={cn('flex items-center gap-3', !expanded && 'flex-col')}>
          <Avatar
            name={profile?.name || 'User'}
            size={expanded ? 'md' : 'sm'}
            status={navigator.onLine ? 'online' : 'offline'}
          />
          {expanded && (
            <>
              <div className="flex flex-col min-w-0 flex-1">
                <span className="text-sm font-bold text-slate-900 truncate">{profile?.name || 'User'}</span>
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider truncate">{profile?.role || ''}</span>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                title={String(t.signOut || 'Sign Out')}
              >
                <LogOut size={16} />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setIsMobileOpen(true)}
        className="lg:hidden fixed z-50 top-4 left-4 p-2.5 bg-white shadow-lg rounded-xl border border-slate-100"
      >
        <Menu size={20} className="text-slate-600" />
      </button>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsMobileOpen(false)}
            className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm lg:hidden"
          />
        )}
      </AnimatePresence>
      {/* Sidebar */}
      <aside
        ref={sidebarRef}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => { setIsHovering(false); dispatch({ type: 'SET_SEARCH', payload: '' }); }}
        className={cn(
          'fixed inset-y-0 z-50 flex flex-col bg-white border-slate-200 shadow-2xl transition-all duration-300 ease-out',
          isRtl ? 'right-0 border-l' : 'left-0 border-r',
          expanded ? 'w-64' : 'w-16',
          isMobileOpen ? 'translate-x-0' : (isRtl ? 'translate-x-full' : '-translate-x-full'),
          'lg:translate-x-0'
        )}
      >
        {sidebarContent}
      </aside>
      {/* Collapsed hover trigger zone */}
      {isCollapsed && !isHovering && (
        <div
          onMouseEnter={() => setIsHovering(true)}
          className={cn(
            'fixed inset-y-0 z-40 w-4 cursor-pointer',
            isRtl ? 'right-0' : 'left-0'
          )}
        />
      )}
    </>
  );
});