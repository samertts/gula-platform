import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ShieldAlert, MapPin, Activity, Zap, ChevronRight, Clock } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function PredictiveOutbreak() {
  const { t } = useLanguage();
  const [timeIndex, setTimeIndex] = useState(0);

  const forecast = [
    { day: 'Today', status: 'Stable', risk: 12, cities: ['Baghdad', 'Basrah'] },
    { day: '+24h', status: 'Warning', risk: 34, cities: ['Baghdad', 'Najaf'] },
    { day: '+48h', status: 'Elevated', risk: 65, cities: ['Mosul', 'Erbil'] },
    { day: '+72h', status: 'Critical', risk: 89, cities: ['Kirkuk', 'Nineveh'] },
    { day: '+1w', status: 'Outbreak', risk: 98, cities: ['National Grid'] },
  ];

  return (
    <div className="bg-slate-900 border border-white/5 rounded-[3rem] p-8 text-white h-full flex flex-col relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-64 h-64 bg-rose-500/10 blur-[100px] -mr-32 -mt-32" />
      
      <div className="relative z-10 flex flex-col h-full">
        <div className="flex justify-between items-start mb-8">
           <div>
              <h3 className="text-xl font-black uppercase tracking-tight">{t.predictiveOutbreak}</h3>
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">Epi-Neural Engine v2.0</p>
           </div>
           <div className="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-xl text-[10px] font-black uppercase text-indigo-400">
              <Zap size={12} /> Live Sync
           </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center space-y-12 py-8">
           <div className="relative">
              <motion.div 
                key={timeIndex}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="relative z-10 text-center"
              >
                 <div className="text-6xl font-black text-white mb-2 drop-shadow-[0_0_30px_rgba(255,255,255,0.1)]">
                    {forecast[timeIndex].risk}%
                 </div>
                 <p className={cn(
                   "text-[10px] font-black uppercase tracking-[1em] ml-[1em]",
                   forecast[timeIndex].risk > 80 ? "text-rose-500" : forecast[timeIndex].risk > 50 ? "text-amber-500" : "text-emerald-500"
                 )}>
                    {forecast[timeIndex].status}
                 </p>
              </motion.div>
              <div className="absolute inset-0 border-[1px] border-white/5 rounded-full scale-150 animate-[ping_4s_linear_infinite]" />
              <div className="absolute inset-0 border-[1px] border-white/5 rounded-full scale-125 animate-[ping_3s_linear_infinite_reverse]" />
           </div>

           <div className="w-full space-y-6">
              <div className="flex flex-wrap gap-2 justify-center">
                 {forecast[timeIndex].cities.map(city => (
                    <div key={city} className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/5 rounded-2xl">
                       <MapPin size={12} className="text-rose-400" />
                       <span className="text-xs font-bold">{city}</span>
                    </div>
                 ))}
              </div>

              <div className="px-8 flex flex-col gap-4">
                 <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-slate-500">
                    <span>Temporal Scrubbing</span>
                    <span>{forecast[timeIndex].day} Foresight</span>
                 </div>
                 <input 
                   type="range" 
                   min="0" 
                   max={forecast.length - 1} 
                   value={timeIndex}
                   onChange={(e) => setTimeIndex(Number(e.target.value))}
                   className="w-full accent-rose-600 cursor-pointer h-1.5 bg-white/10 rounded-full appearance-none"
                 />
              </div>
           </div>
        </div>

        <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center justify-between group-hover:border-rose-500/30 transition-colors">
           <div className="flex items-center gap-4">
              <div className="p-2 bg-rose-500/10 text-rose-500 rounded-xl">
                 <ShieldAlert size={18} />
              </div>
              <div>
                 <p className="text-[10px] font-black uppercase tracking-widest opacity-60">Containment Protocol</p>
                 <p className="text-xs font-bold">Automatic Lockdown Threshold at 75%</p>
              </div>
           </div>
           <ChevronRight size={18} className="text-slate-500 group-hover:text-white transition-colors" />
        </div>
      </div>
    </div>
  );
}
