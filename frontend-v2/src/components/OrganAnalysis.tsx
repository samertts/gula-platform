import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Heart, Activity, Thermometer, ShieldCheck, Zap, X, ChevronRight } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

export function OrganAnalysis() {
  const { t } = useLanguage();
  const [activeSegment, setActiveSegment] = useState<'aorta' | 'ventricle' | 'atrium' | null>(null);

  const segments = {
    aorta: { title: 'Aortic Arch', status: 'Stable', pressure: '120 mmHg', desc: 'Normal elasticity and flow dynamics detected via Doppler-AI synthesis.' },
    ventricle: { title: 'Left Ventricle', status: 'Elevated Load', pressure: '145 mmHg', desc: 'Mild hypertrophic patterns observed. Correlation with hypertension history.' },
    atrium: { title: 'Right Atrium', status: 'Optimal', pressure: '5 mmHg', desc: 'Sinus rhythm synchronization at 99.4%.' },
  };

  return (
    <div className="bg-slate-900 rounded-[32px] p-8 text-white relative overflow-hidden h-full min-h-[500px] flex flex-col">
      <div className="absolute top-0 right-0 p-12 opacity-[0.05]">
         <Heart size={300} strokeWidth={1} />
      </div>

      <div className="relative z-10 flex flex-col h-full">
        <div className="flex justify-between items-start mb-8">
           <div>
              <h3 className="text-xl font-black uppercase tracking-tight">{t.organAnalysis}</h3>
              <div className="flex items-center gap-2 mt-1">
                 <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                 <span className="text-[10px] font-black uppercase tracking-widest text-emerald-400">Quantum Rendering Active</span>
              </div>
           </div>
           <div className="flex gap-2">
              <div className="p-2 bg-white/5 rounded-xl border border-white/10 text-indigo-400">
                 <Zap size={18} />
              </div>
           </div>
        </div>

        <div className="flex-1 flex items-center justify-center relative">
           {/* Conceptual 3D Heart Visualizer */}
           <div className="relative">
              <motion.div 
                animate={{ 
                  scale: [1, 1.05, 1],
                  filter: ['brightness(1)', 'brightness(1.2)', 'brightness(1)']
                }}
                transition={{ repeat: Infinity, duration: 0.8 }}
                className="relative z-10 text-rose-500/80 drop-shadow-[0_0_40px_rgba(244,63,94,0.4)]"
              >
                 <Heart size={200} fill="currentColor" strokeWidth={0.5} />
              </motion.div>

              {/* Interaction Hotspots */}
              <button 
                onClick={() => setActiveSegment('aorta')}
                className="absolute top-4 left-1/2 -translate-x-1/2 z-20 group"
              >
                 <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center shadow-xl group-hover:scale-150 transition-all">
                    <div className="w-2 h-2 bg-indigo-600 rounded-full" />
                 </div>
                 <div className="absolute top-6 left-1/2 -translate-x-1/2 whitespace-nowrap bg-black/80 backdrop-blur-md px-2 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">Aorta</div>
              </button>

              <button 
                onClick={() => setActiveSegment('ventricle')}
                className="absolute bottom-12 right-12 z-20 group"
              >
                 <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center shadow-xl group-hover:scale-150 transition-all">
                    <div className="w-2 h-2 bg-indigo-600 rounded-full" />
                 </div>
                 <div className="absolute top-6 left-1/2 -translate-x-1/2 whitespace-nowrap bg-black/80 backdrop-blur-md px-2 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">Ventricle</div>
              </button>

              <div className="absolute inset-0 border-[40px] border-white/[0.02] rounded-full scale-150 animate-[spin_20s_linear_infinity]" />
              <div className="absolute inset-0 border border-white/5 rounded-full scale-125 border-dashed animate-[spin_15s_linear_infinite_reverse]" />
           </div>
        </div>

        <div className="space-y-6">
           <AnimatePresence mode="wait">
              {activeSegment ? (
                <motion.div 
                  key={activeSegment}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="p-6 bg-white/5 rounded-3xl border border-white/10 relative group"
                >
                   <button 
                     onClick={() => setActiveSegment(null)}
                     className="absolute top-4 right-4 p-1 hover:bg-white/10 rounded-full transition-colors"
                   >
                     <X size={14} />
                   </button>
                   <div className="flex items-center gap-2 mb-3">
                      <ShieldCheck size={16} className="text-indigo-400" />
                      <h4 className="text-sm font-black uppercase tracking-tight">{segments[activeSegment].title}</h4>
                   </div>
                   <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
                         <span className="text-[8px] font-black uppercase tracking-widest text-white/40 block mb-1">Status</span>
                         <span className="text-xs font-bold text-indigo-300">{segments[activeSegment].status}</span>
                      </div>
                      <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
                         <span className="text-[8px] font-black uppercase tracking-widest text-white/40 block mb-1">Pressure</span>
                         <span className="text-xs font-bold text-white font-mono">{segments[activeSegment].pressure}</span>
                      </div>
                   </div>
                   <p className="text-[10px] text-white/60 leading-relaxed font-medium">
                      {segments[activeSegment].desc}
                   </p>
                </motion.div>
              ) : (
                <motion.div 
                   initial={{ opacity: 0 }}
                   animate={{ opacity: 1 }}
                   className="p-6 bg-indigo-600/20 rounded-3xl border border-indigo-500/30 border-dashed text-center"
                >
                   <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400 mb-2">Select a Hotspot for Analysis</p>
                   <p className="text-[9px] text-indigo-300 font-medium">Click on any marker in the 3D space to run a real-time molecular-biological analysis report.</p>
                </motion.div>
              )}
           </AnimatePresence>
           
           <div className="grid grid-cols-3 gap-3">
              {[
                { icon: Activity, label: 'Flow', val: '92%' },
                { icon: Thermometer, label: 'Temp', val: '37.2°' },
                { icon: Zap, label: 'Impulse', val: 'High' },
              ].map((m, i) => (
                <div key={i} className="p-3 bg-white/5 rounded-2xl border border-white/5 text-center">
                   <m.icon size={12} className="mx-auto mb-2 text-indigo-400" />
                   <p className="text-[8px] font-black uppercase tracking-widest text-white/30">{m.label}</p>
                   <p className="text-[10px] font-black mt-0.5">{m.val}</p>
                </div>
              ))}
           </div>
        </div>
      </div>
    </div>
  );
}
