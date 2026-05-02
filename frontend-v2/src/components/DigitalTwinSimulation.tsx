import React from 'react';
import { motion } from 'motion/react';
import { User, Activity, Zap, Shield, Play, RotateCcw, Brain, Heart, Thermometer } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function DigitalTwinSimulation() {
  const { t } = useLanguage();

  return (
    <div className="bg-white border border-slate-100 rounded-[3rem] p-10 shadow-sm relative overflow-hidden group">
      <div className="absolute top-0 right-0 p-12 opacity-[0.02]">
         <User size={400} strokeWidth={1} />
      </div>

      <div className="relative z-10 flex flex-col h-full lg:min-h-[600px]">
        <div className="flex justify-between items-start mb-12">
           <div>
              <h3 className="text-2xl font-black uppercase tracking-tight text-slate-900">{t.digitalTwin}</h3>
              <div className="flex items-center gap-2 mt-1">
                 <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                 <span className="text-[10px] font-black uppercase tracking-widest text-emerald-500 font-bold">Real-time Telemetry Active</span>
              </div>
           </div>
           <div className="flex gap-2">
              <button className="p-3 bg-slate-50 text-slate-400 rounded-2xl hover:text-indigo-600 transition-colors border border-slate-100">
                 <RotateCcw size={20} />
              </button>
              <button className="px-6 py-3 bg-indigo-600 text-white rounded-2xl flex items-center gap-2 shadow-lg shadow-indigo-100 hover:scale-105 transition-all">
                 <Play size={18} />
                 <span className="text-[10px] font-black uppercase tracking-widest">Start Simulation</span>
              </button>
           </div>
        </div>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
           <div className="lg:col-span-5 space-y-8">
              <div>
                 <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-6">Simulation Models</p>
                 <div className="space-y-3">
                    {[
                      { label: 'Dietary Impact v4', icon: Zap, status: '98% Probable' },
                      { label: 'Sleep Recovery AI', icon: Brain, status: 'Stable' },
                      { label: 'Exercise Optimization', icon: Activity, status: 'Needs Input' },
                    ].map((model, i) => (
                      <div key={i} className="p-5 bg-slate-50 rounded-[2rem] border border-slate-100 flex items-center justify-between group/model hover:bg-white hover:shadow-md transition-all">
                         <div className="flex items-center gap-4">
                            <div className="p-2 bg-white rounded-xl shadow-sm text-indigo-500">
                               <model.icon size={18} />
                            </div>
                            <div>
                               <p className="text-xs font-black text-slate-800">{model.label}</p>
                               <p className="text-[8px] font-bold text-slate-400 uppercase tracking-widest">{model.status}</p>
                            </div>
                         </div>
                         <Shield size={14} className="text-slate-200 group-hover/model:text-emerald-400 transition-colors" />
                      </div>
                    ))}
                 </div>
              </div>

              <div className="p-6 bg-slate-900 rounded-[2.5rem] text-white">
                 <div className="flex items-center gap-3 mb-4 text-indigo-400">
                    <Brain size={20} />
                    <h4 className="text-sm font-black uppercase tracking-tight">{t.treatmentSimulation}</h4>
                 </div>
                 <p className="text-[11px] text-slate-400 leading-relaxed">
                    Predict the efficacy of prescribed medications by simulating metabolic absorption against your genetic markers.
                 </p>
                 <button className="w-full mt-6 py-3 bg-white/5 border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-white/10 transition-all">
                    Run Metabolic Analysis
                 </button>
              </div>
           </div>

           <div className="lg:col-span-7 flex flex-col items-center justify-center relative py-12">
              <div className="relative z-10 w-full max-w-[400px] aspect-square flex items-center justify-center">
                 <motion.div 
                   animate={{ rotate: 360 }}
                   transition={{ duration: 60, repeat: Infinity, ease: 'linear' }}
                   className="absolute inset-0 border border-slate-100 rounded-full border-dashed"
                 />
                 <motion.div 
                   animate={{ rotate: -360 }}
                   transition={{ duration: 40, repeat: Infinity, ease: 'linear' }}
                   className="absolute inset-4 border border-slate-50 rounded-full"
                 />
                 
                 <div className="relative z-20 text-indigo-100/50">
                    <User size={280} strokeWidth={0.5} />
                    {/* Pulsing Vital Markers */}
                    <div className="absolute top-1/4 left-1/3 w-3 h-3 bg-rose-500 rounded-full ring-4 ring-rose-500/20 animate-ping" />
                    <div className="absolute top-1/2 right-1/4 w-3 h-3 bg-indigo-500 rounded-full ring-4 ring-indigo-500/20 animate-ping" />
                    <div className="absolute bottom-1/3 left-1/4 w-3 h-3 bg-indigo-500 rounded-full ring-4 ring-indigo-500/20 animate-ping" />
                 </div>

                 {/* Floating Metric Bubbles */}
                 <motion.div 
                    animate={{ y: [0, -20, 0] }}
                    transition={{ duration: 4, repeat: Infinity }}
                    className="absolute top-0 right-0 p-4 bg-white shadow-xl rounded-[2rem] border border-slate-100 flex items-center gap-3"
                 >
                    <Heart size={16} className="text-rose-500" />
                    <div className="text-right">
                       <p className="text-[8px] font-black uppercase text-slate-400">Cardio</p>
                       <p className="text-xs font-black text-slate-900">Elevated</p>
                    </div>
                 </motion.div>

                 <motion.div 
                    animate={{ y: [0, 20, 0] }}
                    transition={{ duration: 5, repeat: Infinity }}
                    className="absolute bottom-10 left-0 p-4 bg-white shadow-xl rounded-[2rem] border border-slate-100 flex items-center gap-3"
                 >
                    <Thermometer size={16} className="text-indigo-500" />
                    <div className="text-left">
                       <p className="text-[8px] font-black uppercase text-slate-400">Thermo</p>
                       <p className="text-xs font-black text-slate-900">37.1°C</p>
                    </div>
                 </motion.div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
