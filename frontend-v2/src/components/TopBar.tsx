import { Search, Bell, User, Globe, LogOut, Zap, Plus, Clock, Activity, Wifi, WifiOff, ChevronDown, Sun, Moon, Settings, LayoutDashboard, History, Star, X, Command, Sparkles, Shield, Building2, CheckCheck, ListTodo, ArrowLeftRight, RefreshCw, AlertTriangle } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useNotifications } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
import { NotificationCenter } from './NotificationCenter';
import { Language } from '../translations';
import { cn } from '../lib/utils';
import { useState, useEffect, memo, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Badge, Avatar, Kbd, Tooltip, Button } from './ui';

interface QuickAction {
  id: string;
  label: string;
  icon: any;
  action: () => void;
  shortcut?: string;
  description?: string;
}

const LANGUAGES: Language[] = ['EN', 'AR', 'KU', 'TR', 'SY'];
const LANG_NAMES: Record<Language, string> = {
  EN: 'English', AR: 'العربية', KU: 'Kurdî', TR: 'Türkçe', SY: 'ܣܘܪܝܬ'
};

const QUICK_ACTIONS: QuickAction[] = [
  { id: 'new-patient', label: 'Register Patient', icon: User, description: 'New patient record', action: () => {} },
  { id: 'new-order', label: 'New Order', icon: Plus, description: 'Create lab order', action: () => {} },
  { id: 'new-appointment', label: 'Appointment', icon: Clock, description: 'Schedule visit', action: () => {} },
  { id: 'new-result', label: 'Enter Result', icon: Activity, description: 'Record test results', action: () => {} },
];

