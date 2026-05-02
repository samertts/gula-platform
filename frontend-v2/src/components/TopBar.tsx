import { Search, Globe, Bell, LogOut, Activity, Cpu, Zap, User, Network, Wifi, WifiOff, X, ShieldAlert, FlaskConical, Stethoscope } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useNotifications } from '../contexts/NotificationContext';
import { NotificationCenter } from './NotificationCenter';
import { Language } from '../translations';
import { cn } from '../lib/utils';
import { auth } from '../firebase';
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'motion/react';
import { NeuralSparkline } from './NeuralSparkline';
import { SystemDiagnosticsDrawer } from './SystemDiagnosticsDrawer';
import { toast } from 'sonner';

export function TopBar() {
  const { t, setLanguage, language, dir } = useLanguage();
  const { unreadCount } = useNotifications();
  const { user, profile, logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showMobileSearch, setShowMobileSearch] = useState(false);
  const [throughput, setThroughput] = useState(42.8);
  const [isLowBandwidth, setIsLowBandwidth] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [clinicalMode, setClinicalMode] = useState<'clinic' | 'emergency' | 'research'>('clinic');
  const isRtl = dir === 'rtl';

  useEffect(() => {
    const timer = setInterval(() => {
      setThroughput(prev => Math.max(30, Math.min(60, prev + (Math.random() * 2 - 1))));
    }, 4000);

    const savedLowBandwidth = localStorage.getItem('gula_low_bandwidth') === 'true';
    setIsLowBandwidth(savedLowBandwidth);

    const savedMode = localStorage.getItem('clinical_mode') as any;
    if (savedMode) setClinicalMode(savedMode);

    return () => clearInterval(timer);
  }, []);

  const toggleMode = (mode: 'clinic' | 'emergency' | 'research') => {
    setClinicalMode(mode);
    localStorage.setItem('clinical_mode', mode);
    toast.info(`Clinical Mode Switched to ${mode.toUpperCase()}`);
  };

  const toggleLowBandwidth = () => {
    const newValue = !isLowBandwidth;
    setIsLowBandwidth(newValue);
    localStorage.setItem('gula_low_bandwidth', String(newValue));
    // Trigger global refresh or event if needed
  };

  const handleSignOut = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("Sign out error:", error);
    }
  };

  const langs: Language[] = ['EN', 'AR', 'KU', 'TR', 'SY'];

  return (
    <div className="sticky top-0 z-40">
      <SystemDiagnosticsDrawer 
        isOpen={showDiagnostics} 
        onClose={() => setShowDiagnostics(false)} 
      />
      <div className="bg-slate-950 text-white py-1.5 px-6 flex items-center justify-between gap-4 overflow-hidden relative border-b border-white/5">
         <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),transparent_70%)]" />
         <motion.div 
           animate={{ x: ['-100%', '100%'] }}
           transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
           className="absolute top-0 bottom-0 w-1/3 bg-gradient-to-r from-transparent via-indigo-500/10 to-transparent opacity-30"
         />
         
         <div className="flex items-center gap-3 relative z-10 px-2 lg:px-4">
            <div className="flex items-center gap-1.5">
               <div className={cn("w-1 h-3 rounded-full transition-colors duration-500", isLowBandwidth ? "bg-amber-500" : "bg-indigo-500")} />
               <div className={cn("w-1 h-2 rounded-full transition-colors duration-500 opacity-50", isLowBandwidth ? "bg-amber-400" : "bg-indigo-400")} />
               <div className={cn("w-1 h-1 rounded-full transition-colors duration-500 opacity-30", isLowBandwidth ? "bg-amber-300" : "bg-indigo-300")} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-[0.25em] text-white/70 whitespace-nowrap hidden sm:inline">
               {isLowBandwidth ? "Optimization Mode: ACTIVE" : "Grid Core: OPERATIONAL"}
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.25em] text-white/70 whitespace-nowrap sm:hidden">
               {isLowBandwidth ? "OPT_MODE" : "GRID_SYNC"}
            </span>

            <button 
              onClick={() => setShowDiagnostics(true)}
              className="ml-auto hidden lg:flex items-center gap-2 group hover:text-indigo-400 transition-colors"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[9px] font-black uppercase tracking-widest text-white/40 group-hover:text-indigo-400">System Pulsar: NOMINAL</span>
            </button>
         </div>
         
         <div className="hidden xl:flex items-center gap-8 relative z-10">
            <div className="flex items-center gap-4">
               <div className="flex flex-col items-end">
                  <span className="text-[8px] font-black text-indigo-400 uppercase tracking-widest leading-none mb-1">Signal</span>
                  <NeuralSparkline />
               </div>
               <div className="w-px h-6 bg-white/10" />
               <div className="flex flex-col items-end">
                  <span className="text-[8px] font-black text-emerald-400 uppercase tracking-widest leading-none">Throughput</span>
                  <span className="text-[10px] font-mono font-bold text-white/80">{throughput.toFixed(1)} GB/s</span>
               </div>
            </div>
         </div>
 
         <div className="flex items-center gap-3 relative z-10">
            <button 
              onClick={toggleLowBandwidth}
              className={cn(
                "flex items-center gap-2 px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all border",
                isLowBandwidth 
                  ? "bg-amber-500/10 border-amber-500/20 text-amber-500" 
                  : "bg-white/5 border-white/10 text-white/40 hover:text-white hover:bg-white/10"
              )}
            >
              {isLowBandwidth ? <WifiOff size={12} /> : <Wifi size={12} />}
              <span className="hidden md:inline">{isLowBandwidth ? "Lite Mode" : "Turbo Link"}</span>
            </button>
 
            <div className="h-4 w-px bg-white/10 hidden sm:block" />
 
            <div className="flex items-center gap-1.5 px-2 py-0.5 bg-white/5 rounded-md border border-white/10 hidden sm:flex">
               <Activity size={10} className="text-emerald-400" />
               <span className="text-[8px] font-black text-emerald-400 animate-pulse">ENCRYPTED</span>
            </div>
         </div>
      </div>
      <header className="w-full bg-white/90 backdrop-blur-xl border-b border-slate-100 h-16 flex items-center shadow-sm">
      <div className="flex justify-between items-center px-4 md:px-8 w-full max-w-[1600px] mx-auto gap-4">
         <div className="flex items-center gap-4 md:gap-8 flex-1">
          <div className="flex items-center gap-2 lg:hidden">
             <button 
               onClick={() => setShowMobileSearch(!showMobileSearch)}
               className="p-2.5 bg-slate-50 text-slate-600 rounded-xl hover:bg-slate-100 transition-colors"
             >
               {showMobileSearch ? <X size={20} /> : <Search size={20} />}
             </button>
          </div>
 
          <div className={cn(
            "relative w-full max-w-xl group transition-all duration-300",
            showMobileSearch ? "flex absolute left-0 right-0 px-4 z-50 bg-white h-full items-center" : "hidden md:flex"
          )}>
            <div className={cn(
               "absolute top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-600 transition-all z-10",
               isRtl ? "right-9 md:right-4" : "left-9 md:left-4"
            )}>
               <Search size={18} />
            </div>
            <input 
              type="text" 
              placeholder={t.searchPlaceholder}
              onClick={() => window.dispatchEvent(new CustomEvent('open-command-palette'))}
              readOnly
              className={cn(
                "w-full py-2.5 bg-slate-50/50 border-slate-200 border rounded-2xl text-sm font-medium focus:ring-4 focus:ring-indigo-100 focus:bg-white transition-all placeholder:text-slate-400 cursor-pointer shadow-sm group-hover:border-slate-300",
                isRtl ? "pr-16 md:pr-11" : "pl-16 md:pl-11"
              )}
            />
            <div className={cn(
               "absolute top-1/2 -translate-y-1/2 flex items-center gap-1.5 px-2 py-1 rounded-lg border border-slate-200 bg-white opacity-40 group-hover:opacity-100 transition-opacity pointer-events-none hidden md:flex shadow-sm",
               isRtl ? "left-4" : "right-4"
            )}>
               <span className="text-[10px] font-black text-slate-500">⌘</span>
               <span className="text-[10px] font-black text-slate-500">K</span>
            </div>
          </div>
        </div>
 
        <div className="flex items-center gap-2 sm:gap-6">
          {/* Clinical Mode Switcher */}
          <div className="hidden xl:flex items-center p-1 bg-slate-900 shadow-xl shadow-slate-200 border border-slate-200 rounded-2xl">
             <button 
               onClick={() => toggleMode('clinic')}
               className={cn(
                 "flex items-center gap-2 px-4 py-2 rounded-xl text-[10px] font-black transition-all",
                 clinicalMode === 'clinic' ? "bg-white text-indigo-600 shadow-sm" : "text-white/40 hover:text-white/60"
               )}
             >
                <Stethoscope size={14} />
                <span className="font-headline tracking-tighter">CLINIC</span>
             </button>
             <button 
               onClick={() => toggleMode('emergency')}
               className={cn(
                 "flex items-center gap-2 px-4 py-2 rounded-xl text-[10px] font-black transition-all",
                 clinicalMode === 'emergency' ? "bg-rose-600 text-white shadow-lg shadow-rose-200" : "text-white/40 hover:text-rose-400"
               )}
             >
                <ShieldAlert size={14} />
                <span className="font-headline tracking-tighter">STAT_EMR</span>
             </button>
             <button 
               onClick={() => toggleMode('research')}
               className={cn(
                 "flex items-center gap-2 px-4 py-2 rounded-xl text-[10px] font-black transition-all",
                 clinicalMode === 'research' ? "bg-amber-500 text-white shadow-lg shadow-amber-200" : "text-white/40 hover:text-amber-400"
               )}
             >
                <FlaskConical size={14} />
                <span className="font-headline tracking-tighter">RESEARCH</span>
             </button>
          </div>

          <div className="flex items-center p-1 bg-slate-100/50 border border-slate-200 rounded-2xl">
            {langs.map((l) => (
              <button
                key={l}
                onClick={() => setLanguage(l)}
                className={cn(
                  "px-2 sm:px-3 py-1.5 rounded-xl text-[10px] sm:text-[11px] font-black transition-all relative overflow-hidden",
                  language === l 
                    ? "bg-white text-indigo-600 shadow-sm ring-1 ring-black/5" 
                    : "text-slate-400 hover:text-slate-600 hover:bg-white/50"
                )}
              >
                <span className="relative z-10">{l}</span>
              </button>
            ))}
          </div>
 
          <div className="h-6 w-px bg-slate-200 hidden md:block" />
 
          <div className="hidden lg:flex items-center gap-4 group cursor-pointer p-1.5 hover:bg-slate-50 rounded-2xl transition-all">
             <div className={cn("flex flex-col", isRtl ? "items-start text-left" : "items-end text-right")}>
                <p className="text-sm font-black text-slate-900 leading-none mb-0.5 group-hover:text-indigo-600 transition-colors">
                  {profile?.displayName || user?.displayName || user?.email?.split('@')[0] || t.clinicalLead}
                </p>
                <div className="flex items-center gap-1.5">
                   <div className="relative">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      <div className="absolute inset-0 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping opacity-75" />
                   </div>
                   <p className="text-[9px] font-black text-slate-400 uppercase tracking-[0.1em] leading-none group-hover:text-indigo-500 transition-colors">
                     {profile?.role === 'master_admin' ? 'System Master' : profile?.role || t.activeSession}
                   </p>
                </div>
             </div>
             <div className="relative">
                <div className="w-11 h-11 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-100 group-hover:scale-105 transition-transform overflow-hidden relative">
                   <div className="absolute inset-0 bg-gradient-to-tr from-white/20 to-transparent" />
                   <User size={22} className="relative z-10" />
                </div>
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-white rounded-lg shadow-sm" />
             </div>
          </div>
 
          <div className="flex items-center gap-1.5">
            <div className="relative">
               <button 
                 onClick={() => setShowNotifications(!showNotifications)}
                 className="p-3 text-slate-500 hover:bg-slate-50 hover:text-indigo-600 rounded-2xl transition-all relative border border-transparent hover:border-slate-100"
               >
                 <Bell size={20} />
                 {unreadCount > 0 && (
                   <span className={cn(
                      "absolute top-2.5 w-4.5 h-4.5 bg-red-500 border-2 border-white rounded-lg text-[8px] font-black text-white flex items-center justify-center shadow-sm",
                      isRtl ? "left-2.5" : "right-2.5"
                   )}>
                     {unreadCount > 9 ? '9+' : unreadCount}
                   </span>
                 )}
               </button>
               <NotificationCenter 
                 isOpen={showNotifications} 
                 onClose={() => setShowNotifications(false)} 
               />
            </div>
 
            <button 
              onClick={handleSignOut}
              className="p-3 text-slate-400 hover:bg-red-50 hover:text-red-600 rounded-2xl transition-all"
              title={t.signOut}
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </div>
    </header>
    </div>
  );
}
