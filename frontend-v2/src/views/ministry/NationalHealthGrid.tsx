import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Globe, Shield, Building2, Users, Activity, 
  AlertCircle, ArrowUpRight, Zap, Filter, 
  MapPin, Database, Layers, Search, Download
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';
import { 
  ResponsiveContainer, AreaChart, Area, 
  XAxis, YAxis, CartesianGrid, Tooltip, 
  BarChart, Bar, Cell 
} from 'recharts';

import { useNavigate } from 'react-router-dom';

const data = [
  { name: 'Karkh', value: 400, load: 85, active: 1240 },
  { name: 'Rusafa', value: 300, load: 72, active: 980 },
  { name: 'Basrah', value: 200, load: 94, active: 2100 },
  { name: 'Erbil', value: 278, load: 65, active: 1450 },
  { name: 'Najaf', value: 189, load: 88, active: 890 },
  { name: 'Nineveh', value: 239, load: 79, active: 1670 },
];

const hospitalData: Record<string, any[]> = {
  'Karkh': [
    { name: 'Al-Kindy General', cases: 142, load: 92, trend: '+5%' },
    { name: 'Yarmouk Specialized', cases: 88, load: 78, trend: '-2%' },
    { name: 'Ibn Sina Center', cases: 45, load: 40, trend: 'stable' },
  ],
  'Rusafa': [
    { name: 'Sheikh Zayed Hospital', cases: 110, load: 82, trend: '+12%' },
    { name: 'Ibn Al-Quff', cases: 67, load: 60, trend: 'stable' },
  ],
  'Basrah': [
    { name: 'Al-Sadr Teaching', cases: 210, load: 98, trend: '+18%' },
    { name: 'Basrah Childrens', cases: 54, load: 45, trend: '-4%' },
  ],
  // Default for others
};

