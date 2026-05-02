import React from 'react';
import { motion } from 'motion/react';
import { ShieldAlert, Zap, Radio, Globe, ShieldCheck, Activity } from 'lucide-react';
import { cn } from '../../lib/utils';

const PIPELINE_STEPS = [
  { id: 'DET', label: 'Detection', icon: Radio, status: 'active', desc: 'Real-time symptom clustering via Karkh Nodes.' },
  { id: 'VAL', label: 'Validation', icon: Activity, status: 'pending', desc: 'Predictive modeling verifying vector trajectory.' },
  { id: 'QUA', label: 'Quarantine', icon: ShieldAlert, status: 'waiting', desc: 'Data-layer isolation for affected clinical sectors.' },
  { id: 'DEP', label: 'Response', icon: Zap, status: 'waiting', desc: 'Strategic reserve deployment & lab re-prioritization.' },
];

export function CrisisResponsePipeline() {
  return (
    <div className="bg-slate-900 rounded-[3rem] p-10 text-white relative overflow-hidden shadow-2xl border border-white/5">
      <div className="absolute top-0 right-0 p-12 opacity-[0.03] pointer-events-none scale-150">
         <ShieldAlert size={300} />
      </div>

      <div className="relative z-10 space-y-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
             <div className="w-14 h-14 bg-rose-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-rose-500/20">
                <Zap size={28} className="text-white fill-rose-300" />
             </div>
             <div>
                <h3 className="text-2xl font-black uppercase tracking-tight">Crisis Response Pipeline</h3>
                <p className="text-rose-400 text-[10px] font-black uppercase tracking-[0.2em]">Automated Protocol Execution v9.2</p>
             </div>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-500/20 font-black text-[10px] uppercase tracking-widest">
            <ShieldCheck size={14} /> GULA Governance Consensus
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
           {PIPELINE_STEPS.map((step, i) => (
             <div key={step.id} className="relative group">
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className={cn(
                    "p-8 rounded-[2.5rem] border transition-all h-full flex flex-col items-center text-center group-hover:scale-[1.02]",
                    step.status === 'active' ? "bg-rose-600 border-rose-500 shadow-2xl shadow-rose-900/40" : 
                    step.status === 'pending' ? "bg-slate-800 border-white/10" : "bg-white/5 border-white/5 opacity-60"
                  )}
                >
                   <div className={cn(
                     "w-16 h-16 rounded-2xl flex items-center justify-center mb-6 shadow-sm",
                     step.status === 'active' ? "bg-white/20" : "bg-white/5"
                   )}>
                      <step.icon size={32} className={cn(step.status === 'active' && "animate-pulse")} />
                   </div>
                   <h4 className="text-lg font-black uppercase tracking-tight mb-2">{step.label}</h4>
                   <p className="text-[10px] text-slate-400 font-medium group-hover:text-white/80 transition-colors">{step.desc}</p>
                   
                   {step.status === 'active' && (
                     <div className="mt-8 w-full bg-black/20 h-1.5 rounded-full overflow-hidden">
                        <motion.div 
                          animate={{ x: ['-100%', '300%'] }} 
                          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                          className="w-1/3 h-full bg-white shadow-[0_0_15px_white]"
                        />
                     </div>
                   )}
                </motion.div>
                
                {i < PIPELINE_STEPS.length - 1 && (
                  <div className="hidden xl:block absolute top-1/2 -right-4 translate-y-[-50%] z-20">
                     <div className="p-3 bg-slate-900 rounded-full border border-white/10 text-slate-600">
                        <Globe size={16} />
                     </div>
                  </div>
                )}
             </div>
           ))}
        </div>

        <div className="p-6 bg-white/5 rounded-[2.5rem] border border-white/5 flex flex-col md:flex-row items-center justify-between gap-6">
           <div className="flex items-center gap-4">
              <div className="flex -space-x-3">
                 {[1, 2, 3].map(i => (
                    <div key={i} className="w-10 h-10 rounded-full bg-slate-800 border-2 border-slate-900 overflow-hidden flex items-center justify-center text-[10px] font-black uppercase tracking-widest text-slate-500">Node {i}</div>
                 ))}
              </div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Collaborative Validation Path Active</p>
           </div>
           <button className="px-8 py-4 bg-white text-slate-900 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-[1.05] transition-all shadow-xl">
              Initiate Manual Override
           </button>
        </div>
      </div>
    </div>
  );
}
