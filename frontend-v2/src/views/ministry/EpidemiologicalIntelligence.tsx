import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Activity, ShieldAlert, Zap, Filter, 
  MapPin, Database, Layers, Search, 
  TrendingUp, AlertTriangle, Fingerprint,
  FileSpreadsheet, Share2, ShieldCheck
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';
import { PredictiveOutbreak } from '../../components/PredictiveOutbreak';
import { 
  ResponsiveContainer, AreaChart, Area, 
  XAxis, YAxis, CartesianGrid, Tooltip, 
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ComposedChart, Bar, Line
} from 'recharts';

const outbreakData = [
  { subject: 'Influenza', A: 120, B: 110, fullMark: 150 },
  { subject: 'COVID-X', A: 98, B: 130, fullMark: 150 },
  { subject: 'Malaria', A: 86, B: 130, fullMark: 150 },
  { subject: 'Hepatitis', A: 99, B: 100, fullMark: 150 },
  { subject: 'Cholera', A: 85, B: 90, fullMark: 150 },
  { subject: 'Typhoid', A: 65, B: 85, fullMark: 150 },
];

const zoneSpecificData: Record<string, any[]> = {
  'Basrah Cluster': [
    { name: 'Week 1', cases: 140, predicted: 130, risk: 40 },
    { name: 'Week 2', cases: 210, predicted: 180, risk: 65 },
    { name: 'Week 3', cases: 450, predicted: 300, risk: 95 },
    { name: 'Week 4', cases: 880, predicted: 600, risk: 100 },
  ],
  'Nineveh Hub': [
    { name: 'Week 1', cases: 80, predicted: 90, risk: 20 },
    { name: 'Week 2', cases: 120, predicted: 110, risk: 30 },
    { name: 'Week 3', cases: 250, predicted: 200, risk: 55 },
    { name: 'Week 4', cases: 380, predicted: 400, risk: 45 },
  ],
};

const timelineData = [
  { name: 'Week 1', cases: 400, predicted: 420, risk: 20 },
  { name: 'Week 2', cases: 300, predicted: 350, risk: 40 },
  { name: 'Week 3', cases: 600, predicted: 580, risk: 90 },
  { name: 'Week 4', cases: 800, predicted: 850, risk: 100 },
  { name: 'Week 5', cases: 500, predicted: 600, risk: 60 },
  { name: 'Week 6', cases: 400, predicted: 450, risk: 30 },
];

import { CrisisResponsePipeline } from '../../components/ministry/CrisisResponsePipeline';

