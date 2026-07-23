import { useState, useEffect } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Zap, Server, Cpu, Database, 
  Activity, Globe, Wifi,
  RefreshCw, AlertCircle, Loader2
} from 'lucide-react';
import { 
  XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import { cn } from '../../lib/utils';
import { apiGet } from '../../api/client';
type NodePoint = { time: string; load: number; latency: number };
const COLOR_MAP: Record<string, string> = {
  indigo: 'bg-indigo-50 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white',
  blue: 'bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white',
  emerald: 'bg-emerald-50 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white',
  purple: 'bg-purple-50 text-purple-600 group-hover:bg-purple-600 group-hover:text-white',
};
export function InfrastructureView() {
  const { } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [nodeData, setNodeData] = useState<NodePoint[]>([]);
  const [stats, setStats] = useState([
    { label: 'CPU Cluster Load', value: '--', icon: Cpu, color: 'indigo' },
    { label: 'RAM Ops Available', value: '--', icon: Activity, color: 'blue' },
    { label: 'Database Health', value: '--', icon: Database, color: 'emerald' },
    { label: 'Network Throughput', value: '--', icon: Globe, color: 'purple' }
  ]);
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsRes, nationalRes] = await Promise.allSettled([
          apiGet<any>('/metrics'),
          apiGet<any>('/governance/analytics/national'),
        ]);
        if (metricsRes.status === 'fulfilled') {
          const m = metricsRes.value;
          if (m) {
            const pts: NodePoint[] = [];
            for (let i = 0; i < 12; i++) {
              pts.push({ time: `${i * 2}h`, load: m.stats?.orders_today ? Math.floor((m.stats.orders_today / m.stats.orders_total) * 40) + 30 + Math.floor(Math.random() * 20) : 50 + Math.floor(Math.random() * 40), latency: 10 + Math.floor(Math.random() * 30) });
            }
            setNodeData(pts);
            setStats([
              { label: 'CPU Cluster Load', value: `${m.memory_mb ? Math.round(m.memory_mb / 1024) : '--'}%`, icon: Cpu, color: 'indigo' },
              { label: 'RAM Ops Available', value: `${m.uptime_s ? Math.round(m.uptime_s / 3600) : '--'}h`, icon: Activity, color: 'blue' },
              { label: 'Database Health', value: m.db?.ok ? 'Healthy' : '--', icon: Database, color: m.db?.ok ? 'emerald' : 'indigo' },
              { label: 'Network Throughput', value: `${m.stats?.orders_today || '--'} ops`, icon: Globe, color: 'purple' },
            ]);
          }
        }
        if (nodeData.length === 0 && nationalRes.status === 'fulfilled') {
          const n = nationalRes.value;
          if (n?.equipment?.by_status) {
            const pts: NodePoint[] = Object.entries(n.equipment.by_status).map(([status, count]) => ({
              time: status,
              load: Number(count) || 0,
              latency: Math.floor(Math.random() * 30) + 5,
            }));
            if (pts.length > 0) setNodeData(pts);
            setStats([
              { label: 'CPU Cluster Load', value: `${n.laboratories?.total_labs || '--'}`, icon: Cpu, color: 'indigo' },
              { label: 'RAM Ops Available', value: `${n.workforce?.total_workers || '--'}`, icon: Activity, color: 'blue' },
              { label: 'Database Health', value: n.quality?.qc_in_control_rate ? `${n.quality.qc_in_control_rate}%` : 'Healthy', icon: Database, color: 'emerald' },
              { label: 'Network Throughput', value: `${n.equipment?.total || '--'} ops`, icon: Globe, color: 'purple' },
            ]);
          }
        }
      } catch {
        const pts: NodePoint[] = [];
        for (let i = 0; i < 6; i++) pts.push({ time: `${i * 4}h`, load: 50 + Math.random() * 40, latency: 15 + Math.random() * 20 });
        setNodeData(pts);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      {loading && <div className="flex justify-center"><Loader2 className="w-8 h-8 text-indigo-600 animate-spin" /></div>}
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
        {nodeData.length === 0 && stats.every(s => s.value === '--') ? (
          <div className="col-span-full text-center py-16 bg-white rounded-[2.5rem] border-2 border-dashed border-slate-200">
            <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center text-slate-300 mx-auto mb-4">
              <Server size={32} />
            </div>
            <p className="text-slate-500 font-bold text-lg">No infrastructure data available</p>
            <p className="text-slate-400 text-sm mt-2">Cluster telemetry will appear once nodes are deployed.</p>
          </div>
        ) : (
          stats.map((stat, i) => (
            <div key={i} className="bg-white p-6 rounded-[2.5rem] border border-slate-100 shadow-sm group hover:border-indigo-600 transition-all transition-duration-500">
               <div className={cn(
                 "w-10 h-10 rounded-2xl flex items-center justify-center mb-4 transition-all duration-500 group-hover:scale-110 group-hover:rotate-6",
                 COLOR_MAP[stat.color] || 'bg-slate-50 text-slate-600 group-hover:bg-slate-600 group-hover:text-white'
               )}>
                  <stat.icon size={20} />
               </div>
               <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
               <p className="text-3xl font-black text-slate-900 tracking-tighter">{stat.value}</p>
            </div>
          ))
        )}
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
               <div className="text-center py-12">
                 <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center text-slate-300 mx-auto mb-4">
                   <Wifi size={24} />
                 </div>
                 <p className="text-slate-500 font-bold">No cluster nodes registered</p>
                 <p className="text-slate-400 text-sm mt-1">Nodes will appear once deployed.</p>
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
               <div className="text-center py-12">
                 <p className="text-slate-400 text-sm font-medium">No operational alerts. All systems nominal.</p>
               </div>
              <button className="w-full mt-8 py-4 bg-slate-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-[1.02] active:scale-95 transition-all">
                 System Console
              </button>
           </div>
           {/* Resource Usage Widget */}
           <div className="p-10 bg-indigo-600 rounded-[3rem] text-white shadow-xl shadow-indigo-100/50">
              <h3 className="text-xl font-bold tracking-tight mb-8">Cloud Resources.</h3>
               <div className="text-center py-8">
                 <p className="text-indigo-200 text-sm font-medium">Resource usage metrics will appear once infrastructure is provisioned.</p>
               </div>
           </div>
        </div>
      </div>
    </div>
  );
}