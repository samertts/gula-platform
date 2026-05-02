import React from 'react';
import { motion } from 'motion/react';
import { Network, Activity, Zap, Shield, Database, LayoutGrid, ArrowUpRight, Cpu, AlertTriangle, Users } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function MinistryCommandCenter() {
  const { t } = useLanguage();

  const metrics = [
    { label: t.slaTracking, value: '99.94%', status: 'Nominal', icon: Activity, color: 'text-emerald-500' },
    { label: t.workQueueOpt, value: 'AI Active', status: 'Optimizing', icon: Zap, color: 'text-indigo-500' },
    { label: t.populationForecasting, value: 'Stable', status: 'Next 30d', icon: Users, color: 'text-amber-500' },
    { label: t.apiMarketplace, value: '142 Apps', status: 'Connected', icon: Database, color: 'text-rose-500' },
  ];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((m, i) => (
          <motion.div 
            key={m.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-8 bg-white border border-slate-100 rounded-[2.5rem] shadow-sm hover:shadow-md transition-shadow group"
          >
            <div className="flex justify-between items-start mb-6">
               <div className={cn("p-3 rounded-2xl bg-slate-50 group-hover:bg-indigo-50 transition-colors", m.color.replace('text', 'bg').replace('500', '100'))}>
                  <m.icon size={24} className={m.color} />
               </div>
               <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">{m.status}</span>
            </div>
            <h4 className="text-xs font-black uppercase tracking-widest text-slate-500 mb-1">{m.label}</h4>
            <p className="text-2xl font-black text-slate-900 tracking-tight">{m.value}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
         <div className="lg:col-span-8 bg-slate-900 rounded-[3rem] p-10 text-white relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-12 opacity-5 scale-150 rotate-12 transition-transform group-hover:scale-125">
               <Cpu size={300} />
            </div>
            <div className="relative z-10">
               <div className="flex justify-between items-start mb-12">
                  <div>
                     <h3 className="text-2xl font-black uppercase tracking-tight">{t.autonomousEcosystem} Control</h3>
                     <p className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mt-1">Autonomous Grid Management Engine v4.2</p>
                  </div>
                  <div className="flex items-center gap-3 px-4 py-2 bg-white/5 border border-white/10 rounded-xl">
                     <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
                     <span className="text-[10px] font-black tracking-widest uppercase">Ecosystem: Balanced</span>
                  </div>
               </div>

               <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                  {[
                    { label: 'Hospital Resource AI', val: 'Allocated', sub: '92% Efficiency' },
                    { label: 'Supply Chain Nodes', val: 'Synchronized', sub: 'No Disruptions' },
                    { label: 'Incident Response', val: 'Auto-Pilot', sub: '0 Crits' },
                  ].map((node, i) => (
                    <div key={i} className="p-6 bg-white/5 border border-white/5 rounded-3xl hover:bg-white/10 transition-all">
                       <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">{node.label}</p>
                       <h4 className="text-lg font-bold text-white leading-tight mb-1">{node.val}</h4>
                       <p className="text-[9px] font-medium text-indigo-400 uppercase tracking-widest">{node.sub}</p>
                    </div>
                  ))}
               </div>

               <div className="flex items-center justify-between p-8 bg-indigo-600 rounded-3xl shadow-xl shadow-indigo-900/50">
                  <div className="flex items-center gap-6">
                     <div className="p-4 bg-white/10 rounded-2xl">
                        <AlertTriangle size={28} className="text-amber-400" />
                     </div>
                     <div>
                        <h4 className="text-lg font-black uppercase tracking-tight">Active Policy Guard</h4>
                        <p className="text-xs text-indigo-100 opacity-80">Autonomous intervention required in Node B-14 (Delayed Pathology SLA).</p>
                     </div>
                  </div>
                  <button className="px-8 py-4 bg-white text-indigo-600 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-lg">
                     Authorize Intervention
                  </button>
               </div>
            </div>
         </div>

         <div className="lg:col-span-4 bg-white border border-slate-100 rounded-[3rem] p-10 flex flex-col justify-between">
            <div>
               <h3 className="text-xl font-black uppercase tracking-tight text-slate-900 mb-2">{t.apiMarketplace}</h3>
               <p className="text-xs text-slate-400 font-medium leading-relaxed">
                  Monitor decentralized health applications and external data streams connecting to the National Health Grid.
               </p>
            </div>
            
            <div className="space-y-6 my-10">
               {[
                 { name: 'OncoAI Diagnostics', sync: '1.2s', status: 'Certified' },
                 { name: 'Basrah Public Health Monitor', sync: '0.4s', status: 'Certified' },
                 { name: 'National Pharmacy Grid', sync: '0.1s', status: 'Certified' },
               ].map((app, i) => (
                 <div key={i} className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100">
                    <div>
                       <p className="text-xs font-black text-slate-800">{app.name}</p>
                       <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Sync: {app.sync}</p>
                    </div>
                    <span className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">{app.status}</span>
                 </div>
               ))}
            </div>

            <button className="w-full py-4 bg-slate-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-slate-800 transition-all flex items-center justify-center gap-2 group">
               Access Marketplace Portal <ArrowUpRight size={14} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
            </button>
         </div>
      </div>
    </div>
  );
}
