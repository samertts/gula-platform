import React from 'react';
import { motion } from 'motion/react';
import { BrainCircuit, Activity, Zap, TrendingUp, AlertTriangle, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/utils';
import { ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';

const RISK_DATA = [
  { subject: 'Cardiovascular', A: 85, full: 100 },
  { subject: 'Respiratory', A: 70, full: 100 },
  { subject: 'Neurological', A: 40, full: 100 },
  { subject: 'Renal', A: 30, full: 100 },
  { subject: 'Metabolic', A: 90, full: 100 },
];

export function AdvancedTriageDetails({ patientName }: { patientName: string }) {
  return (
    <div className="bg-slate-900 rounded-[3rem] p-10 text-white relative overflow-hidden shadow-2xl border border-white/5">
      <div className="absolute top-0 right-0 p-12 opacity-[0.03] pointer-events-none scale-150">
         <BrainCircuit size={300} />
      </div>

      <div className="relative z-10 space-y-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="w-14 h-14 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-indigo-500/20">
               <Zap size={28} className="text-white fill-indigo-300" />
            </div>
            <div>
               <h3 className="text-2xl font-black uppercase tracking-tight">Post-Neural Analysis</h3>
               <p className="text-indigo-400 text-[10px] font-black uppercase tracking-[0.2em]">Deep Triage for {patientName}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 px-6 py-3 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-xl">
             <ShieldCheck size={18} className="text-emerald-400" />
             <span className="text-xs font-black uppercase tracking-widest tracking-tighter">Clinical Confidence: 99.1%</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div className="space-y-8">
            <div className="space-y-4">
              <h4 className="text-sm font-black uppercase tracking-widest text-slate-400 border-l-4 border-indigo-600 pl-4">Systemic Multi-Risk Vectors</h4>
              <p className="text-sm text-slate-400 leading-relaxed font-medium">
                GULA's neural backbone has correlated recent lab data (CRP, WBC) with vital telemetry in real-time, identifying a high metabolic-cardio intersection risk.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'Sepsis Risk', val: 'Low', color: 'text-emerald-400' },
                { label: 'CV Event', val: 'High', color: 'text-rose-400' },
                { label: 'Resp. Distress', val: 'Moderate', color: 'text-amber-400' },
                { label: 'Neural Deficit', val: 'Minimal', color: 'text-slate-400' },
              ].map((item, i) => (
                <div key={i} className="p-6 bg-white/5 rounded-[2rem] border border-white/5 group hover:bg-white/10 transition-colors">
                   <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-2">{item.label}</span>
                   <div className={cn("text-xl font-black uppercase tracking-tight", item.color)}>{item.val}</div>
                </div>
              ))}
            </div>

            <div className="p-6 bg-indigo-600/20 border border-indigo-500/20 rounded-[2.5rem] flex items-center gap-4">
               <Activity size={32} className="text-indigo-400 shrink-0" />
               <div>
                  <p className="text-xs font-black uppercase tracking-widest leading-none mb-1 text-indigo-300">Predictive Trajectory</p>
                  <p className="text-sm font-medium leading-tight">Vitals indicate a potential HR spike in the next 15-20 minutes based on historical trend matching.</p>
               </div>
            </div>
          </div>

          <div className="relative h-[400px] bg-white/5 rounded-[3rem] border border-white/5 p-8 flex flex-col items-center justify-center group overflow-hidden">
             <div className="absolute inset-0 opacity-[0.02] pointer-events-none group-hover:scale-110 transition-transform">
               <div style={{ backgroundImage: 'radial-gradient(white 1px, transparent 1px)', backgroundSize: '30px 30px' }} className="w-full h-full" />
             </div>
             
             <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-4 z-10">Systems Health Radar</h4>
             
             <div className="w-full h-full relative z-10">
                <ResponsiveContainer width="100%" height="100%">
                   <RadarChart cx="50%" cy="50%" outerRadius="80%" data={RISK_DATA}>
                     <PolarGrid stroke="#ffffff20" />
                     <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700 }} />
                     <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                     <Radar
                        name="Patient Risk"
                        dataKey="A"
                        stroke="#6366f1"
                        fill="#6366f1"
                        fillOpacity={0.6}
                     />
                   </RadarChart>
                </ResponsiveContainer>
             </div>

             <div className="absolute bottom-8 right-8 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-indigo-500" />
                <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Deep Neural Scoring</span>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
