import React from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Zap, Server, Cpu, Database, 
  Activity, ShieldCheck, Globe, Wifi,
  HardDrive, Monitor, RefreshCw, AlertCircle
} from 'lucide-react';
import { motion } from 'motion/react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import { cn } from '../../lib/utils';

const nodeData = [
  { time: '00:00', load: 32, latency: 45 },
  { time: '04:00', load: 28, latency: 42 },
  { time: '08:00', load: 65, latency: 85 },
  { time: '12:00', load: 88, latency: 120 },
  { time: '16:00', load: 74, latency: 95 },
  { time: '20:00', load: 45, latency: 55 },
  { time: '23:59', load: 38, latency: 48 },
];

export function InfrastructureView() {
  const { t } = useLanguage();

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
             <div className="p-2 bg-slate-900 rounded-xl text-white">
                <Server size={24} />
             </div>
             <h1 className="text-4xl font-black text-slate-900 tracking-tight uppercase italic underline decoration-indigo-600/30 underline-offset-8">GULA Infrastructure.</h1>
          </div>
          <p className="text-sm text-slate-500 font-medium tracking-tight">Enterprise node cluster health and decentralized ledger integrity.</p>
        </div>
        
        <div className="flex items-center gap-4 bg-white p-3 rounded-2xl border border-slate-100 shadow-sm">
           <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-600 rounded-xl">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
              <span className="text-[10px] font-black uppercase tracking-widest">Global Status: Healthy</span>
           </div>
           <button className="p-2 hover:bg-slate-50 rounded-xl transition-colors">
              <RefreshCw size={18} className="text-slate-400" />
           </button>
        </div>
      </div>

      {/* Cluster Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'CPU Cluster Load', value: '42.8%', icon: Cpu, color: 'indigo' },
          { label: 'RAM Ops Available', value: '128 GB', icon: Activity, color: 'blue' },
          { label: 'Database Health', value: '99.99%', icon: Database, color: 'emerald' },
          { label: 'Network Throughput', value: '2.4 Gbps', icon: Globe, color: 'purple' }
        ].map((stat, i) => (
          <div key={i} className="bg-white p-6 rounded-[2.5rem] border border-slate-100 shadow-sm group hover:border-indigo-600 transition-all transition-duration-500">
             <div className={cn(
               "w-10 h-10 rounded-2xl flex items-center justify-center mb-4 transition-all duration-500 group-hover:scale-110 group-hover:rotate-6",
               `bg-${stat.color}-50 text-${stat.color}-600 group-hover:bg-${stat.color}-600 group-hover:text-white`
             )}>
                <stat.icon size={20} />
             </div>
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
             <p className="text-3xl font-black text-slate-900 tracking-tighter">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
           {/* Real-time Performance Card */}
           <div className="p-8 bg-slate-900 rounded-[3rem] text-white shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-12 opacity-5 rotate-12 scale-150 transition-transform duration-1000 group-hover:rotate-0">
                 <Zap size={200} />
              </div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-8">
                   <div>
                      <h2 className="text-2xl font-black tracking-tight italic">Compute Performance</h2>
                      <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">Aggregate node stress test - Sector Delta</p>
                   </div>
                   <div className="flex items-center gap-6">
                      <div className="flex gap-4">
                         <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-indigo-500" />
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Load</span>
                         </div>
                         <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-emerald-500" />
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Latency</span>
                         </div>
                      </div>
                      <div className="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-lg">
                         <Activity size={14} className="text-indigo-400" />
                         <span className="text-[10px] font-black uppercase tracking-widest">Realtime Feed</span>
                      </div>
                   </div>
                </div>
                <div className="h-[300px] w-full">
                   <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={nodeData}>
                         <defs>
                            <linearGradient id="colorLoad" x1="0" y1="0" x2="0" y2="1">
                               <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                               <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                            </linearGradient>
                         </defs>
                         <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                         <XAxis 
                           dataKey="time" 
                           axisLine={false} 
                           tickLine={false} 
                           tick={{ fontSize: 10, fontWeight: 900, fill: '#475569' }} 
                         />
                         <YAxis 
                           axisLine={false} 
                           tickLine={false} 
                           tick={{ fontSize: 10, fontWeight: 900, fill: '#475569' }} 
                         />
                         <Tooltip 
                            contentStyle={{ borderRadius: '24px', border: 'none', backgroundColor: '#0f172a', color: '#fff', boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.5)' }} 
                         />
                         <Area type="monotone" dataKey="load" stroke="#6366f1" strokeWidth={4} fillOpacity={1} fill="url(#colorLoad)" />
                         <Area type="monotone" dataKey="latency" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" fill="none" />
                      </AreaChart>
                   </ResponsiveContainer>
                </div>
              </div>
           </div>

           {/* Infrastructure Nodes */}
           <div className="bg-white border border-slate-100 rounded-[3rem] p-8 shadow-sm overflow-hidden">
              <h3 className="text-xl font-bold text-slate-900 tracking-tight mb-8">Cluster Node Registry.</h3>
              <div className="space-y-4">
                {[
                  { id: 'NODE-01', location: 'Frankfurt Central', type: 'Primary Ledger', uptime: '482d 12h', health: 100 },
                  { id: 'NODE-02', location: 'Erbil Science Park', type: 'Clinical Proxy', uptime: '12d 4h', health: 94 },
                  { id: 'NODE-03', location: 'Dubai Cloud Hub', type: 'Regional Storage', uptime: '88d 19h', health: 100 },
                  { id: 'NODE-04', location: 'London Bio-Bridge', type: 'Research Node', uptime: '142d 2h', health: 100 }
                ].map(node => (
                  <div key={node.id} className="p-6 bg-slate-50/50 border border-slate-100 rounded-[2rem] flex items-center justify-between group hover:bg-white hover:shadow-xl transition-all duration-300">
                     <div className="flex items-center gap-6">
                        <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-slate-400 group-hover:text-indigo-600 transition-colors shadow-sm">
                           <Wifi size={24} />
                        </div>
                        <div>
                           <p className="text-sm font-black text-slate-900">{node.id}</p>
                           <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{node.location} • {node.type}</p>
                        </div>
                     </div>
                     <div className="flex items-center gap-12">
                        <div className="hidden md:block">
                           <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest mb-1">Lifetime Uptime</p>
                           <p className="text-xs font-black text-slate-700">{node.uptime}</p>
                        </div>
                        <div className="flex flex-col items-end">
                           <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest mb-1">Integrity</p>
                           <div className="flex items-center gap-2">
                             <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                <div className={cn("h-full rounded-full", node.health > 95 ? "bg-emerald-500" : "bg-amber-500")} style={{ width: `${node.health}%` }} />
                             </div>
                             <span className="text-[10px] font-black text-slate-900">{node.health}%</span>
                           </div>
                        </div>
                     </div>
                  </div>
                ))}
              </div>
           </div>
        </div>

        <div className="space-y-8">
           {/* Security Event Log */}
           <div className="p-8 bg-white border border-slate-100 rounded-[3rem] shadow-sm">
              <div className="flex items-center justify-between mb-8">
                 <h3 className="text-lg font-black text-slate-900 uppercase tracking-tight">Ops Alert Feed.</h3>
                 <AlertCircle size={20} className="text-red-500" />
              </div>
              <div className="space-y-6">
                 {[
                   { event: 'DDoS Mitigation', time: '4m ago', status: 'Blocked', color: 'bg-emerald-50 text-emerald-600' },
                   { event: 'DB Migration Complete', time: '12m ago', status: 'Success', color: 'bg-indigo-50 text-indigo-600' },
                   { event: 'High Latency Detect', time: '41m ago', status: 'Investigating', color: 'bg-amber-50 text-amber-600' },
                   { event: 'API Key Rotation', time: '2h ago', status: 'Verified', color: 'bg-emerald-50 text-emerald-600' }
                 ].map((log, i) => (
                   <div key={i} className="flex flex-col gap-2 p-4 border border-slate-50 rounded-2xl hover:bg-slate-50 transition-colors">
                      <div className="flex items-center justify-between">
                         <p className="text-xs font-black text-slate-900 tracking-tight">{log.event}</p>
                         <span className="text-[9px] font-bold text-slate-400">{log.time}</span>
                      </div>
                      <div className={cn("inline-block w-fit px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest", log.color)}>
                         {log.status}
                      </div>
                   </div>
                 ))}
              </div>
              <button className="w-full mt-8 py-4 bg-slate-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-[1.02] active:scale-95 transition-all">
                 System Console
              </button>
           </div>

           {/* Resource Usage Widget */}
           <div className="p-10 bg-indigo-600 rounded-[3rem] text-white shadow-xl shadow-indigo-100/50">
              <h3 className="text-xl font-bold tracking-tight mb-8">Cloud Resources.</h3>
              <div className="space-y-8">
                 {[
                   { label: 'Object Storage', used: '4.2 TB', total: '10 TB', percentage: 42 },
                   { label: 'Analytical Compute', used: '18 Nodes', total: '24 Nodes', percentage: 75 },
                   { label: 'Ledger Ledger', used: '1.2 GB', total: '5 GB', percentage: 24 }
                 ].map((res, i) => (
                   <div key={i}>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-[10px] font-black text-indigo-200 uppercase tracking-widest">{res.label}</p>
                        <p className="text-[10px] font-bold">{res.used} / {res.total}</p>
                      </div>
                      <div className="h-2 w-full bg-indigo-500 rounded-full overflow-hidden">
                         <motion.div 
                           initial={{ width: 0 }}
                           animate={{ width: `${res.percentage}%` }}
                           transition={{ duration: 1, delay: i * 0.2 }}
                           className="h-full bg-white rounded-full shadow-[0_0_10px_rgba(255,255,255,0.5)]" 
                         />
                      </div>
                   </div>
                 ))}
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
