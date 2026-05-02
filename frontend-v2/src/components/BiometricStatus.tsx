import React from 'react';
import { motion } from 'motion/react';
import { Fingerprint, ShieldCheck, Activity, Brain } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function BiometricStatus() {
  const { t } = useLanguage();

  const metrics = [
    { label: 'Voice Signature', status: 'Verified', value: 99.4, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Ocular Pattern', status: 'Active', value: 98.2, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Thermal Logic', status: 'In-Sync', value: 100, color: 'text-rose-600', bg: 'bg-rose-50' },
    { label: 'Behavioral DNA', status: 'Calibrating', value: 85.0, color: 'text-amber-600', bg: 'bg-amber-50' },
  ];

  return (
    <div className="bg-white border border-slate-100 rounded-[3rem] p-8 shadow-sm">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h3 className="text-lg font-black uppercase tracking-tight text-slate-900">{t.biometricStatus}</h3>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Grid Multi-Factor Integrity</p>
        </div>
        <div className="p-3 bg-indigo-600 text-white rounded-2xl shadow-lg shadow-indigo-100">
          <Fingerprint size={24} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {metrics.map((m, i) => (
          <motion.div 
            key={m.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className={cn("p-4 rounded-3xl border border-slate-50", m.bg.replace('50', '20'))}
          >
            <div className="flex justify-between items-start mb-3">
              <span className={cn("text-[9px] font-black uppercase tracking-widest", m.color)}>{m.status}</span>
              <Activity size={12} className={m.color} />
            </div>
            <p className="text-xs font-black text-slate-800 mb-1">{m.label}</p>
            <div className="flex items-end gap-1">
              <span className="text-xl font-black text-slate-900">{m.value}%</span>
              <span className="text-[8px] font-bold text-slate-400 mb-1 uppercase">Match</span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-8 p-6 bg-slate-900 rounded-[2.5rem] relative overflow-hidden group">
         <div className="absolute inset-0 bg-indigo-600/10 opacity-0 group-hover:opacity-100 transition-opacity" />
         <div className="relative z-10 flex items-center gap-4">
            <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center text-indigo-400">
               <Brain size={24} />
            </div>
            <div>
               <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Cognitive Load</p>
               <h4 className="text-sm font-bold text-white uppercase tracking-tight">System Optimized for Heavy Traffic</h4>
            </div>
         </div>
      </div>
    </div>
  );
}
