import React from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Users, UserPlus, ShieldCheck, Heart, 
  ChevronRight, ArrowUpRight, Activity, 
  Baby, UserRound, MoreVertical, History
} from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../../lib/utils';

export function FamilyManagement() {
  const { t } = useLanguage();

  const familyMembers = [
    { id: 'f1', name: 'Zaid (Son)', role: 'Dependent', status: 'Optimal', score: 92, lastCheck: '2 days ago', avatar: '👶' },
    { id: 'f2', name: 'Mariam (Wife)', role: 'Contributor', status: 'Warning', score: 68, lastCheck: 'Today', avatar: '👩' },
    { id: 'f3', name: 'Ahmed (Father)', role: 'Dependent', status: 'Stable', score: 75, lastCheck: '1 week ago', avatar: '👴' },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto p-4 md:p-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div className="editorial-stack">
          <span className="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-600 mb-2 block">{t.familyManagement}</span>
          <h1 className="text-4xl font-black text-slate-900 tracking-tighter leading-none italic">{t.familyNetwork}</h1>
          <p className="text-slate-500 mt-2 font-medium">Coordinate care and manage health permissions for your dependents.</p>
        </div>
        <button className="flex items-center gap-2 px-8 py-4 bg-slate-900 text-white rounded-[2rem] font-black text-xs uppercase tracking-widest shadow-xl shadow-slate-200 hover:scale-[1.02] transition-all">
          <UserPlus size={18} /> {t.addDependent}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Main List */}
        <div className="lg:col-span-8 space-y-6">
          {familyMembers.map((member, i) => (
            <motion.div 
              key={member.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className="bg-white p-8 rounded-[3rem] border border-slate-200 shadow-sm hover:shadow-xl hover:shadow-slate-100 transition-all group flex flex-col md:flex-row md:items-center justify-between gap-8"
            >
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 bg-slate-50 rounded-[2rem] flex items-center justify-center text-4xl shadow-sm border border-slate-100 group-hover:scale-105 transition-transform">
                  {member.avatar}
                </div>
                <div>
                   <h3 className="text-2xl font-black text-slate-900 tracking-tighter leading-none mb-1">{member.name}</h3>
                   <div className="flex items-center gap-3">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest bg-slate-50 px-2 py-0.5 rounded-md">{member.role}</span>
                      <span className="w-1 h-1 bg-slate-200 rounded-full" />
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Last synced: {member.lastCheck}</span>
                   </div>
                </div>
              </div>

              <div className="flex items-center gap-10">
                <div className="text-center">
                   <p className="text-[9px] font-black uppercase text-slate-400 tracking-widest mb-1">Health Score</p>
                   <div className="flex items-center gap-2">
                      <span className={cn(
                        "text-2xl font-black",
                        member.score > 80 ? "text-emerald-500" : member.score > 60 ? "text-amber-500" : "text-red-500"
                      )}>{member.score}</span>
                      <Activity size={16} className={member.score > 80 ? "text-emerald-500" : "text-amber-500"} />
                   </div>
                </div>
                
                <div className="h-12 w-px bg-slate-100 hidden md:block" />

                <div className="flex items-center gap-3">
                   <button className="p-4 bg-slate-50 text-slate-400 rounded-2xl hover:bg-slate-900 hover:text-white transition-all shadow-sm">
                      <ShieldCheck size={20} />
                   </button>
                   <button className="px-6 py-4 bg-indigo-600 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest flex items-center gap-3 shadow-lg shadow-indigo-100 hover:bg-slate-900 transition-colors">
                      View Records <ChevronRight size={16} />
                   </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Sidebar Info */}
        <div className="lg:col-span-4 space-y-6">
           <div className="bg-indigo-600 rounded-[3rem] p-10 text-white shadow-2xl relative overflow-hidden group border-b-8 border-indigo-800">
              <div className="absolute top-0 right-0 p-10 opacity-10 group-hover:scale-110 transition-transform">
                <ShieldCheck size={120} />
              </div>
              <h3 className="text-xl font-black uppercase tracking-widest mb-6 italic">Privacy Control</h3>
              <p className="text-indigo-100 text-sm leading-relaxed mb-8 opacity-90">
                 You have **Sovereign Access** to these records. All data transfer is encrypted and auditable in the Data Sovereignty Hub.
              </p>
              <div className="space-y-4">
                 <div className="flex items-center justify-between p-4 bg-white/10 rounded-2xl border border-white/5 backdrop-blur-md">
                    <span className="text-[10px] font-bold uppercase tracking-widest">Shared Access</span>
                    <span className="text-[10px] font-black text-emerald-400">ENABLED</span>
                 </div>
                 <div className="flex items-center justify-between p-4 bg-white/10 rounded-2xl border border-white/5 backdrop-blur-md">
                    <span className="text-[10px] font-bold uppercase tracking-widest">Emergency Bypass</span>
                    <span className="text-[10px] font-black text-emerald-400">AUTHORIZED</span>
                 </div>
              </div>
           </div>

           <div className="bg-slate-50 border border-slate-200 rounded-[3rem] p-10 space-y-6">
              <div className="flex items-center gap-4 mb-4">
                 <div className="w-12 h-12 bg-white rounded-2xl border border-slate-200 flex items-center justify-center shadow-sm">
                    <History size={24} className="text-indigo-600" />
                 </div>
                 <h4 className="text-lg font-black tracking-tight leading-none italic">Security Audit</h4>
              </div>
              <div className="space-y-4">
                 {[
                   { event: 'Records viewed by Samer', target: 'Zaid', time: '1h ago' },
                   { event: 'Consent updated', target: 'Ahmed', time: 'Yesterday' }
                 ].map((log, idx) => (
                   <div key={idx} className="flex flex-col gap-1 border-b border-slate-200 pb-3 last:border-0">
                      <p className="text-xs font-bold text-slate-900">{log.event}</p>
                      <div className="flex items-center justify-between">
                         <span className="text-[9px] font-black uppercase text-indigo-600">{log.target}</span>
                         <span className="text-[9px] font-bold text-slate-400">{log.time}</span>
                      </div>
                   </div>
                 ))}
              </div>
              <button className="w-full py-4 bg-white border border-slate-200 rounded-[2rem] text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-all">
                 View Full Chain
              </button>
           </div>
        </div>
      </div>
    </div>
  );
}
