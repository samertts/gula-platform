import React from 'react';
import { motion } from 'motion/react';
import { Settings, CheckCircle, Zap, Shield, Database, LayoutGrid, RotateCw, Activity, Cpu } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function LabDeviceMonitor() {
  const { t } = useLanguage();

  const devices = [
    { id: 'NODE-01', model: 'Spectro-X4', status: 'Optimal', calibration: '99.9%', drift: '0.001%' },
    { id: 'NODE-02', model: 'Hematology Gen-6', status: 'Auto-Calibrating', calibration: '92.4%', drift: '0.012%' },
    { id: 'NODE-03', model: 'Molecular Array', status: 'Optimal', calibration: '100%', drift: '0.000%' },
  ];

  return (
    <div className="bg-white border border-slate-100 rounded-[3rem] p-10 shadow-sm relative overflow-hidden group">
      <div className="absolute top-0 right-0 p-12 opacity-[0.02] text-slate-900 pointer-events-none">
         <LayoutGrid size={400} />
      </div>

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-12">
           <div>
              <h3 className="text-2xl font-black uppercase tracking-tight text-slate-900">{t.selfCalibrating}</h3>
              <p className="text-[10px] font-black uppercase tracking-widest text-indigo-600 mt-1">Autonomous Device Integrity Grid</p>
           </div>
           <button className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest shadow-xl shadow-slate-200 hover:scale-105 transition-all">
              <RotateCw size={14} className="group-hover:rotate-180 transition-transform duration-500" /> 
              Global Re-Sync
           </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
           {devices.map((device, i) => (
             <motion.div 
               key={device.id}
               initial={{ opacity: 0, y: 10 }}
               animate={{ opacity: 1, y: 0 }}
               transition={{ delay: i * 0.1 }}
               className="p-8 bg-slate-50 rounded-[2.5rem] border border-slate-100 space-y-6 hover:bg-white hover:shadow-xl transition-all group/card"
             >
                <div className="flex justify-between items-start">
                   <div className="p-4 bg-white rounded-2xl shadow-sm text-indigo-600 group-hover/card:bg-indigo-600 group-hover/card:text-white transition-colors">
                      <Cpu size={24} />
                   </div>
                   <div className={cn(
                     "px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest",
                     device.status === 'Optimal' ? "bg-emerald-100 text-emerald-600" : "bg-amber-100 text-amber-600 animate-pulse"
                   )}>
                      {device.status}
                   </div>
                </div>

                <div>
                   <h4 className="text-lg font-black text-slate-900 tracking-tight">{device.model}</h4>
                   <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{device.id}</p>
                </div>

                <div className="space-y-4 pt-4 border-t border-slate-100">
                   <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-slate-400 uppercase tracking-widest">Calibration</span>
                      <span className="font-black text-slate-900">{device.calibration}</span>
                   </div>
                   <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                      <motion.div 
                         initial={{ width: 0 }}
                         animate={{ width: device.calibration }}
                         className="h-full bg-indigo-500"
                      />
                   </div>
                   <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-slate-400 uppercase tracking-widest">Temporal Drift</span>
                      <span className="font-black text-amber-600">{device.drift}</span>
                   </div>
                </div>
             </motion.div>
           ))}
        </div>

        <div className="mt-12 p-8 bg-slate-900 rounded-[3rem] text-white flex flex-col lg:flex-row items-center justify-between gap-8">
           <div className="flex items-center gap-6">
              <div className="p-4 bg-white/10 rounded-2xl">
                 <Shield size={32} className="text-indigo-400" />
              </div>
              <div>
                 <h4 className="text-lg font-black uppercase tracking-tight">{t.immutableAudit} Trail Active</h4>
                 <p className="text-xs text-slate-400 font-medium">All device cycles are hashed and appended to the national relational sync grid.</p>
              </div>
           </div>
           <div className="flex items-center gap-8">
              <div className="text-right">
                 <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Consistency Score</p>
                 <p className="text-2xl font-black">99.999%</p>
              </div>
              <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center border border-white/10">
                 <Activity size={32} className="text-emerald-500" />
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
