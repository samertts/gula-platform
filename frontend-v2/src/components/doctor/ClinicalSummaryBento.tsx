import React from 'react';
import { 
  Sparkles, BrainCircuit, Activity, 
  TrendingUp, AlertTriangle, Scale,
  Microscope, Stethoscope, FileText
} from 'lucide-react';
import { motion } from 'motion/react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';

export function ClinicalSummaryBento() {
  const { t } = useLanguage();

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 w-full">
      {/* Primary Narrative */}
      <div className="md:col-span-8 bg-indigo-600 rounded-[3rem] p-8 text-white relative overflow-hidden group shadow-2xl shadow-indigo-100">
        <div className="absolute top-0 right-0 p-12 opacity-10 group-hover:scale-125 transition-transform duration-1000">
          <BrainCircuit size={180} />
        </div>
        <div className="relative z-10 flex flex-col h-full justify-between">
           <div>
              <div className="flex items-center gap-3 mb-6">
                 <div className="p-2 bg-white/20 rounded-xl">
                    <Sparkles size={20} />
                 </div>
                 <span className="text-[10px] font-black uppercase tracking-[0.3em] font-headline">Clinical Synthesis</span>
              </div>
              <h3 className="text-3xl font-black font-headline tracking-tighter mb-4 leading-none italic">
                "Probable chronic anemia exacerbation linked to diet."
              </h3>
              <p className="text-sm text-indigo-100 font-medium leading-relaxed max-w-xl opacity-90">
                AI cross-reference with previous 4 years of CBC data indicates a cyclic drop in Ferritin levels every March. Current symptoms of fatigue and pallor align with this metabolic trend. Recommended action: Strategic iron supplementation and metabolic follow-up in 3 weeks.
              </p>
           </div>
           
           <div className="mt-10 flex gap-4">
              <div className="px-4 py-2 bg-white/10 border border-white/20 rounded-xl backdrop-blur-md">
                 <p className="text-[8px] font-black uppercase tracking-widest text-indigo-200 mb-1">Confidence Score</p>
                 <p className="text-xl font-black">94.2%</p>
              </div>
              <div className="px-4 py-2 bg-white/10 border border-white/20 rounded-xl backdrop-blur-md">
                 <p className="text-[8px] font-black uppercase tracking-widest text-indigo-200 mb-1">Risk of Anomaly</p>
                 <p className="text-xl font-black text-emerald-400">Low</p>
              </div>
           </div>
        </div>
      </div>

      {/* Quick Metrics */}
      <div className="md:col-span-4 flex flex-col gap-6">
         <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm group">
            <div className="flex justify-between items-start mb-6">
               <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                  <TrendingUp size={24} />
               </div>
               <span className="px-2 py-0.5 bg-rose-50 text-rose-600 text-[10px] font-black uppercase rounded tracking-widest">Rising</span>
            </div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Metabolic Trend</p>
            <h4 className="text-2xl font-black text-slate-900 tracking-tight">+14.2% CRP</h4>
            <p className="text-[11px] text-slate-400 font-medium mt-2">Inflamation indices higher than region average (Erbal-04).</p>
         </div>

         <div className="bg-slate-900 p-8 rounded-[2.5rem] text-white flex-1 relative overflow-hidden group">
            <div className="absolute bottom-0 right-0 p-8 opacity-10 group-hover:translate-x-4 transition-transform">
               <Scale size={80} />
            </div>
            <div className="flex items-center gap-3 mb-6">
               <AlertTriangle className="text-amber-400" size={20} />
               <span className="text-[10px] font-black uppercase tracking-widest text-amber-400">Interaction Risk</span>
            </div>
            <p className="text-sm font-bold leading-relaxed">
               Current protocol conflicts with regional disease trends (H1N1 variant).
            </p>
            <button className="mt-6 text-[10px] font-black uppercase tracking-widest text-indigo-400 hover:text-white transition-colors">
               Adjust Reasoning →
            </button>
         </div>
      </div>

      {/* Evidence Panels */}
      <div className="md:col-span-12 grid grid-cols-1 md:grid-cols-4 gap-6">
         {[
           { label: 'Lab Accuracy', val: '99.9%', icon: Microscope, color: 'text-emerald-500' },
           { label: 'System Guard', val: 'Active', icon: Stethoscope, color: 'text-indigo-500' },
           { label: 'Historical Gap', val: 'None', icon: FileText, color: 'text-slate-400' },
           { label: 'Live Vitals', val: 'Synced', icon: Activity, color: 'text-rose-500' }
         ].map((item, i) => (
           <div key={i} className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm flex items-center justify-between hover:border-indigo-100 transition-all cursor-pointer group">
              <div>
                 <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">{item.label}</p>
                 <p className="text-xl font-black text-slate-900 tracking-tight">{item.val}</p>
              </div>
              <div className={cn("p-3 bg-slate-50 rounded-xl group-hover:scale-110 transition-transform", item.color)}>
                 <item.icon size={20} />
              </div>
           </div>
         ))}
      </div>
    </div>
  );
}
