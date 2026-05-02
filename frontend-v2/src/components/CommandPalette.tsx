import React, { useState, useEffect } from 'react';
import { Search, Command, User, Activity, Settings, Smartphone, LogOut, ChevronRight, Calculator, Microscope, Pill, FileText, Zap, BrainCircuit } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';
import { useNavigate } from 'react-router-dom';

export function CommandPalette() {
  const { t, language } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const isRtl = language === 'AR' || language === 'KU' || language === 'SY';

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
      if (e.key === 'Escape') setIsOpen(false);
    };

    const handleOpenEvent = () => setIsOpen(true);

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('open-command-palette', handleOpenEvent);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('open-command-palette', handleOpenEvent);
    };
  }, []);

  const onClose = () => setIsOpen(false);

  const actions = [
    { id: 'p1', label: 'Open Ahmed Mansour', category: 'Patients', icon: User, shortcut: 'P 1', action: () => navigate('/doctor/patient/P-9021') },
    { id: 'p2', label: 'Open Layla S.', category: 'Patients', icon: User, shortcut: 'P 2', action: () => navigate('/doctor/patient/P-105') },
    { id: 'c1', label: 'Order CBC Panel', category: 'Quick Actions', icon: Microscope, shortcut: 'O C', action: () => alert('Order Created') },
    { id: 'c2', label: 'New Prescription', category: 'Quick Actions', icon: Pill, shortcut: 'O P', action: () => navigate('/doctor/patient/P-9021?tab=prescriptions') },
    { id: 'c3', label: 'Dose Calculator', category: 'Tools', icon: Calculator, shortcut: 'T C', action: () => alert('Calculator Opened') },
    { id: 's1', label: 'Switch to Emergency Mode', category: 'System', icon: Zap, shortcut: 'S E', action: () => alert('Emergency Mode Active') },
    { id: 's2', label: 'View Clinical Guidelines', category: 'System', icon: FileText, shortcut: 'S G', action: () => alert('Guidelines Opened') },
    { id: 'dash', label: t.goToDashboard, icon: Command, shortcut: 'G D', category: 'Navigation', action: () => navigate('/') },
    { id: 'lab-dash', label: 'Laboratory Hub', icon: Microscope, shortcut: 'G L', category: 'Navigation', action: () => navigate('/lab/dashboard') },
    { id: 'settings', label: t.settings, icon: Settings, shortcut: 'G S', category: 'Navigation', action: () => navigate('/settings') },
  ];

  const filteredActions = actions.filter(a => 
    a.label.toLowerCase().includes(query.toLowerCase()) || 
    a.category.toLowerCase().includes(query.toLowerCase())
  );

  if (!isOpen) return null;

  const categories = Array.from(new Set(filteredActions.map(a => a.category)));

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] px-4">
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-md"
      />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: -20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: -20 }}
        className="relative w-full max-w-2xl bg-white rounded-[2.5rem] shadow-2xl shadow-indigo-500/20 overflow-hidden border border-slate-100"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        <div className="p-8 border-b border-slate-100 flex items-center gap-6">
          <div className="w-14 h-14 bg-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-indigo-100">
             <Command size={28} />
          </div>
          <input 
            autoFocus
            type="text"
            placeholder={t.searchCommands || "Universal Command Search (Ctrl+K)..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent border-none outline-none text-2xl font-black text-slate-900 placeholder:text-slate-200 tracking-tight"
          />
          <div className="flex items-center gap-3">
             <div className="px-3 py-1.5 bg-slate-900 rounded-xl text-[10px] font-black text-white shadow-xl">CTRL</div>
             <div className="px-3 py-1.5 bg-slate-900 rounded-xl text-[10px] font-black text-white shadow-xl">K</div>
          </div>
        </div>

        <div className="p-6 max-h-[60vh] overflow-y-auto custom-scrollbar bg-slate-50/30">
          {categories.map(cat => (
            <div key={cat} className="mb-10 last:mb-0">
               <div className="px-4 py-2 text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-indigo-600 rounded-full" />
                  {cat}
               </div>
               <div className="space-y-1">
                 {filteredActions.filter(a => a.category === cat).map((action) => (
                   <button
                     key={action.id}
                     onClick={() => { action.action(); onClose(); }}
                     className="w-full flex items-center gap-6 p-4 rounded-[1.5rem] hover:bg-white hover:shadow-xl hover:shadow-indigo-100/40 transition-all group"
                   >
                     <div className="w-12 h-12 rounded-xl bg-white border border-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-indigo-600 group-hover:text-white transition-all shadow-sm">
                       <action.icon size={24} />
                     </div>
                     <span className="flex-1 text-left font-bold text-slate-700 group-hover:text-indigo-900 text-lg">{action.label}</span>
                     <div className="flex gap-2">
                       {action.shortcut.split(' ').map((s, i) => (
                         <kbd key={i} className="px-3 py-2 bg-slate-900 rounded-xl text-[10px] font-black text-white shadow-lg border border-white/10">{s}</kbd>
                       ))}
                     </div>
                   </button>
                 ))}
               </div>
            </div>
          ))}
          {filteredActions.length === 0 && (
            <div className="p-20 text-center">
               <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-6">
                  <Search size={32} className="text-slate-300" />
               </div>
               <p className="text-slate-400 font-bold text-lg">No clinical shortcuts found.</p>
               <p className="text-[10px] text-slate-300 font-black uppercase mt-2">Try searching generic names or roles</p>
            </div>
          )}
        </div>

        <div className="p-6 bg-slate-900 border-t border-slate-800 flex justify-between items-center text-[10px] font-bold text-slate-400">
           <div className="flex gap-6">
             <span className="flex items-center gap-2 text-indigo-400"><ChevronRight size={14} /> Execute</span>
             <span className="flex items-center gap-2"><Command size={14} /> OS Mode</span>
           </div>
           <div className="flex items-center gap-2 text-emerald-400">
             <BrainCircuit size={14} className="animate-pulse" /> GULA Clinical Reasoning (v4.2)
           </div>
        </div>
      </motion.div>
    </div>
  );
}