export const TopBar = memo(function TopBar() {
  const { t, setLanguage, language, dir } = useLanguage();
  const { unreadCount, notifications } = useNotifications();
  const { profile, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isRtl = dir === 'rtl';

  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showQuickCreate, setShowQuickCreate] = useState(false);
  const [showLang, setShowLang] = useState(false);
  const [showTasks, setShowTasks] = useState(false);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [showEmergency, setShowEmergency] = useState(false);
  const [showOrgSwitcher, setShowOrgSwitcher] = useState(false);

  const profileRef = useRef<HTMLDivElement>(null);
  const langRef = useRef<HTMLDivElement>(null);
  const quickCreateRef = useRef<HTMLDivElement>(null);
  const tasksRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => { window.removeEventListener('online', handleOnline); window.removeEventListener('offline', handleOffline); };
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setShowProfile(false);
      if (langRef.current && !langRef.current.contains(e.target as Node)) setShowLang(false);
      if (quickCreateRef.current && !quickCreateRef.current.contains(e.target as Node)) setShowQuickCreate(false);
      if (tasksRef.current && !tasksRef.current.contains(e.target as Node)) setShowTasks(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  QUICK_ACTIONS[0].action = () => { navigate('/citizen/register'); setShowQuickCreate(false); };
  QUICK_ACTIONS[1].action = () => { navigate('/lab/queue'); setShowQuickCreate(false); };
  QUICK_ACTIONS[2].action = () => { navigate('/appointments'); setShowQuickCreate(false); };
  QUICK_ACTIONS[3].action = () => { navigate('/lab/queue'); setShowQuickCreate(false); };

  const getPageTitle = useCallback(() => {
    const path = location.pathname;
    if (path === '/') return t.home || 'Home';
    if (path.startsWith('/patients')) return t.patients || 'Patients';
    if (path.startsWith('/appointments')) return t.appointments || 'Appointments';
    if (path.startsWith('/intelligence')) return t.medicalIntelligence || 'AI Intelligence';
    if (path.startsWith('/lab/dashboard')) return (t as any).labDashboard || 'Lab Dashboard';
    if (path.startsWith('/lab/queue')) return t.workQueue || 'Work Queue';
    if (path.startsWith('/lab/samples')) return t.sampleTracking || 'Samples';
    if (path.startsWith('/lab/devices')) return t.deviceManagement || 'Devices';
    if (path.startsWith('/lab/inventory')) return t.inventory || 'Inventory';
    if (path.startsWith('/lab/qc')) return t.qualityControl || 'Quality Control';
    if (path.startsWith('/lab/imaging')) return t.imagingLab || 'Imaging Lab';
    if (path.startsWith('/citizen/dashboard')) return t.dashboard || 'Dashboard';
    if (path.startsWith('/citizen/profile')) return t.myHealth || 'My Health';
    if (path.startsWith('/citizen/results')) return t.labResults || 'Lab Results';
    if (path.startsWith('/citizen/medications')) return (t as any).medications || 'Medications';
    if (path.startsWith('/citizen/assistant')) return t.aiAssistant || 'AI Assistant';
    if (path.startsWith('/citizen/family')) return t.familyManagement || 'Family';
    if (path.startsWith('/citizen/history')) return t.medicalHistory || 'History';
    if (path.startsWith('/citizen/consent')) return t.consentManagement || 'Consent';
    if (path.startsWith('/citizen/verification')) return (t as any).identityVerification || 'Verification';
    if (path.startsWith('/citizen/register')) return t.registerPatient || 'Register';
    if (path.startsWith('/ministry/dashboard')) return t.populationHealth || 'Population Health';
    if (path.startsWith('/ministry/epidemiology')) return (t as any).epidemiology || 'Epidemiology';
    if (path.startsWith('/ministry/analytics')) return t.analytics || 'Analytics';
    if (path.startsWith('/ministry/audit')) return t.dataSovereignty || 'Data Sovereignty';
    if (path.startsWith('/admin/infrastructure')) return t.infrastructure || 'Infrastructure';
    if (path.startsWith('/admin/integrations')) return t.integrations || 'Integrations';
    if (path.startsWith('/admin/audit')) return t.auditLogs || 'Audit Logs';
    if (path.startsWith('/admin/architecture')) return t.architecture || 'Architecture';
    if (path.startsWith('/settings')) return t.settings || 'Settings';
    return '';
  }, [location.pathname, t]);

  const roleBadge = (() => {
    if (!profile?.role) return '';
    const r = profile.role;
    if (r === 'master_admin') return 'SYS_MASTER';
    if (r === 'ministry_admin') return 'MIN_ADMIN';
    if (r === 'ministry_analyst') return 'MIN_ANALYST';
    if (r === 'ministry_inspector') return 'INSPECTOR';
    if (r === 'physician') return 'PHYSICIAN';
    if (r === 'technician') return 'TECH';
    if (r === 'lab_admin') return 'LAB_ADMIN';
    if (r === 'pathologist') return 'PATH';
    if (r === 'researcher') return 'RESEARCH';
    if (r === 'regulator') return 'REGULATOR';
    if (r === 'auditor') return 'AUDITOR';
    if (r === 'integration_service') return 'INTEGRATION';
    if (r === 'admin') return 'ADMIN';
    if (r === 'citizen') return 'CITIZEN';
    return (r as string).toUpperCase();
  })();

  const unreadCritical = notifications.filter(n => !n.read && n.priority === 'stat').length;
  const tasksCount = 3;

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-100 shadow-sm">
      <div className="flex items-center justify-between px-4 md:px-6 h-14 max-w-screen-2xl mx-auto gap-2">
        {/* Left: Page context + breadcrumb */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900 truncate font-headline">{getPageTitle()}</h1>
              <Badge variant="primary" className="hidden sm:inline-flex">{roleBadge}</Badge>
              {isOffline && (
                <Badge variant="warning" dot pulsing>
                  <WifiOff size={10} />
                  <span className="ml-1">OFFLINE</span>
                </Badge>
              )}
              {unreadCritical > 0 && (
                <Badge variant="danger" dot pulsing>
                  <AlertTriangle size={10} />
                  <span className="ml-1">{unreadCritical} CRITICAL</span>
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Center: Universal Search */}
        <div className="hidden md:flex flex-1 max-w-md justify-center">
          <button
            onClick={() => window.dispatchEvent(new CustomEvent('open-command-palette'))}
            className="flex items-center gap-2 w-full max-w-sm px-4 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-400 hover:text-slate-600 hover:border-slate-300 transition-all group"
          >
            <Search size={15} className="shrink-0" />
            <span className="truncate">{t.searchEverything || 'Search patients, orders, help...'}</span>
            <span className="ml-auto hidden sm:flex items-center gap-1">
              <Kbd><Command size={8} />K</Kbd>
            </span>
          </button>
        </div>

        {/* Right: Command Center Actions */}
        <div className="flex items-center gap-1">
          {/* Quick Create */}
          <div className="relative" ref={quickCreateRef}>
            <Tooltip content={t.quickCreate || 'Quick Create'}>
              <button
                onClick={() => setShowQuickCreate(!showQuickCreate)}
                className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
              >
                <Plus size={18} />
              </button>
            </Tooltip>
            <AnimatePresence>
              {showQuickCreate && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.95 }}
                  className={cn('absolute top-full mt-2 w-64 bg-white border border-slate-200 rounded-2xl shadow-2xl p-2 z-50', isRtl ? 'left-0' : 'right-0')}
                >
                  <div className="px-3 py-2 text-[9px] font-black uppercase tracking-widest text-slate-400 border-b border-slate-100 mb-1">
                    {t.quickCreate || 'Quick Create'}
                  </div>
                  {QUICK_ACTIONS.map(qa => (
                    <button
                      key={qa.id}
                      onClick={() => { qa.action(); setShowQuickCreate(false); }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-600 transition-all"
                    >
                      <div className="w-8 h-8 bg-slate-100 rounded-xl flex items-center justify-center shrink-0">
                        <qa.icon size={16} className="text-slate-500" />
                      </div>
                      <div className="flex flex-col items-start">
                        <span className="text-sm font-bold">{t[qa.id.replace('new-', '')] || qa.label}</span>
                        <span className="text-[9px] text-slate-400">{qa.description}</span>
                      </div>
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Language */}
          <div className="relative" ref={langRef}>
            <Tooltip content={t.language || 'Language'}>
              <button
                onClick={() => setShowLang(!showLang)}
                className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
              >
                <Globe size={18} />
              </button>
            </Tooltip>
            <AnimatePresence>
              {showLang && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.95 }}
                  className={cn('absolute top-full mt-2 bg-white border border-slate-200 rounded-2xl shadow-2xl p-2 z-50 min-w-[140px]', isRtl ? 'left-0' : 'right-0')}
                >
                  {LANGUAGES.map(l => (
                    <button
                      key={l}
                      onClick={() => { setLanguage(l); setShowLang(false); }}
                      className={cn('w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all', language === l ? 'bg-indigo-50 text-indigo-600' : 'text-slate-600 hover:bg-slate-50')}
                    >
                      <span className={cn('w-6 h-6 rounded-lg flex items-center justify-center text-[9px] font-black', language === l ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500')}>
                        {l}
                      </span>
                      <span className="flex-1">{LANG_NAMES[l]}</span>
                      {language === l && <CheckAllIcon />}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Tasks / Workflow */}
          <div className="relative" ref={tasksRef}>
            <Tooltip content="Tasks">
              <button
                onClick={() => setShowTasks(!showTasks)}
                className="relative p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
              >
                <ListTodo size={18} />
                {tasksCount > 0 && (
                  <span className="absolute -top-1 -right-1 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1.5 rounded-full text-[9px] font-black leading-none bg-amber-100 text-amber-700">{tasksCount > 9 ? '9+' : tasksCount}</span>
                )}
              </button>
            </Tooltip>
            <AnimatePresence>
              {showTasks && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.95 }}
                  className={cn('absolute top-full mt-2 w-72 bg-white border border-slate-200 rounded-2xl shadow-2xl p-2 z-50', isRtl ? 'left-0' : 'right-0')}
                >
                  <div className="px-3 py-2 flex items-center justify-between border-b border-slate-100 mb-1">
                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Tasks</span>
                    <span className="inline-flex items-center justify-center min-w-[18px] h-[18px] px-1.5 rounded-full text-[9px] font-black leading-none bg-amber-100 text-amber-700">{tasksCount}</span>
                  </div>
                  <div className="space-y-1">
                    {[
                      { label: 'Validate lab results', priority: 'high', time: '2 min ago' },
                      { label: 'Review QC anomalies', priority: 'urgent', time: '5 min ago' },
                      { label: 'Approve pending orders', priority: 'normal', time: '1 hour ago' },
                    ].map((task, i) => (
                      <button key={i} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm hover:bg-slate-50 transition-all text-left">
                        <div className={cn(
                          'w-2 h-2 rounded-full shrink-0',
                          task.priority === 'urgent' ? 'bg-red-500' : task.priority === 'high' ? 'bg-amber-500' : 'bg-slate-300'
                        )} />
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-medium text-slate-700 block truncate">{task.label}</span>
                          <span className="text-[9px] text-slate-400">{task.time}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                  <button className="w-full mt-1 py-2 text-center text-[10px] font-black text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all tracking-widest uppercase">
                    View All Tasks
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Emergency Alerts */}
          <Tooltip content={t.emergencyAlerts || 'Emergency Alerts'}>
            <button
              onClick={() => setShowEmergency(!showEmergency)}
              className={cn('p-2 rounded-xl transition-all', unreadCritical > 0 ? 'bg-red-50 text-red-600 animate-pulse' : 'text-slate-400 hover:text-amber-600 hover:bg-amber-50')}
            >
              <AlertTriangle size={18} />
            </button>
          </Tooltip>

          {/* Notifications */}
          <div className="relative">
            <Tooltip content={t.notifications || 'Notifications'}>
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all"
              >
                <Bell size={18} />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1.5 rounded-full text-[9px] font-black leading-none bg-red-100 text-red-700">{unreadCount > 9 ? '9+' : unreadCount}</span>
                )}
              </button>
            </Tooltip>
            <NotificationCenter isOpen={showNotifications} onClose={() => setShowNotifications(false)} />
          </div>

          {/* Sync status */}
          <Tooltip content={isOffline ? 'Offline - changes queued' : 'All changes synced'}>
            <div className={cn('hidden sm:flex items-center justify-center w-9 h-9 rounded-xl transition-all', isOffline ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600')}>
              {isOffline ? <WifiOff size={16} /> : <Wifi size={16} />}
            </div>
          </Tooltip>

          <div className="h-6 w-px bg-slate-200 mx-0.5" />

          {/* Profile */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setShowProfile(!showProfile)}
              className="flex items-center gap-2 p-1 hover:bg-slate-50 rounded-xl transition-all"
            >
              <Avatar name={profile?.name || 'User'} size="sm" status={isOffline ? 'offline' : 'online'} />
              <div className="hidden lg:flex flex-col items-start">
                <span className="text-sm font-bold text-slate-900 leading-none">{profile?.name || 'User'}</span>
                <span className="text-[9px] font-bold text-slate-400 uppercase">{roleBadge}</span>
              </div>
              <ChevronDown size={14} className="hidden lg:block text-slate-400" />
            </button>
            <AnimatePresence>
              {showProfile && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.95 }}
                  className={cn('absolute top-full mt-2 w-64 bg-white border border-slate-200 rounded-2xl shadow-2xl p-2 z-50', isRtl ? 'left-0' : 'right-0')}
                >
                  <div className="px-3 py-3 flex items-center gap-3 border-b border-slate-100 mb-1">
                    <Avatar name={profile?.name || 'User'} size="lg" />
                    <div className="flex flex-col">
                      <p className="text-sm font-bold text-slate-900">{profile?.name || 'User'}</p>
                      <p className="text-[10px] text-slate-400">{profile?.email || ''}</p>
                      <Badge variant="primary" className="mt-1 self-start">{roleBadge}</Badge>
                    </div>
                  </div>
                  <button
                    onClick={() => { navigate('/settings'); setShowProfile(false); }}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-600 transition-all"
                  >
                    <Settings size={16} />
                    <span>{t.settings || 'Settings'}</span>
                  </button>
                  <button
                    onClick={() => { window.dispatchEvent(new CustomEvent('open-command-palette')); setShowProfile(false); }}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-600 transition-all"
                  >
                    <Command size={16} />
                    <span>{t.commandPalette || 'Command Palette'}</span>
                    <Kbd className="ml-auto">⌘K</Kbd>
                  </button>
                  <div className="border-t border-slate-100 mt-1 pt-1">
                    <button
                      onClick={() => { logout(); setShowProfile(false); }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-600 hover:bg-red-50 transition-all"
                    >
                      <LogOut size={16} />
                      <span>{t.signOut || 'Sign Out'}</span>
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </header>
  );
});

function CheckAllIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-600">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