export function NationalHealthGrid() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [activeRegion, setActiveRegion] = useState<string | null>(null);

  const displayedHospitals = activeRegion ? (hospitalData[activeRegion] || [
    { name: `${activeRegion} General Hub`, cases: Math.floor(Math.random() * 100), load: 75, trend: 'stable' },
    { name: `${activeRegion} Regional Center`, cases: Math.floor(Math.random() * 80), load: 60, trend: '+2%' },
  ]) : [];

  return (
    <div className="p-8 space-y-8 bg-slate-950 min-h-screen text-slate-100 selection:bg-indigo-500/30">
      {/* Header Panel */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-8 pb-8 border-b border-white/5">
        <div className="space-y-2">
           <div className="flex items-center gap-4 text-left">
              <div className="p-3 bg-indigo-600 rounded-2xl shadow-xl shadow-indigo-900/40 relative group cursor-pointer" onClick={() => navigate('/ministry/dashboard')}>
                 <Globe size={32} />
                 <div className="absolute inset-x-0 bottom-0 h-1 bg-white scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
              </div>
              <div>
                 <h1 className="text-3xl font-black tracking-tight uppercase">{t.nationalHealthGrid}</h1>
                 <p className="text-indigo-400 font-bold text-xs uppercase tracking-[0.3em]">{t.ministryOversight} • GULA OS V4</p>
              </div>
           </div>
        </div>

        <div className="flex gap-4">
             <button 
               onClick={() => navigate('/ministry/epidemiology')}
               className="px-6 py-3 bg-rose-600/20 border border-rose-500/30 text-rose-400 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-rose-600 hover:text-white transition-all flex items-center gap-2"
             >
               <AlertCircle size={14} /> {t.epiIntelligence}
             </button>
             <button 
               onClick={() => navigate('/ministry/audit')}
               className="px-6 py-3 bg-indigo-600 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest shadow-xl shadow-indigo-900/40 hover:scale-[1.02] transition-all flex items-center gap-2"
             >
               <Shield size={14} /> {t.compliance}
             </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Real-time Map/Grid Simulation */}
        <div className="xl:col-span-2 space-y-8">
           <div className="p-8 bg-white/5 border border-white/5 rounded-[3rem] relative overflow-hidden group">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/5 blur-[120px] rounded-full" />
              
              <div className="relative z-10">
                 <div className="flex justify-between items-start mb-12">
                    <div>
                       <h2 className="text-xl font-bold tracking-tight mb-1">{t.geospatialPattern}</h2>
                       <p className="text-xs text-indigo-400 font-bold uppercase tracking-widest">{t.clinicalSurveillance}</p>
                    </div>
                    <div className="flex gap-2">
                       <button className="px-4 py-2 bg-indigo-600 rounded-xl text-[10px] font-black uppercase tracking-widest">Neural Heatmap</button>
                       <button className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest">Node Clusters</button>
                    </div>
                 </div>

                 <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                    {data.map((region) => (
                       <motion.div
                         key={region.name}
                         whileHover={{ scale: 1.02 }}
                         className={cn(
                           "p-6 rounded-[2rem] border transition-all cursor-pointer group/node",
                           activeRegion === region.name 
                            ? "bg-indigo-600/20 border-indigo-500 shadow-xl shadow-indigo-900/40" 
                            : region.load > 85 
                            ? "bg-rose-500/10 border-rose-500/20" 
                            : "bg-white/5 border-white/5 hover:bg-white/10"
                         )}
                         onClick={() => setActiveRegion(region.name === activeRegion ? null : region.name)}
                       >
                          <div className="flex justify-between items-start mb-6">
                             <div className={cn(
                               "p-3 rounded-xl transition-all",
                               activeRegion === region.name ? "bg-indigo-600 text-white" : "bg-white/5 group-hover/node:bg-white/10"
                             )}>
                                <MapPin size={20} className={region.load > 85 && activeRegion !== region.name ? "text-rose-400" : "text-indigo-400"} />
                             </div>
                             <span className={cn(
                               "text-[10px] font-black px-2 py-1 rounded-full uppercase tracking-widest",
                               activeRegion === region.name ? "bg-white text-indigo-600" : region.load > 85 ? "bg-rose-500 text-white" : "bg-indigo-500/20 text-indigo-400"
                             )}>
                                {region.load}% Load
                             </span>
                          </div>
                          <h3 className="text-lg font-black text-white mb-1">{region.name}</h3>
                          <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                             <span>{region.active} Sessions</span>
                             <span>{region.value} Mbps</span>
                          </div>
                          
                          <div className="mt-4 h-1 w-full bg-white/5 rounded-full overflow-hidden">
                             <motion.div 
                               initial={{ width: 0 }}
                               animate={{ width: `${region.load}%` }}
                               className={cn(
                                 "h-full rounded-full shadow-[0_0_10px_rgba(79,70,229,0.5)]",
                                 region.load > 85 ? "bg-rose-500" : "bg-indigo-500"
                               )} 
                             />
                          </div>
                       </motion.div>
                    ))}
                 </div>

                 <AnimatePresence>
                   {activeRegion && (
                     <motion.div
                       initial={{ opacity: 0, y: 20 }}
                       animate={{ opacity: 1, y: 0 }}
                       exit={{ opacity: 0, y: 10 }}
                       className="mt-12 p-8 bg-indigo-600/5 border border-indigo-500/20 rounded-[2.5rem] relative overflow-hidden"
                     >
                        <div className="flex items-center justify-between mb-8">
                           <div className="flex items-center gap-4">
                              <div className="w-10 h-10 bg-indigo-600 rounded-2xl flex items-center justify-center">
                                 <Building2 size={20} />
                              </div>
                              <div>
                                 <h4 className="text-sm font-black uppercase tracking-widest">{activeRegion} Granular Overview</h4>
                                 <p className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest italic">Hospital-Specific Health Intelligence</p>
                              </div>
                           </div>
                           <button 
                             onClick={() => setActiveRegion(null)}
                             className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white"
                           >
                              Collapse Details
                           </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                           {displayedHospitals.map((h, i) => (
                             <div key={i} className="p-4 bg-white/5 border border-white/5 rounded-2xl flex flex-col justify-between">
                                <div className="flex justify-between items-start mb-4">
                                   <h5 className="text-xs font-black text-white">{h.name}</h5>
                                   <span className={cn(
                                     "text-[8px] font-black px-1.5 py-0.5 rounded uppercase",
                                     h.load > 90 ? "bg-rose-500 text-white" : "bg-emerald-500/20 text-emerald-400"
                                   )}>{h.load}% CAP</span>
                                </div>
                                <div className="mt-auto">
                                  <div className="flex items-baseline justify-between">
                                     <p className="text-[10px] font-bold text-slate-400 uppercase">Active Cases: <span className="text-white">{h.cases}</span></p>
                                     <span className={cn(
                                       "text-[8px] font-black",
                                       h.trend.includes('+') ? "text-rose-400" : h.trend === 'stable' ? "text-slate-500" : "text-emerald-400"
                                     )}>{h.trend}</span>
                                  </div>
                                  <div className="w-full bg-white/5 h-1 rounded-full mt-2 overflow-hidden">
                                     <div className={cn("h-full", h.load > 90 ? "bg-rose-500" : "bg-indigo-500")} style={{ width: `${h.load}%` }} />
                                  </div>
                                </div>
                             </div>
                           ))}
                        </div>
                     </motion.div>
                   )}
                 </AnimatePresence>
              </div>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="p-8 bg-white/5 border border-white/5 rounded-[3rem]">
                 <h3 className="text-sm font-black uppercase tracking-widest text-indigo-400 mb-6">{t.latency} (ms)</h3>
                 <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                       <AreaChart data={data}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '12px' }}
                            itemStyle={{ color: '#fff' }}
                          />
                          <Area type="monotone" dataKey="value" stroke="#6366f1" fill="rgba(99,102,241,0.1)" strokeWidth={3} />
                       </AreaChart>
                    </ResponsiveContainer>
                 </div>
              </div>
              <div className="p-8 bg-slate-900 rounded-[3rem] border border-white/5">
                 <h3 className="text-sm font-black uppercase tracking-widest text-indigo-400 mb-6">{t.distribution}</h3>
                 <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                       <BarChart data={data}>
                          <Bar dataKey="active">
                             {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.load > 85 ? '#f43f5e' : '#6366f1'} />
                             ))}
                          </Bar>
                       </BarChart>
                    </ResponsiveContainer>
                 </div>
              </div>
           </div>
        </div>

        {/* Sidebar Alerts / Intelligence */}
        <div className="space-y-8">
           <div className="p-8 bg-indigo-600 rounded-[3rem] text-white shadow-2xl shadow-indigo-900/20 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
              <div className="relative z-10">
                 <div className="flex items-center gap-3 mb-8">
                    <div className="p-2 bg-white/20 rounded-xl">
                       <Zap size={24} />
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-[0.3em]">Cluster Alert</span>
                 </div>
                 <h3 className="text-2xl font-black mb-4 leading-tight">Critical Resource Depletion: Zone C</h3>
                 <p className="text-sm text-indigo-100 font-medium mb-8 leading-relaxed opacity-80">
                   Supply chain heuristics predict reagent exhaustion in the Basrah cluster within 36 hours. Auto-routing active.
                 </p>
                 <div className="pt-4">
                    <button className="w-full py-4 bg-white text-indigo-600 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-[1.02] transition-transform shadow-xl">
                        Override Logistics
                    </button>
                 </div>
              </div>
           </div>

           <div className="p-8 bg-white/5 border border-white/5 rounded-[3rem] space-y-6">
              <h3 className="text-sm font-black uppercase tracking-widest text-indigo-400">{t.nodeStatus}</h3>
              {[
                { id: '1', title: 'Nineveh Hub Offline for Neural Update', time: '2m ago', type: 'info' },
                { id: '2', title: 'Unauthorized API Access Detected', time: '12m ago', type: 'alert' },
                { id: '3', title: 'New Lab Cluster Integrated: Erbil East', time: '1h ago', type: 'success' },
                { id: '4', title: 'Data Sovereignty Audit Complete', time: '3h ago', type: 'info' },
              ].map(item => (
                <div key={item.id} className="flex gap-4 group cursor-pointer p-2 hover:bg-white/5 rounded-2xl transition-all">
                   <div className={cn(
                     "w-10 h-10 rounded-xl shrink-0 flex items-center justify-center border",
                     item.type === 'alert' ? "bg-rose-500/10 border-rose-500/20 text-rose-400 group-hover:scale-110" : "bg-white/5 border-white/10 text-slate-400"
                   )}>
                      <Activity size={18} />
                   </div>
                   <div className="min-w-0">
                      <p className="text-[10px] font-black text-white uppercase tracking-tight truncate leading-tight mb-1">{item.title}</p>
                      <div className="flex items-center gap-2">
                         <span className="text-[8px] font-bold text-slate-500 tracking-wider font-mono">{item.time}</span>
                         <div className="w-1 h-1 rounded-full bg-slate-700" />
                         <span className="text-[8px] font-bold text-indigo-400 uppercase tracking-widest">Protocol V4</span>
                      </div>
                   </div>
                </div>
              ))}
              <button className="w-full py-3 text-[10px] font-black text-indigo-400 uppercase tracking-widest hover:bg-white/5 rounded-xl transition-all mt-4">
                 Full System Audit
              </button>
           </div>

           <div className="p-8 bg-emerald-600/10 border border-emerald-500/20 rounded-[3rem] text-center">
              <div className="w-16 h-16 bg-emerald-500 text-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-xl shadow-emerald-500/20">
                 <Shield size={32} />
              </div>
              <h3 className="text-lg font-black text-white mb-2">{t.trustScore}</h3>
              <p className="text-3xl font-black text-emerald-400 mb-2">99.8%</p>
              <div className="flex items-center justify-center gap-1">
                 <ArrowUpRight size={14} className="text-emerald-400" />
                 <span className="text-[8px] font-black uppercase text-emerald-400/60">+0.2% vs Last Quarter</span>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
