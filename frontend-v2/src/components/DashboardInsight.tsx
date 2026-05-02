import React from 'react';
import { BrainCircuit, Sparkles, ArrowUpRight, TrendingUp } from 'lucide-react';
import { motion } from 'motion/react';
import { useLanguage } from '../contexts/LanguageContext';

export function DashboardInsight() {
  const { t } = useLanguage();

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-indigo-600 p-8 rounded-[2.5rem] text-white shadow-2xl shadow-indigo-200 relative overflow-hidden group"
    >
      <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-125 transition-transform duration-700">
        <BrainCircuit size={120} />
      </div>

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-white/20 rounded-xl relative">
            <Sparkles size={20} className="text-white" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-rose-500 rounded-full border-2 border-indigo-600 animate-pulse" />
          </div>
          <span className="text-[10px] font-black uppercase tracking-[0.2em]">{t?.medicalIntelligence || 'Medical Intelligence'}</span>
        </div>

        <h3 className="text-2xl font-black font-headline mb-4 tracking-tighter leading-tight italic">
          "Regional data suggests a shift in resource allocation priorities."
        </h3>

        <p className="text-sm text-indigo-100 font-medium leading-relaxed mb-8 opacity-80">
          Based on real-time epidemiological tracking, there is an 82% probability of increased diagnostics load in the North-East corridor over the next 72 hours.
        </p>

        <div className="flex items-center gap-4">
          <button className="px-6 py-3 bg-white text-indigo-600 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-xl">
            Authorize Allocation
          </button>
          <button className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-white/60 hover:text-white transition-colors">
            View Analytics <ArrowUpRight size={14} />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
