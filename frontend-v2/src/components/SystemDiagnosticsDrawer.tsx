import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Server, Activity, Database, Cpu, Globe, Zap, ShieldCheck } from 'lucide-react';
import { cn } from '../lib/utils';
import { useLanguage } from '../contexts/LanguageContext';

interface NodeStatus {
  id: string;
  name: string;
  status: 'online' | 'warning' | 'offline';
  load: number;
}

const NODES: NodeStatus[] = [
  { id: 'BG-01', name: 'Baghdad Backbone', status: 'online', load: 82 },
  { id: 'BA-04', name: 'Basrah Relational', status: 'online', load: 45 },
  { id: 'NI-07', name: 'Nineveh Analyzer', status: 'warning', load: 94 },
  { id: 'ER-02', name: 'Erbil Bio-Grid', status: 'online', load: 61 },
  { id: 'ST-09', name: 'Sovereign Storage', status: 'online', load: 12 },
];

export function SystemDiagnosticsDrawer({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
  const { isRtl } = useLanguage();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[70]"
          />
          <motion.div
            initial={{ x: isRtl ? '-100%' : '100%' }}
            animate={{ x: 0 }}
            exit={{ x: isRtl ? '-100%' : '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={cn(
              "fixed top-0 bottom-0 w-full max-w-md bg-white shadow-2xl z-[80] overflow-hidden flex flex-col",
              isRtl ? "left-0" : "right-0"
            )}
          >
            <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-slate-900 rounded-2xl flex items-center justify-center text-white">
                   <Activity size={24} className="animate-pulse" />
                </div>
                <div>
                   <h3 className="text-xl font-black uppercase tracking-tight text-slate-900">Bio-Grid Pulse</h3>
                   <p className="text-[10px] font-black text-indigo-600 uppercase tracking-widest">Global Diagnostics v12.4</p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="p-3 hover:bg-slate-200 rounded-2xl transition-all"
              >
                <X size={24} className="text-slate-400" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
              {/* Global Health Section */}
              <div className="space-y-4">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">Operational Health</h4>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Latency', value: '14ms', icon: Database, color: 'text-indigo-600' },
                    { label: 'Uptime', value: '99.99%', icon: Globe, color: 'text-emerald-500' },
                    { label: 'Traffic', value: '4.2 TB/s', icon: Zap, color: 'text-rose-500' },
                    { label: 'Nodes', value: '1,204', icon: Server, color: 'text-slate-900' },
                  ].map((stat, i) => (
                    <div key={i} className="p-5 bg-slate-50 border border-slate-100 rounded-[2rem] group hover:bg-white hover:shadow-xl transition-all">
                       <stat.icon size={18} className={cn("mb-3", stat.color)} />
                       <div className="text-lg font-black text-slate-900">{stat.value}</div>
                       <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{stat.label}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Individual Node Status */}
              <div className="space-y-4">
                 <div className="flex items-center justify-between">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">Backbone Nodes</h4>
                    <span className="text-[9px] font-black text-emerald-500 uppercase tracking-widest flex items-center gap-1"><div className="w-1 h-1 bg-emerald-500 rounded-full animate-pulse" /> All Secure</span>
                 </div>
                 <div className="space-y-2">
                    {NODES.map((node) => (
                      <div key={node.id} className="p-4 bg-white border border-slate-100 rounded-2xl flex items-center gap-4 group hover:bg-slate-50 transition-colors">
                         <div className={cn(
                           "w-10 h-10 rounded-xl flex items-center justify-center",
                           node.status === 'online' ? "bg-emerald-50 text-emerald-600" :
                           node.status === 'warning' ? "bg-amber-50 text-amber-600" : "bg-rose-50 text-rose-600"
                         )}>
                            <Cpu size={18} />
                         </div>
                         <div className="flex-1">
                            <div className="flex justify-between items-center mb-1">
                               <span className="text-xs font-bold text-slate-900">{node.name}</span>
                               <span className="text-[10px] font-black text-slate-400">{node.load}%</span>
                            </div>
                            <div className="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                               <motion.div 
                                 initial={{ width: 0 }}
                                 animate={{ width: `${node.load}%` }}
                                 className={cn(
                                   "h-full",
                                   node.load > 90 ? "bg-rose-500" : node.load > 70 ? "bg-amber-500" : "bg-indigo-500"
                                 )}
                               />
                            </div>
                         </div>
                         <div className="text-[9px] font-black uppercase text-slate-300 group-hover:text-slate-900 transition-colors">{node.id}</div>
                      </div>
                    ))}
                 </div>
              </div>

              {/* Security Status */}
              <div className="p-6 bg-slate-900 rounded-[2.5rem] text-white overflow-hidden relative group">
                 <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 transition-transform">
                   <ShieldCheck size={100} />
                 </div>
                 <div className="relative z-10">
                    <h4 className="text-xs font-black uppercase tracking-widest text-indigo-400 mb-2">Security Perimeter</h4>
                    <p className="text-sm font-medium leading-relaxed opacity-80">Quantum-resistant encryption is active across all regional data transfer paths. Sovereign data sovereignty is verified.</p>
                 </div>
              </div>
            </div>

            <div className="p-8 border-t border-slate-100 bg-slate-50/30">
               <button className="w-full py-5 bg-indigo-600 text-white rounded-[2rem] font-black text-xs uppercase tracking-[0.2em] shadow-2xl shadow-indigo-100 hover:scale-[1.02] active:scale-95 transition-all">
                  Initiate Deep Scan
               </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
