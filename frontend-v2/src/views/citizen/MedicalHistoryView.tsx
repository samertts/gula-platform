import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  History as HistoryIcon, Calendar, Filter, FileText, 
  ChevronRight, Stethoscope, Beaker, Activity as ActivityIcon,
  Search, Download, Share2, ShieldCheck, ArrowUpRight, User, Shield
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';

export const MedicalHistoryView: React.FC = () => {
  const { t } = useLanguage();
  const [filter, setFilter] = useState('all');

  const aiInsights = [
    { 
      type: 'warning', 
      title: 'Cardiac Rhythm Anomaly', 
      content: 'Pattern analysis suggests intermittent systolic elevation. Recommended: 24h ambulatory monitoring.',
      action: 'Schedule Holter'
    },
    { 
      type: 'info', 
      title: 'Optimal Recovery', 
      content: 'Post-treatment inflammatory markers have decreased by 22% compared to previous baseline.',
      action: 'View Trend'
    }
  ];

  const historyItems = [
    { id: '1', date: '2024-03-15', provider: 'Dr. Sarah Smith', type: 'diagnosis', title: 'Hypertension Follow-up', desc: 'Blood pressure stabilized at 125/82. Continuing current medication.' },
    { id: '2', date: '2024-02-28', provider: 'Central Lab', type: 'lab', title: 'Complete Blood Count', desc: 'All parameters within normal range. Slight vitamin D deficiency noted.' },
    { id: '3', date: '2024-01-10', provider: 'Radiology Dept', type: 'imaging', title: 'Chest X-Ray', desc: 'No significant findings. Clear lung fields.' },
    { id: '4', date: '2023-12-05', provider: 'General Clinic', type: 'prescription', title: 'Amoxicillin 500mg', desc: 'Treatment for acute pharyngitis.' },
  ];

  const getTypeStyles = (type: string) => {
    switch(type) {
      case 'diagnosis': return 'bg-blue-100 text-blue-600';
      case 'lab': return 'bg-amber-100 text-amber-600';
      case 'imaging': return 'bg-purple-100 text-purple-600';
      case 'prescription': return 'bg-green-100 text-green-600';
      default: return 'bg-slate-100 text-slate-600';
    }
  };

  const getTypeIcon = (type: string) => {
    switch(type) {
      case 'diagnosis': return Stethoscope;
      case 'lab': return Beaker;
      case 'imaging': return ActivityIcon;
      case 'prescription': return FileText;
      default: return HistoryIcon;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-indigo-600 mb-1">
            <HistoryIcon size={20} />
            <span className="text-[10px] font-black uppercase tracking-[0.2em]">{t.records || 'RECORDS'}</span>
          </div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">{t.medicalHistory}</h1>
          <p className="text-slate-500 font-medium">{t.motto}</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="p-4 bg-white border border-slate-200 rounded-2xl text-slate-600 hover:bg-slate-50 transition-all shadow-sm flex items-center gap-2 font-black text-[10px] uppercase tracking-widest">
            <Download size={16} /> {t.downloadPdf || 'PDF'}
          </button>
          <button className="p-4 bg-indigo-600 text-white rounded-2xl hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-100 flex items-center gap-2 font-black text-[10px] uppercase tracking-widest">
            <Share2 size={16} /> {t.shareRecords || 'SHARE'}
          </button>
        </div>
      </div>

      {/* AI Intelligence Block */}
      <div className="bg-slate-900 rounded-[3rem] p-10 text-white relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/20 rounded-full blur-[80px] -mr-32 -mt-32" />
        <div className="relative z-10 grid md:grid-cols-2 gap-12">
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-indigo-500 rounded-2xl shadow-lg ring-4 ring-indigo-500/20">
                <ShieldCheck size={24} className="text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-black tracking-tight tracking-tight">Clinical Insights.</h3>
                <p className="text-indigo-300 text-xs font-bold uppercase tracking-widest">Autonomous Intelligence Analysis</p>
              </div>
            </div>
            <p className="text-slate-400 leading-relaxed font-medium">
              GULA AI has synthesized your complete medical timeline. Our models have identified patterns that may require clinical attention or represent positive health trends.
            </p>
            <div className="flex gap-4 pt-4">
              <button className="px-6 py-3 bg-white text-slate-900 rounded-xl text-[10px] font-black uppercase tracking-widest hover:scale-105 transition-transform">Download Intelligence Report</button>
              <button className="px-6 py-3 bg-white/10 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-white/20 transition-all border border-white/10">Methodology</button>
            </div>
          </div>
          <div className="space-y-4">
            {aiInsights.map((insight, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.2 }}
                className="p-6 bg-white/5 border border-white/10 rounded-3xl backdrop-blur-md"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", insight.type === 'warning' ? 'bg-amber-400' : 'bg-blue-400')} />
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">{insight.title}</span>
                  </div>
                  <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Confidence 94%</span>
                </div>
                <p className="text-sm font-medium text-slate-400 leading-snug mb-4">{insight.content}</p>
                <button className="text-[10px] font-black text-indigo-400 uppercase tracking-widest hover:text-indigo-300 transition-colors flex items-center gap-1.5">
                  {insight.action} <ArrowUpRight size={12} />
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
         {[
           { label: 'Visits', value: '24', color: 'indigo' },
           { label: 'Procedures', value: '03', color: 'blue' },
           { label: 'Prescriptions', value: '42', color: 'emerald' },
           { label: 'Lab Tests', value: '81', color: 'amber' }
         ].map((stat, i) => (
           <div key={i} className="p-6 bg-white border border-slate-100 rounded-[2.5rem] shadow-sm">
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
             <p className="text-2xl font-black text-slate-900 tracking-tight">{stat.value}</p>
           </div>
         ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-8 items-start">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-slate-100 rounded-[3rem] shadow-xl shadow-slate-200/50 overflow-hidden">
            <div className="p-8 border-b border-slate-50 flex items-center justify-between">
               <h2 className="text-xl font-black text-slate-800 tracking-tight uppercase">{t.recentHistory || 'RECENT HISTORY'}</h2>
               <div className="flex gap-2">
                  {['all', 'diagnosis', 'lab', 'imaging', 'prescription'].map(f => (
                    <button 
                      key={f}
                      onClick={() => setFilter(f)}
                      className={cn(
                        "px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all",
                        filter === f ? "bg-indigo-600 text-white shadow-md shadow-indigo-100" : "bg-white text-slate-400 border border-slate-200 hover:border-indigo-300"
                      )}
                    >
                      {f}
                    </button>
                  ))}
               </div>
            </div>

            <div className="p-2">
               {historyItems.filter(h => filter === 'all' || h.type === filter).map((h, i) => {
                 const Icon = getTypeIcon(h.type);
                 return (
                   <motion.div
                     initial={{ opacity: 0, x: -10 }}
                     animate={{ opacity: 1, x: 0 }}
                     transition={{ delay: i * 0.1 }}
                     key={h.id}
                     className="p-8 hover:bg-slate-50 rounded-[2.5rem] transition-colors flex items-start gap-8 group cursor-pointer border-b border-transparent last:border-b-0 border-slate-50"
                   >
                     <div className="flex flex-col items-center pt-1 w-20">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">{h.date.split('-')[1]}/{h.date.split('-')[2]}</span>
                        <div className={cn("p-4 rounded-2xl shadow-inner transition-transform group-hover:scale-110", getTypeStyles(h.type))}>
                           <Icon className="w-6 h-6" />
                        </div>
                        <span className="text-[10px] font-black text-slate-400 mt-3">{h.date.split('-')[0]}</span>
                     </div>
                     
                     <div className="flex-1 space-y-2">
                        <div className="flex items-center justify-between">
                           <h3 className="font-black text-slate-900 text-xl tracking-tight group-hover:text-indigo-600 transition-colors uppercase">{h.title}</h3>
                           <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-indigo-600 transition-transform group-hover:translate-x-1" />
                        </div>
                        <div className="flex items-center gap-2">
                           <User size={12} className="text-indigo-400" />
                           <span className="text-[10px] font-black text-indigo-500 uppercase tracking-widest">{h.provider}</span>
                        </div>
                        <p className="text-sm text-slate-500 leading-relaxed pt-2 font-medium">{h.desc}</p>
                     </div>
                   </motion.div>
                 );
               })}
            </div>
          </div>
        </div>

        <div className="space-y-6">
           <h3 className="text-xl font-black text-slate-800 tracking-tight uppercase">Structured Labs</h3>
           <div className="p-8 bg-white border border-slate-100 rounded-[2.5rem] shadow-xl shadow-slate-200/50 space-y-6">
              {[
                { name: 'Hemoglobin A1c', val: '5.4', unit: '%', status: 'optimal', range: '4.8 - 5.6' },
                { name: 'Creatinine', val: '0.92', unit: 'mg/dL', status: 'optimal', range: '0.7 - 1.3' },
                { name: 'Vitamin D', val: '24', unit: 'ng/mL', status: 'low', range: '30 - 100' },
                { name: 'LDL Cholesterol', val: '142', unit: 'mg/dL', status: 'warning', range: '< 100' }
              ].map((lab, i) => (
                <div key={i} className="space-y-2">
                   <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest">
                      <span className="text-slate-400">{lab.name}</span>
                      <span className={cn(
                        lab.status === 'optimal' ? 'text-emerald-500' : 
                        lab.status === 'warning' ? 'text-amber-500' : 'text-indigo-500'
                      )}>{lab.status}</span>
                   </div>
                   <div className="flex items-end justify-between">
                      <div className="flex items-baseline gap-1">
                         <span className="text-2xl font-black text-slate-900">{lab.val}</span>
                         <span className="text-xs font-bold text-slate-400 tracking-tight">{lab.unit}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-300 font-bold uppercase tracking-widest">REF: {lab.range}</span>
                   </div>
                   <div className="h-1.5 w-full bg-slate-50 rounded-full overflow-hidden">
                      <div 
                        className={cn("h-full rounded-full transition-all duration-1000", lab.status === 'optimal' ? 'bg-emerald-500' : 'bg-amber-400')} 
                        style={{ width: `${Math.min((parseFloat(lab.val) / 200) * 100, 100)}%` }}
                      />
                   </div>
                </div>
              ))}
              <button className="w-full py-4 bg-slate-50 text-slate-400 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-100 transition-all">View All 42 Results</button>
           </div>

           <div className="p-8 bg-slate-900 rounded-[2.5rem] border border-white/10 flex items-center gap-4 text-white">
              <div className="bg-indigo-600 p-3 rounded-xl shadow-lg ring-4 ring-indigo-500/20">
                 <Shield size={20} />
              </div>
              <p className="text-[10px] font-black leading-snug uppercase tracking-[0.1em]">Data integrity verified via national backbone.</p>
           </div>
        </div>
      </div>
    </div>
  );
};
