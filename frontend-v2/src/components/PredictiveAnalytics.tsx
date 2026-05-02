import React from 'react';
import { motion } from 'motion/react';
import { TrendingUp, Activity, Users, FlaskConical, AlertTriangle } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';

const data = [
  { name: 'Mon', volume: 450, expected: 480 },
  { name: 'Tue', volume: 520, expected: 510 },
  { name: 'Wed', volume: 480, expected: 550 },
  { name: 'Thu', volume: 610, expected: 590 },
  { name: 'Fri', volume: 550, expected: 620 },
  { name: 'Sat', volume: 320, expected: 350 },
  { name: 'Sun', volume: 210, expected: 240 },
];

export function PredictiveAnalytics() {
  const { t } = useLanguage();

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-black text-slate-900 uppercase tracking-tight">{t.workloadPrediction}</h3>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">7-Day Foresight Model v4.1</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-2xl border border-indigo-100">
          <TrendingUp size={16} />
          <span className="text-[10px] font-black uppercase tracking-widest">Accuracy: 98.4%</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden relative group">
           <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.07] transition-opacity">
              <Activity size={120} />
           </div>
           
           <div className="relative z-10 h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorVol" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorExp" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.05}/>
                      <stop offset="95%" stopColor="#94a3b8" stopOpacity={0}/>
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
                    contentStyle={{ borderRadius: '1rem', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="volume" 
                    stroke="#4f46e5" 
                    strokeWidth={4}
                    fillOpacity={1} 
                    fill="url(#colorVol)" 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="expected" 
                    stroke="#94a3b8" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    fillOpacity={1} 
                    fill="url(#colorExp)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
           </div>
        </div>

        <div className="space-y-6">
           <div className="bg-slate-900 rounded-[2.5rem] p-8 text-white">
              <div className="flex items-center gap-3 mb-6">
                 <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-xl">
                    <FlaskConical size={18} />
                 </div>
                 <h4 className="text-sm font-black uppercase tracking-tight">Capacity Forecast</h4>
              </div>
              
              <div className="space-y-6">
                 <div className="flex justify-between items-end">
                    <div>
                       <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Peak Utilization</p>
                       <p className="text-3xl font-black tracking-tight">Thursday <span className="text-indigo-400">14:00</span></p>
                    </div>
                 </div>
                 
                 <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                       <AlertTriangle size={14} className="text-amber-400" />
                       <span className="text-[10px] font-black uppercase tracking-widest text-amber-400">Reagent Alert</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed font-medium">
                       Expected peak on Thursday will require +15% reagent allocation for Cluster B nodes.
                    </p>
                 </div>
              </div>
           </div>

           <div className="bg-indigo-600 rounded-[2.5rem] p-8 text-white relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 blur-[50px] -mr-16 -mt-16" />
              <div className="relative z-10">
                 <div className="flex items-center gap-3 mb-6 text-white/60">
                    <Users size={18} />
                    <h4 className="text-sm font-black uppercase tracking-tight">Staff Optimization</h4>
                 </div>
                 
                 <div className="space-y-2">
                    <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-white/60">
                       <span>Staffing Level</span>
                       <span>88% Optimal</span>
                    </div>
                    <div className="w-full bg-white/20 h-1.5 rounded-full overflow-hidden">
                       <motion.div 
                         initial={{ width: 0 }}
                         animate={{ width: '88%' }}
                         className="h-full bg-white"
                       />
                    </div>
                 </div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
