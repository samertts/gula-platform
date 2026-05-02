import React, { useState, useEffect } from 'react';
import { 
  Globe, 
  User, 
  Shield, 
  Bell, 
  Languages, 
  Moon, 
  Sun, 
  Fingerprint, 
  Smartphone, 
  History, 
  Database, 
  Cpu, 
  Check, 
  ChevronRight,
  Info,
  LogOut,
  RefreshCw,
  Lock,
  Eye,
  Settings as SettingsIcon,
  Palette,
  Sparkles,
  Microscope,
  AlertCircle
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { Language } from '../translations';
import { cn } from '../lib/utils';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from '../contexts/AuthContext';

type TabId = 'profile' | 'appearance' | 'language' | 'security' | 'ai' | 'compliance' | 'network' | 'system';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ElementType;
}

export function SettingsView() {
  const { t, setLanguage, language } = useLanguage();
  const { user, profile } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>('profile');
  const [searchQuery, setSearchQuery] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [accentColor, setAccentColor] = useState('indigo');
  const [isLoading, setIsLoading] = useState(false);
  
  // AI Settings State
  const [aiConfidence, setAiConfidence] = useState(85);
  const [explainableAi, setExplainableAi] = useState(true);
  
  // System State (Simulated)
  const [cpuLoad, setCpuLoad] = useState(24);
  const [memoryUsage, setMemoryUsage] = useState(12.4);
  
  const [hasChanges, setHasChanges] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  
  const isRtl = language === 'AR' || language === 'KU' || language === 'SY';

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        if (hasChanges) handleSave();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('settings-search')?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hasChanges]);

  // Simulate System Flux
  useEffect(() => {
    const interval = setInterval(() => {
      setCpuLoad(prev => Math.max(5, Math.min(95, prev + (Math.random() * 10 - 5))));
      setMemoryUsage(prev => Math.max(8, Math.min(32, prev + (Math.random() * 2 - 1))));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const tabs: Tab[] = [
    { id: 'profile', label: t.providerProfile, icon: User },
    { id: 'language', label: t.langAndRegion, icon: Languages },
    { id: 'appearance', label: t.appearance, icon: Palette },
    { id: 'ai', label: t.labIntelligence, icon: Sparkles },
    { id: 'security', label: t.security, icon: Shield },
    { id: 'compliance', label: t.compliance, icon: Lock },
    { id: 'network', label: t.connectivity, icon: Globe },
    { id: 'system', label: t.infrastructure, icon: Cpu },
  ];

  const filteredTabs = searchQuery 
    ? tabs.filter(tab => tab.label.toLowerCase().includes(searchQuery.toLowerCase()))
    : tabs;

  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => setIsLoading(false), 400);
    return () => clearTimeout(timer);
  }, [activeTab]);

  const handleSave = () => {
    setSaveStatus('saving');
    setTimeout(() => {
      // Simulate potential error for one of the UX recovery flows
      if (Math.random() > 0.95) {
        setSaveStatus('error');
        return;
      }
      setSaveStatus('saved');
      setHasChanges(false);
      setTimeout(() => setSaveStatus('idle'), 3000);
    }, 1500);
  };

  const langs: { id: Language; name: string; native: string }[] = [
    { id: 'EN', name: 'English', native: 'English' },
    { id: 'AR', name: 'Arabic', native: 'العربية' },
    { id: 'KU', name: 'Kurdish', native: 'کوردي' },
    { id: 'TR', name: 'Turkmen', native: 'Türkmen' },
    { id: 'SY', name: 'Syriac', native: 'ܠܫܢܐ ܣܘܪܝܝܐ' }
  ];

  const renderSkeleton = () => (
    <div className="space-y-6 animate-pulse">
      <div className="h-40 bg-slate-100 rounded-3xl w-full" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-20 bg-slate-50 rounded-xl border border-slate-100" />
        ))}
      </div>
    </div>
  );

  const renderTabContent = () => {
    if (isLoading) return renderSkeleton();

    switch (activeTab) {
      case 'ai':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <div className="p-6 bg-indigo-900 rounded-3xl text-white relative overflow-hidden shadow-2xl shadow-indigo-200">
               <div className="absolute top-0 right-0 p-8 opacity-10">
                 <Sparkles size={120} />
               </div>
               <h4 className="text-xl font-black mb-2">{t.neuralEngine}</h4>
               <p className="text-indigo-200 text-sm max-w-md">{t.neuralEngineDesc}</p>
               
               <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
                 <div className="space-y-4">
                   <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-indigo-300">
                     <span>{t.confidenceThreshold}</span>
                     <span>{aiConfidence}%</span>
                   </div>
                   <div className="relative h-20 flex items-end gap-1 mb-2">
                     {[...Array(20)].map((_, i) => {
                       const height = 20 + Math.sin(i * 0.5 + aiConfidence * 0.1) * 15 + Math.random() * 5;
                       const isActive = (i / 20) * 100 < aiConfidence;
                       return (
                         <div 
                           key={i} 
                           className={cn(
                             "flex-1 rounded-t-sm transition-all duration-500",
                             isActive ? "bg-indigo-400" : "bg-white/10"
                           )} 
                           style={{ height: `${height}%` }}
                         />
                       );
                     })}
                   </div>
                   <input 
                     type="range" 
                     min={50} max={99} 
                     value={aiConfidence}
                     onChange={(e) => { setAiConfidence(Number(e.target.value)); setHasChanges(true); }}
                     className="w-full h-2 bg-white/10 rounded-full appearance-none cursor-pointer accent-white"
                   />
                   <div className="flex justify-between text-[10px] text-indigo-300 font-bold uppercase">
                     <span>High Recall</span>
                     <span>High Precision</span>
                   </div>
                 </div>
                 <div className="flex flex-col justify-center gap-4">
                   <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/10">
                     <div>
                       <div className="text-sm font-bold">{t.explainableAI}</div>
                       <div className="text-[10px] text-indigo-300">{t.showReasoning}</div>
                     </div>
                     <button 
                      onClick={() => { setExplainableAi(!explainableAi); setHasChanges(true); }}
                      className={cn(
                        "w-12 h-6 rounded-full transition-all relative outline-none",
                        explainableAi ? "bg-white shadow-[0_0_15px_rgba(255,255,255,0.5)]" : "bg-white/20"
                      )}
                     >
                       <div className={cn(
                         "absolute top-1 w-4 h-4 rounded-full transition-all duration-300",
                         explainableAi ? (isRtl ? "left-1" : "right-1") : (isRtl ? "right-1" : "left-1"),
                         explainableAi ? "bg-indigo-900" : "bg-white"
                       )} />
                     </button>
                   </div>
                   <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
                      <div className="flex items-center gap-2 text-xs font-bold text-indigo-300 mb-2">
                        <Info size={14} /> {t.shortcutSave}
                      </div>
                      <p className="text-[10px] text-white/40 leading-tight">GULA utilizes Med-Gemini 1.5 for clinical reasoning. High thresholds prioritize clinical certainty.</p>
                   </div>
                 </div>
               </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-xs font-black uppercase tracking-widest text-slate-400">{t.availableModels}</h4>
              {[
                { name: 'Med-Gemini 1.5 Ultra', type: t.clinicalDiagnostics, status: t.optimal },
                { name: 'Pathology-Vision 2.0', type: t.imagingAnalysis, status: t.ready },
                { name: 'Epi-Forecast Prime', type: t.outbreakPrediction, status: t.updating }
              ].map((model, i) => (
                <div key={i} className="p-4 bg-white border border-slate-100 rounded-2xl flex items-center justify-between group hover:border-indigo-200 transition-all cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center text-indigo-500 group-hover:scale-110 transition-transform">
                      <Cpu size={20} />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">{model.name}</div>
                      <div className="text-[10px] text-slate-400 uppercase font-black">{model.type}</div>
                    </div>
                  </div>
                  <span className={cn(
                    "text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded",
                    model.status === t.optimal ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"
                  )}>{model.status}</span>
                </div>
              ))}
            </div>
          </motion.div>
        );
      case 'compliance':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-6 bg-slate-50 rounded-2xl border border-slate-100">
                <Shield size={24} className="text-indigo-600 mb-4" />
                <h4 className="font-bold text-slate-900">{t.dataSovereignty}</h4>
                <p className="text-xs text-slate-500 mt-2">{t.dataSovereigntyDesc}</p>
                <button className="mt-4 text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:underline">{t.changeRegion}</button>
              </div>
              <div className="p-6 bg-slate-50 rounded-2xl border border-slate-100">
                <Lock size={24} className="text-rose-600 mb-4" />
                <h4 className="font-bold text-slate-900">{t.zeroTrustAudit}</h4>
                <p className="text-xs text-slate-500 mt-2">{t.zeroTrustAuditDesc}</p>
                <button className="mt-4 text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:underline">{t.downloadReport}</button>
              </div>
              <div className="p-6 bg-slate-50 rounded-2xl border border-slate-100">
                <Database size={24} className="text-emerald-600 mb-4" />
                <h4 className="font-bold text-slate-900">{t.archivePolicy}</h4>
                <p className="text-xs text-slate-500 mt-2">{t.archivePolicyDesc}</p>
                <button className="mt-4 text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:underline">{t.manageRules}</button>
              </div>
            </div>

            <div className="p-6 bg-white border border-slate-200 rounded-3xl space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-slate-900">{t.consentProtocol}</h4>
                <span className="px-2 py-1 bg-green-100 text-green-700 text-[10px] font-black uppercase rounded">{t.enforced}</span>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between py-3 border-b border-slate-100">
                  <span className="text-sm text-slate-600">{t.dynamicConsentMobile}</span>
                  <div className="w-10 h-5 bg-indigo-600 rounded-full relative"><div className={cn("absolute top-0.5 w-4 h-4 bg-white rounded-full", isRtl ? "left-0.5" : "right-0.5")} /></div>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-slate-100">
                  <span className="text-sm text-slate-600">{t.researcherAnonymization}</span>
                  <div className="w-10 h-5 bg-indigo-600 rounded-full relative"><div className={cn("absolute top-0.5 w-4 h-4 bg-white rounded-full", isRtl ? "left-0.5" : "right-0.5")} /></div>
                </div>
              </div>
            </div>
          </motion.div>
        );
      case 'network':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm">
               <div className="p-6 border-b border-slate-100 bg-slate-50">
                 <div className="flex items-center justify-between">
                   <div className="flex items-center gap-3">
                     <Globe size={20} className="text-indigo-600" />
                     <h4 className="font-bold text-slate-900">{t.regionalNodes}</h4>
                   </div>
                   <div className="flex items-center gap-2">
                     <div className="w-2 h-2 bg-green-500 rounded-full" />
                     <span className="text-[10px] font-black text-green-600 uppercase tracking-widest">{t.globalLinkActive}</span>
                   </div>
                 </div>
               </div>
               <div className="p-6 space-y-4">
                 {[
                   { region: 'Northern Erbil Node', lat: '12.4ms', status: t.healthy },
                   { region: 'Central Baghdad Node', lat: '24.1ms', status: t.degraded },
                   { region: 'Southern Basra Node', lat: '18.9ms', status: t.healthy }
                 ].map((node, i) => (
                   <div key={i} className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100">
                     <div className="flex items-center gap-4">
                       <Database size={18} className="text-slate-400" />
                       <div>
                         <div className="text-sm font-bold text-slate-900">{node.region}</div>
                         <div className="text-[10px] text-slate-400 uppercase font-black">{t.latency}: {node.lat}</div>
                       </div>
                     </div>
                     <span className={cn(
                       "text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded",
                       node.status === t.healthy ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                     )}>{node.status}</span>
                   </div>
                 ))}
               </div>
            </div>

            <div className="p-6 bg-slate-900 rounded-3xl text-white shadow-xl shadow-slate-900/20">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center">
                  <RefreshCw size={24} className="text-indigo-400" />
                </div>
                <div>
                   <h4 className="font-bold">{t.interopBridge}</h4>
                   <p className="text-xs text-white/50">{t.interopBridgeDesc}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
                   <div className="text-[10px] font-black text-white/40 uppercase mb-2">{t.fhirPort}</div>
                   <div className="text-lg font-mono font-bold">8080</div>
                </div>
                <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
                   <div className="text-[10px] font-black text-white/40 uppercase mb-2">{t.tlsEncryption}</div>
                   <div className="text-lg font-bold">v1.3 AES-256</div>
                </div>
              </div>
            </div>
          </motion.div>
        );
      case 'profile':
        return (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="flex flex-col sm:flex-row items-center gap-6 mb-8 text-center sm:text-left">
              <div className="w-24 h-24 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 border-4 border-white shadow-xl relative group overflow-hidden">
                <User size={48} />
                <button className="absolute inset-0 bg-black/40 rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white">
                  <RefreshCw size={24} />
                </button>
              </div>
              <div className={cn(isRtl ? "sm:text-right" : "sm:text-left")}>
                <h3 className="text-2xl font-bold text-slate-900">{profile?.displayName || user?.displayName || t.clinicalPractitioner}</h3>
                <p className="text-slate-500 font-medium">{t.healthcareProfessional}</p>
                <div className="flex flex-wrap justify-center sm:justify-start gap-2 mt-3">
                  <span className="px-3 py-1 bg-green-100 text-green-700 text-[10px] font-black uppercase tracking-widest rounded-full">{t.activeStatus}</span>
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-700 text-[10px] font-black uppercase tracking-widest rounded-full">{t.role}: {profile?.role || t.admin}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">{t.email}</label>
                <div className="text-sm font-bold text-slate-700">{user?.email}</div>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">{t.providerId}</label>
                <div className="text-sm font-bold text-slate-700 font-mono">GULA-PX-{user?.uid.slice(0,6).toUpperCase()}</div>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">{t.workplace}</label>
                <div className="text-sm font-bold text-slate-700">Central Medical Command</div>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-1">{t.specialization}</label>
                <div className="text-sm font-bold text-slate-700">{t.medicalIntelligence}</div>
              </div>
            </div>

            <div className="pt-6 border-t border-slate-100 space-y-6">
              <h4 className="text-xs font-black uppercase tracking-widest text-slate-400">{t.biometricVaulting}</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-5 bg-emerald-50 border border-emerald-100 rounded-3xl flex items-center gap-4">
                  <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-emerald-600 shadow-sm">
                    <Fingerprint size={24} />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-emerald-900">Bio-Verified</div>
                    <div className="text-[10px] text-emerald-600 font-bold uppercase">Hardware Match Active</div>
                  </div>
                </div>
                <div className="p-5 bg-slate-50 border border-slate-100 rounded-3xl flex items-center gap-4">
                  <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-slate-400">
                    <Smartphone size={24} />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-slate-500">Physical Token</div>
                    <div className="text-[10px] text-slate-400 font-bold uppercase">Not Provisioned</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-slate-100 flex flex-wrap gap-3">
              <button className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-bold text-sm shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-colors">{t.updateProfile}</button>
              <button className="px-6 py-2 bg-slate-100 text-slate-600 rounded-lg font-bold text-sm hover:bg-slate-200 transition-colors">{t.downloadDigitalId}</button>
            </div>
          </motion.div>
        );
      case 'language':
        return (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {langs.map((l) => (
                <button
                  key={l.id}
                  onClick={() => { setLanguage(l.id); setHasChanges(true); }}
                  className={cn(
                    "p-5 rounded-2xl border flex items-center justify-between transition-all group",
                    isRtl ? "text-right" : "text-left",
                    language === l.id 
                      ? "border-indigo-600 bg-indigo-50/50" 
                      : "border-slate-100 hover:border-indigo-200 hover:bg-slate-50"
                  )}
                >
                  <div className={cn(isRtl ? "text-right" : "text-left")}>
                    <span className="font-bold text-slate-900 block">{l.name}</span>
                    <span className="text-xs text-slate-400">{l.native}</span>
                  </div>
                  {language === l.id && (
                    <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white">
                      <Check size={16} />
                    </div>
                  )}
                </button>
              ))}
            </div>
            <div className="p-6 bg-amber-50 border border-amber-100 rounded-2xl flex gap-4">
              <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center text-amber-600 flex-shrink-0 shadow-sm">
                <Globe size={20} />
              </div>
              <p className="text-sm text-amber-800 leading-relaxed">
                <span className="font-bold block mb-1">{t.regionalOptimization}</span>
                {t.regionalOptimizationDesc}
              </p>
            </div>
          </motion.div>
        );
      case 'appearance':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button 
                onClick={() => { setIsDarkMode(false); setHasChanges(true); }} 
                className={cn(
                  "p-6 rounded-3xl border transition-all",
                  isRtl ? "text-right" : "text-left",
                  !isDarkMode ? "bg-indigo-600 text-white shadow-xl shadow-indigo-100" : "bg-white border-slate-100"
                )}
              >
                <Sun size={32} className="mb-4" />
                <div className="font-bold">{t.lightMode}</div>
                <div className="text-[10px] uppercase opacity-50">{t.dayShift}</div>
              </button>
              <button 
                onClick={() => { setIsDarkMode(true); setHasChanges(true); }} 
                className={cn(
                  "p-6 rounded-3xl border transition-all",
                  isRtl ? "text-right" : "text-left",
                  isDarkMode ? "bg-indigo-900 text-white shadow-xl shadow-slate-900/20" : "bg-white border-slate-100 grayscale cursor-not-allowed opacity-50"
                )}
              >
                <Moon size={32} className="mb-4" />
                <div className="font-bold">{t.darkMode}</div>
                <div className="text-[10px] uppercase opacity-50">{t.nightShift}</div>
              </button>
            </div>
            <div className="space-y-4">
              <h4 className="text-xs font-black uppercase tracking-widest text-slate-400">{t.accentColors}</h4>
              <div className="flex flex-wrap gap-4">
                {['indigo', 'emerald', 'rose', 'amber', 'slate'].map((color) => (
                  <button
                    key={color}
                    onClick={() => { setAccentColor(color); setHasChanges(true); }}
                    className={cn(
                      "w-12 h-12 rounded-full border-4 border-white shadow-lg transition-all hover:scale-110",
                      accentColor === color ? "scale-110 ring-4 ring-indigo-100" : "scale-100",
                      color === 'indigo' ? "bg-indigo-600" :
                      color === 'emerald' ? "bg-emerald-600" :
                      color === 'rose' ? "bg-rose-600" :
                      color === 'amber' ? "bg-amber-600" : "bg-slate-600"
                    )}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        );
      case 'security':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
             <div className="p-6 bg-white rounded-3xl border border-slate-100 shadow-sm flex items-center justify-between">
                <div className="flex items-center gap-4">
                   <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center">
                     <Fingerprint size={24} />
                   </div>
                   <div>
                     <h4 className="font-bold">{t.biometricVaulting}</h4>
                     <p className="text-xs text-slate-500">{t.biometricVaultingDesc}</p>
                   </div>
                </div>
                <div className="w-12 h-6 bg-indigo-600 rounded-full relative"><div className={cn("absolute top-1 w-4 h-4 bg-white rounded-full", isRtl ? "left-1" : "right-1")} /></div>
             </div>
             <div className="space-y-4">
                <h4 className="text-xs font-black uppercase tracking-widest text-slate-400">{t.securityActions}</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                   <button className="p-4 bg-slate-900 text-white rounded-2xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-slate-800 transition-colors">
                     <RefreshCw size={18} /> {t.cycleKeys}
                   </button>
                   <button className="p-4 bg-white border border-slate-200 text-rose-500 rounded-2xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-rose-50 transition-colors">
                     <LogOut size={18} /> {t.globalLogout}
                   </button>
                </div>
             </div>
          </motion.div>
        );
      case 'system':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                 <div className="p-6 bg-slate-50 border border-slate-100 rounded-3xl group hover:border-indigo-200 transition-all">
                    <Microscope size={24} className="text-indigo-600 mb-4 group-hover:scale-110 transition-transform" />
                    <h4 className="font-bold">{t.hardwareConnectivity}</h4>
                    <div className="mt-4 space-y-3">
                      <div className="flex justify-between text-xs items-center">
                        <span className="text-slate-500">{t.analyzers}</span> 
                        <div className="flex items-center gap-1.5">
                          <div className="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
                          <span className="font-bold text-green-600">{t.connected}</span>
                        </div>
                      </div>
                      <div className="flex justify-between text-xs items-center">
                        <span className="text-slate-500">{t.scanners}</span> 
                        <div className="flex items-center gap-1.5">
                          <RefreshCw size={10} className="text-indigo-400 animate-spin" />
                          <span className="font-bold text-indigo-400">{t.syncing}</span>
                        </div>
                      </div>
                    </div>
                 </div>
                 <div className="p-6 bg-slate-50 border border-slate-100 rounded-3xl col-span-1 lg:col-span-2">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <Cpu size={24} className="text-indigo-600" />
                        <h4 className="font-bold">{t.systemActivity}</h4>
                      </div>
                      <span className="px-2 py-0.5 bg-indigo-100 text-indigo-600 text-[10px] font-black uppercase rounded">{t.operationalStatus}: {t.optimal}</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-6">
                      <div className="space-y-2">
                        <div className="flex justify-between text-[10px] font-black text-slate-400 uppercase tracking-widest">
                          <span>{t.cpuLoad}</span>
                          <span>{cpuLoad.toFixed(1)}%</span>
                        </div>
                        <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                          <motion.div 
                            className={cn("h-full rounded-full transition-colors", cpuLoad > 80 ? "bg-rose-500" : "bg-indigo-600")} 
                            animate={{ width: `${cpuLoad}%` }}
                            transition={{ type: "spring", stiffness: 50 }}
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-[10px] font-black text-slate-400 uppercase tracking-widest">
                          <span>{t.memoryUsage}</span>
                          <span>{memoryUsage.toFixed(1)} GB</span>
                        </div>
                        <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                          <motion.div 
                            className="h-full bg-emerald-500 rounded-full" 
                            animate={{ width: `${(memoryUsage/32)*100}%` }}
                            transition={{ type: "spring", stiffness: 50 }}
                          />
                        </div>
                      </div>
                    </div>
                 </div>
              </div>
              
              <div className="p-6 bg-white border border-slate-100 rounded-3xl shadow-sm flex flex-col md:flex-row items-center gap-6">
                <Database size={40} className="text-slate-200" />
                <div className="flex-1">
                    <h4 className="font-bold">{t.storageOptimization}</h4>
                    <div className="mt-2 w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className={cn("h-full bg-indigo-600 rounded-full", isRtl ? "float-right" : "")} style={{ width: '32%' }} />
                    </div>
                    <div className="mt-2 text-[10px] text-slate-400 font-medium">32.4 GB of 500 GB used • {t.storagePartition}</div>
                </div>
                <button className="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-bold hover:bg-indigo-600 transition-colors whitespace-nowrap">
                   {t.clearNow}
                </button>
              </div>
          </motion.div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-8" dir={isRtl ? 'rtl' : 'ltr'}>
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 mb-2">
            <SettingsIcon size={18} />
            <span className="text-xs font-black uppercase tracking-[0.2em]">{t.platformControl}</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">{t.systemConfiguration}</h1>
          <p className="text-slate-500 mt-2 font-medium max-w-2xl">{t.settingsDesc}</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 group-focus-within:text-indigo-500 transition-colors">
              <RefreshCw size={16} className="animate-spin-slow" />
            </div>
            <input 
              id="settings-search"
              type="text"
              placeholder={t.searchParameters}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none w-full sm:w-64 transition-all"
            />
            <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
              <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-black text-slate-300 bg-slate-50 border border-slate-100 rounded">⌘K</kbd>
            </div>
          </div>
          <button className="w-full sm:w-auto px-5 py-2.5 bg-white border border-slate-200 text-slate-700 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-slate-50 shadow-sm transition-all whitespace-nowrap">
            <History size={18} /> {t.sessionLogs}
          </button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        <div className="w-full lg:w-72 flex-shrink-0">
          <div className="bg-white rounded-3xl border border-slate-100 p-2 sm:p-3 space-y-1 shadow-xl shadow-slate-200/40 sticky top-8">
            {filteredTabs.length > 0 ? (
              filteredTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); setSearchQuery(''); }}
                  className={cn(
                    "w-full flex items-center gap-3 p-4 rounded-2xl font-bold text-sm transition-all group relative",
                    activeTab === tab.id 
                      ? "bg-indigo-600 text-white shadow-xl shadow-indigo-100" 
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                  )}
                >
                  <div className={cn(
                    "p-1.5 rounded-lg transition-colors",
                    activeTab === tab.id ? "bg-white/20" : "bg-slate-100 group-hover:bg-indigo-50"
                  )}>
                    <tab.icon size={18} />
                  </div>
                  {tab.label}
                  {hasChanges && activeTab === tab.id && (
                    <div className="absolute top-4 right-4 w-2 h-2 bg-indigo-200 rounded-full animate-ping" />
                  )}
                </button>
              ))
            ) : (
              <div className="p-8 text-center">
                <AlertCircle size={32} className="mx-auto text-slate-200 mb-3" />
                <p className="text-xs text-slate-400 font-bold">{t.noSettingsFound}</p>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-3xl border border-slate-100 shadow-xl shadow-slate-200/40 min-h-[600px] flex flex-col">
            <div className="p-6 sm:p-8 border-b border-slate-50">
               <h2 className="text-2xl font-black text-slate-900">{tabs.find(targetTab => targetTab.id === activeTab)?.label}</h2>
               <p className="text-sm text-slate-400 mt-1">{t.configParametersFor} {tabs.find(targetTab => targetTab.id === activeTab)?.label.toLowerCase()}.</p>
            </div>
            <div className="p-6 sm:p-8 flex-1 relative overflow-x-hidden">
               {saveStatus === 'error' && (
                 <div className="mb-6 p-4 bg-rose-50 border border-rose-100 rounded-2xl flex items-center gap-3 text-rose-600 animate-in slide-in-from-top duration-300">
                    <AlertCircle size={20} />
                    <p className="text-xs font-bold">Failed to save configuration. Please check your connection and retry.</p>
                    <button onClick={handleSave} className="ml-auto underline font-black text-[10px] uppercase">Retry</button>
                 </div>
               )}
              <AnimatePresence mode="wait">
                {renderTabContent()}
              </AnimatePresence>
            </div>
            {(hasChanges || saveStatus !== 'idle') && (
              <div className="p-4 sm:p-6 border-t border-slate-50 bg-slate-50 flex flex-col sm:flex-row items-center justify-between gap-4 rounded-b-3xl sticky bottom-0">
                <div className="flex items-center gap-2 text-slate-400 text-[10px] font-black uppercase tracking-widest">
                  <Info size={14} />
                  {t.shortcutSave}
                </div>
                <div className="flex gap-4 w-full sm:w-auto">
                  <button 
                    onClick={() => { setHasChanges(false); setSaveStatus('idle'); }}
                    className="flex-1 sm:flex-none px-6 py-2 text-slate-500 font-bold text-sm hover:text-slate-900"
                    disabled={saveStatus === 'saving'}
                  >
                    {t.revertToDefaults}
                  </button>
                  <button 
                    onClick={handleSave}
                    disabled={saveStatus === 'saving'}
                    className={cn(
                      "flex-1 sm:flex-none px-8 py-2 rounded-xl font-bold text-sm shadow-lg transition-all flex items-center gap-2 min-w-[120px] justify-center",
                      saveStatus === 'saved' ? "bg-emerald-500 text-white shadow-emerald-100" : 
                      saveStatus === 'error' ? "bg-rose-500 text-white shadow-rose-100" :
                      "bg-indigo-600 text-white shadow-indigo-100",
                      saveStatus === 'saving' && "opacity-70 cursor-not-allowed"
                    )}
                  >
                    {saveStatus === 'saving' && <RefreshCw size={16} className="animate-spin" />}
                    {saveStatus === 'saved' && <Check size={16} />}
                    {saveStatus === 'error' ? "Retry" : saveStatus === 'saved' ? t.saved : saveStatus === 'saving' ? t.saving : t.saveChanges}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
