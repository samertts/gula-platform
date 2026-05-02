import React from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  TrendingUp, Users, Activity, ShieldCheck, Zap,
  Map as MapIcon, BrainCircuit, Search, Download,
  Filter, Calendar
} from 'lucide-react';
import { motion } from 'motion/react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { cn } from '../../lib/utils';

const data = [
  { name: 'Jan', glucose: 4000, infection: 2400, cholesterol: 2400 },
  { name: 'Feb', glucose: 3000, infection: 1398, cholesterol: 2210 },
  { name: 'Mar', glucose: 2000, infection: 9800, cholesterol: 2290 },
  { name: 'Apr', glucose: 2780, infection: 3908, cholesterol: 2000 },
  { name: 'May', glucose: 1890, infection: 4800, cholesterol: 2181 },
  { name: 'Jun', glucose: 2390, infection: 3800, cholesterol: 2500 },
];

export function ResearcherDashboard() {
  const { t, dir } = useLanguage();
  const isRtl = dir === 'rtl';

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
             <div className="p-2 bg-indigo-600 rounded-xl text-white">
                <BrainCircuit size={24} />
             </div>
             <h1 className="text-4xl font-black text-slate-900 tracking-tight uppercase">Population Intelligence</h1>
          </div>
          <p className="text-sm text-slate-500 font-medium tracking-tight">AI-driven epidemiological trends and health pattern surveillance.</p>
        </div>
        
        <div className="flex items-center gap-3 bg-white p-2 rounded-2xl border border-slate-100 shadow-sm">
           <button className="px-4 py-2 bg-slate-50 text-slate-600 rounded-xl text-xs font-bold hover:bg-slate-100 transition-colors flex items-center gap-2">
             <Calendar size={14} />
             Last 30 Days
           </button>
           <button className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-100 hover:scale-105 transition-transform flex items-center gap-2">
             <Download size={14} />
             Export Data
           </button>
        </div>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Total Scanned Records', value: '42.8k', trend: '+12%', icon: Users, color: 'indigo' },
          { label: 'Diagnostic Accuracy', value: '99.4%', trend: '+0.2%', icon: Activity, color: 'emerald' },
          { label: 'Regional Alerts', value: '24', trend: '-14%', icon: ShieldCheck, color: 'amber' },
          { label: 'Active Researchers', value: '182', trend: '+5%', icon: TrendingUp, color: 'blue' }
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-6 bg-white border border-slate-100 rounded-[2.5rem] shadow-sm hover:shadow-xl hover:scale-[1.02] transition-all group"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={cn(
                "p-3 rounded-2xl transition-colors",
                `bg-${stat.color}-50 text-${stat.color}-600 group-hover:bg-${stat.color}-600 group-hover:text-white`
              )}>
                <stat.icon size={20} />
              </div>
              <span className="text-[10px] font-black text-emerald-500 bg-emerald-50 px-2 py-1 rounded-full uppercase tracking-widest">{stat.trend}</span>
            </div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
            <p className="text-3xl font-black text-slate-900">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
           {/* Main Trend Line Chart */}
            <div className="p-8 bg-white border border-slate-100 rounded-[3rem] shadow-sm relative group">
              <div className="absolute top-8 right-8 flex gap-2">
                 <button className="p-2 bg-slate-50 text-slate-400 rounded-xl hover:bg-indigo-50 hover:text-indigo-600 transition-all opacity-0 group-hover:opacity-100">
                    <TrendingUp size={16} />
                 </button>
                 <button className="p-2 bg-slate-50 text-slate-400 rounded-xl hover:bg-indigo-50 hover:text-indigo-600 transition-all opacity-0 group-hover:opacity-100">
                    <Zap size={16} />
                 </button>
              </div>
              <div className="flex items-center justify-between mb-8">
                 <div>
                    <h2 className="text-xl font-bold text-slate-900 tracking-tight">Clinical Trends (AI Forecast)</h2>
                    <p className="text-xs text-slate-400 font-bold uppercase tracking-widest mt-1">Cross-sectional analysis of lab indicators</p>
                 </div>
                 <div className="hidden sm:flex gap-2 mr-16">
                    <div className="flex items-center gap-2">
                       <div className="w-2 h-2 rounded-full bg-indigo-500" />
                       <span className="text-[10px] font-bold text-slate-500 uppercase">Glucose</span>
                    </div>
                    <div className="flex items-center gap-2">
                       <div className="w-2 h-2 rounded-full bg-emerald-500" />
                       <span className="text-[10px] font-bold text-slate-500 uppercase">Infections</span>
                    </div>
                 </div>
              </div>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data}>
                    <defs>
                      <linearGradient id="colorGlucose" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorInfection" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis 
                       dataKey="name" 
                       axisLine={false} 
                       tickLine={false} 
                       tick={{ fontSize: 10, fontWeight: 700, fill: '#94a3b8' }} 
                    />
                    <YAxis 
                       axisLine={false} 
                       tickLine={false} 
                       tick={{ fontSize: 10, fontWeight: 700, fill: '#94a3b8' }} 
                    />
                    <Tooltip 
                      cursor={{ stroke: '#6366f1', strokeWidth: 1, strokeDasharray: '4 4' }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-slate-900 text-white p-4 rounded-2xl shadow-2xl border border-white/10 min-w-[150px]">
                               <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">{payload[0].payload.name} 2024</p>
                               {payload.map((p: any, i: number) => (
                                 <div key={i} className="flex items-center justify-between gap-4 mb-1">
                                    <span className="text-xs font-bold" style={{ color: p.color }}>{p.name}</span>
                                    <span className="text-sm font-black">{p.value.toLocaleString()}</span>
                                 </div>
                               ))}
                               <div className="mt-2 pt-2 border-t border-white/5 flex items-center gap-2">
                                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                                  <span className="text-[8px] font-bold text-indigo-400 uppercase tracking-widest">Confidence 98.4%</span>
                               </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Area type="monotone" dataKey="glucose" name="Avg. Glucose" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorGlucose)" />
                    <Area type="monotone" dataKey="infection" name="Infection Rate" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorInfection)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

           {/* Distribution Bar Chart */}
           <div className="p-8 bg-slate-900 rounded-[3rem] text-white overflow-hidden relative group">
             <div className="absolute top-0 right-0 p-12 opacity-5 scale-150 rotate-12 group-hover:rotate-0 transition-transform duration-1000">
                <BrainCircuit size={200} />
             </div>
             <div className="relative z-10">
               <div className="flex items-center justify-between mb-8">
                  <div>
                     <h2 className="text-xl font-bold tracking-tight">Regional Distribution</h2>
                     <p className="text-xs text-slate-400 font-bold uppercase tracking-widest mt-1">Samples by demographic sectors</p>
                  </div>
               </div>
               <div className="h-[250px] w-full">
                 <ResponsiveContainer width="100%" height="100%">
                   <BarChart data={data}>
                     <Bar dataKey="cholesterol" fill="#6366f1" radius={[10, 10, 0, 0]} />
                     <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 700, fill: '#64748b' }} />
                   </BarChart>
                 </ResponsiveContainer>
               </div>
             </div>
           </div>
        </div>

        <div className="space-y-8">
           {/* AI Insight Card */}
           <div className="p-8 bg-indigo-600 rounded-[3rem] text-white shadow-xl shadow-indigo-100">
              <div className="flex items-center gap-3 mb-6">
                 <div className="p-2 bg-indigo-500 rounded-xl">
                    <Activity size={20} />
                 </div>
                 <span className="text-[10px] font-black uppercase tracking-[0.2em]">AI Intelligence</span>
              </div>
              <h3 className="text-2xl font-bold tracking-tight leading-tight mb-4 text-indigo-50">Emerging Anomaly Detected: Zone B-12</h3>
              <p className="text-sm text-indigo-100 leading-relaxed font-medium mb-6">
                Statistical correlation suggests a 15% rise in respiratory biomarkers across Northern sectors. Recommend immediate audit of environmental data.
              </p>
              <button className="w-full py-4 bg-white text-indigo-600 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 transition-transform">
                Initiate Analysis
              </button>
           </div>

           {/* Watchlist */}
           <div className="p-8 bg-white border border-slate-100 rounded-[3rem] shadow-sm">
             <h3 className="text-lg font-black text-slate-900 uppercase tracking-tight mb-6">Surveillance Feed</h3>
             <div className="space-y-6">
               {[
                 { id: 'AN-01', type: 'Viral Load', area: 'Urban A', status: 'Stable', time: '14m ago' },
                 { id: 'AN-02', type: 'Pathogen-X', area: 'Sector 4', status: 'Elevated', time: '1h ago', pulse: true },
                 { id: 'AN-03', type: 'Water Toxins', area: 'Coastline', status: 'Normal', time: '3h ago' }
               ].map((item) => (
                 <div key={item.id} className="flex items-center gap-4 group cursor-pointer p-2 hover:bg-slate-50 transition-colors rounded-2xl px-2 -mx-2">
                    <div className={cn(
                      "w-10 h-10 rounded-2xl flex items-center justify-center border transition-all",
                      item.pulse ? "bg-amber-50 border-amber-100 text-amber-600 animate-pulse shadow-[0_0_15px_rgba(245,158,11,-0.2)]" : "bg-slate-50 border-slate-100 text-slate-400"
                    )}>
                      {item.pulse ? <ShieldCheck size={18} /> : <Search size={18} />}
                    </div>
                    <div className="flex-1 min-w-0">
                       <div className="flex items-center justify-between">
                          <p className="text-xs font-black text-slate-900 uppercase tracking-tight truncate">{item.type}</p>
                          <span className="text-[9px] font-bold text-slate-400">{item.time}</span>
                       </div>
                       <p className="text-[10px] font-bold text-slate-400">{item.area} • {item.status}</p>
                    </div>
                 </div>
               ))}
             </div>
             <button className="w-full mt-8 py-3 text-indigo-600 font-bold text-xs uppercase tracking-tighter hover:tracking-widest transition-all">
                View All Activity
             </button>
           </div>
        </div>
      </div>
    </div>
  );
}