export function EpidemiologicalIntelligence() {
  const { t } = useLanguage();
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  const activeTimeline = selectedZone ? (zoneSpecificData[selectedZone] || timelineData) : timelineData;

  return (
    <div className="p-8 space-y-8 bg-slate-950 min-h-screen text-slate-100">
      {/* HUD Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 pb-8 border-b border-white/5">
        <div className="flex items-center gap-6">
           <div className="p-4 bg-rose-600 rounded-[2rem] shadow-2xl shadow-rose-900/40 relative group">
              <ShieldAlert size={40} className="animate-pulse" />
              <div className="absolute inset-0 bg-rose-400/20 blur-xl scale-125 opacity-0 group-hover:opacity-100 transition-opacity" />
           </div>
           <div>
              <h1 className="text-4xl font-black tracking-tight uppercase leading-none mb-2">{t.epiHud}</h1>
              <div className="flex items-center gap-3">
                 <span className="px-2 py-0.5 bg-rose-500/20 text-rose-400 text-[10px] font-black uppercase tracking-widest border border-rose-500/30 rounded-lg">Level 4 Bio-Surveillance</span>
                 <span className="text-slate-500 font-bold text-[10px] uppercase tracking-[0.2em]">{t.nationalHealthGrid} Integrity: 99.4%</span>
              </div>
           </div>
        </div>

        <div className="flex gap-4">
           <button className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">Export G-88 Report</button>
           <button className="px-6 py-3 bg-rose-600 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest shadow-xl shadow-rose-900/20 hover:scale-[1.02] transition-all">Broadcast Alert</button>
        </div>
      </div>

      <CrisisResponsePipeline />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        {/* Left: Disease Vector Analysis */}
        <div className="xl:col-span-8 space-y-8">
           <div className="p-8 bg-white/5 border border-white/5 rounded-[3rem] relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-5">
                 <TrendingUp size={120} />
              </div>
              <div className="relative z-10">
                 <div className="flex justify-between items-start mb-12">
                    <div>
                       <h2 className="text-2xl font-black mb-1">{selectedZone ? `${selectedZone} Vector Analysis` : t.vectorTimeline}</h2>
                       <p className="text-xs text-rose-400 font-bold uppercase tracking-widest">{selectedZone ? 'Localized Granular Trends' : `${t.clinicalSurveillance} vs Predictive Neural Model`}</p>
                    </div>
                    {selectedZone && (
                       <button 
                         onClick={() => setSelectedZone(null)}
                         className="px-4 py-2 bg-rose-600 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-rose-700 transition-colors"
                       >
                          Reset View
                       </button>
                    )}
                    <div className="flex bg-slate-900 p-1 rounded-xl border border-white/5">
                       {['Caseload', 'Fatality', 'Risk Index'].map(tab => (
                         <button key={tab} className="px-4 py-2 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors">{tab}</button>
                       ))}
                    </div>
                 </div>

                 <div className="h-[400px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                       <ComposedChart data={activeTimeline}>
                          <defs>
                             <linearGradient id="colorCases" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                             </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                          <XAxis dataKey="name" stroke="rgba(255,255,255,0.2)" fontSize={10} fontWeight={900} />
                          <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} fontWeight={900} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '24px' }}
                            itemStyle={{ color: '#fff', fontSize: '10px' }}
                          />
                          <Area type="monotone" dataKey="cases" stroke="#f43f5e" fill="url(#colorCases)" strokeWidth={4} />
                          <Line type="step" dataKey="predicted" stroke="#6366f1" strokeDasharray="5 5" strokeWidth={2} dot={false} />
                          <Bar dataKey="risk" fill="#fbbf24" radius={[4, 4, 0, 0]} opacity={0.2} />
                       </ComposedChart>
                    </ResponsiveContainer>
                 </div>
              </div>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="p-8 bg-white/5 border border-white/5 rounded-[3rem]">
                 <h3 className="text-xs font-black uppercase tracking-widest text-rose-400 mb-8 text-center">{t.pathogenProfiles}</h3>
                 <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                       <RadarChart cx="50%" cy="50%" outerRadius="80%" data={outbreakData}>
                          <PolarGrid stroke="rgba(255,255,255,0.05)" />
                          <PolarAngleAxis dataKey="subject" stroke="rgba(255,255,255,0.4)" fontSize={10} fontWeight={900} />
                          <PolarRadiusAxis angle={30} domain={[0, 150]} stroke="none" />
                          <Radar name="Active Vector" dataKey="A" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.5} />
                          <Radar name="Regional Baseline" dataKey="B" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} />
                       </RadarChart>
                    </ResponsiveContainer>
                 </div>
              </div>

              <div className="p-8 bg-slate-900 rounded-[3rem] border border-white/5">
                 <h3 className="text-xs font-black uppercase tracking-widest text-rose-400 mb-8">{t.bioSovereignty}</h3>
                 <div className="space-y-4">
                    {[
                      { region: 'Basrah Cluster', risk: 'High', cases: 1402, color: 'text-rose-400' },
                      { region: 'Nineveh Hub', risk: 'Moderate', cases: 450, color: 'text-amber-400' },
                      { region: 'Anbar Sector', risk: 'Low', cases: 88, color: 'text-emerald-400' },
                      { region: 'Erbil East', risk: 'Stable', cases: 12, color: 'text-indigo-400' },
                    ].map(node => (
                      <div 
                        key={node.region} 
                        className={cn(
                          "p-4 rounded-2xl flex items-center justify-between border transition-all cursor-pointer group",
                          selectedZone === node.region 
                           ? "bg-rose-600/20 border-rose-500/50 shadow-lg shadow-rose-900/20" 
                           : "bg-white/5 border-white/5 hover:bg-white/10"
                        )}
                        onClick={() => setSelectedZone(node.region === selectedZone ? null : node.region)}
                      >
                         <div className="flex items-center gap-4">
                            <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", node.color.replace('text', 'bg'))} />
                            <span className="text-sm font-black text-white">{node.region}</span>
                         </div>
                         <div className="text-right">
                            <p className={cn("text-[9px] font-black uppercase tracking-widest", node.color)}>{node.risk} Risk</p>
                            <p className="text-xs font-bold text-slate-500">{node.cases} Live IDs</p>
                         </div>
                      </div>
                    ))}
                 </div>
              </div>
           </div>
        </div>

        {/* Right: Regulatory Audit & Control */}
        <div className="xl:col-span-4 space-y-8">
           <div className="p-8 bg-indigo-600 rounded-[3rem] text-white overflow-hidden relative shadow-2xl">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
              <div className="relative z-10">
                 <div className="flex items-center gap-3 mb-6">
                    <Fingerprint size={24} />
                    <span className="text-[10px] font-black uppercase tracking-[0.2em]">{t.regulatoryControl}</span>
                 </div>
                 <h3 className="text-2xl font-black mb-4 leading-tight">{t.dataQuarantine}</h3>
                 <p className="text-sm text-indigo-100/80 mb-8 font-medium leading-relaxed">
                   3 Unauthorized 'read' attempts detected in the Al-Karkh sector via Doctor Portal. Protocol X-01 has localized the breach.
                 </p>
                 <div className="space-y-3 mb-8">
                    <div className="p-4 bg-white/10 rounded-2xl flex items-center justify-between">
                       <span className="text-[10px] font-black uppercase">Active Quarantines</span>
                       <span className="text-xs font-black">04 Nodes</span>
                    </div>
                    <div className="p-4 bg-rose-400/20 rounded-2xl flex items-center justify-between border border-rose-400/30">
                       <span className="text-[10px] font-black uppercase text-rose-100">Integrity Breach</span>
                       <span className="text-xs font-black text-white">IMMEDIATE</span>
                    </div>
                 </div>
                 <button className="w-full py-4 bg-white text-indigo-600 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-[1.02] transition-transform">
                    View Sovereignty Log
                 </button>
              </div>
           </div>

           <PredictiveOutbreak />

           <div className="p-8 bg-emerald-600/10 border border-emerald-500/20 rounded-[3rem] text-center">
              <div className="w-16 h-16 bg-emerald-500 text-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-xl shadow-emerald-500/30 ring-8 ring-emerald-500/10">
                 <ShieldCheck size={32} />
              </div>
              <h3 className="text-lg font-black text-white mb-2 uppercase tracking-tight">{t.trustIntegrity}</h3>
              <p className="text-4xl font-black text-emerald-400 mb-2">99.98%</p>
              <div className="flex items-center justify-center gap-2 text-[10px] font-black uppercase text-emerald-400/60 tracking-widest">
                 <Zap size={10} className="fill-emerald-400/60" /> Grid Validated
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
