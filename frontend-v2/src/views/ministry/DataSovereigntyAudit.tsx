import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  ShieldCheck, ShieldAlert, Fingerprint, 
  Search, Filter, Database, Server,
  Lock, Key, Eye, User, Globe, Activity,
  MoreVertical, Clock, CheckCircle2, AlertTriangle,
  History, Download, Zap, MapPin
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';
import { BiometricStatus } from '../../components/BiometricStatus';

interface AuditLog {
  id: string;
  user: string;
  role: 'doctor' | 'admin' | 'researcher' | 'lab';
  action: string;
  resourceId: string;
  timestamp: string;
  integrity: 'valid' | 'warning' | 'critical';
  ip: string;
  location: string;
}

const auditLogs: AuditLog[] = [
  { id: 'LOG-8821', user: 'Dr. Samer M.', role: 'doctor', action: 'Identity Read', resourceId: 'GID-292-1029', timestamp: '2024-04-25 14:02:11', integrity: 'valid', ip: '192.168.4.12', location: 'Baghdad Central' },
  { id: 'LOG-8822', user: 'SysAdmin Alpha', role: 'admin', action: 'Grid Mod', resourceId: 'CLUSTER-B3', timestamp: '2024-04-25 13:58:00', integrity: 'warning', ip: '110.12.92.1', location: 'Erbil Sector 1' },
  { id: 'LOG-8823', user: 'Researcher Z.', role: 'researcher', action: 'Query Bulk', resourceId: 'EPID-X99', timestamp: '2024-04-25 13:12:45', integrity: 'valid', ip: '29.34.1.92', location: 'Basrah Hub' },
  { id: 'LOG-8824', user: 'Lab Node 04', role: 'lab', action: 'Result Push', resourceId: 'RES-00293', timestamp: '2024-04-24 10:22:11', integrity: 'critical', ip: 'Unknown', location: 'Autonomous' },
];

export function DataSovereigntyAudit() {
  const { t } = useLanguage();
  const [filter, setFilter] = useState('All');

  return (
    <div className="p-8 space-y-8 bg-white min-h-screen">
      {/* Header Panel */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-8 pb-8 border-b border-slate-100">
        <div className="flex items-center gap-6">
           <div className="p-4 bg-slate-900 text-white rounded-[2rem] shadow-2xl shadow-indigo-100">
              <ShieldCheck size={32} />
           </div>
           <div>
              <h1 className="text-3xl font-black tracking-tight text-slate-900 uppercase">{t.auditHub}</h1>
              <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">GULA Regulatory Compliance • Protocol V4.2</p>
           </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
           {[
             { label: t.activeSessions, value: '142', icon: Activity, color: 'text-indigo-600' },
             { label: t.integrityRating, value: '99.9%', icon: ShieldCheck, color: 'text-emerald-600' },
             { label: t.auditDensity, value: 'High', icon: Database, color: 'text-slate-600' },
             { label: t.threatIndex, value: 'Low', icon: AlertTriangle, color: 'text-rose-500' }
           ].map(stat => (
             <div key={stat.label} className="p-4 bg-slate-50 border border-slate-100 rounded-2xl">
                <div className="flex items-center gap-2 mb-2">
                   <stat.icon size={12} className={stat.color} />
                   <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest">{stat.label}</span>
                </div>
                <p className="text-lg font-black text-slate-900">{stat.value}</p>
             </div>
           ))}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Main Audit Feed */}
        <div className="xl:col-span-2 space-y-6">
           <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 px-2">
              <div className="flex items-center gap-4">
                 <h2 className="text-xl font-bold text-slate-900 tracking-tight">{t.immutableLedger}</h2>
                 <span className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-full text-[10px] font-black uppercase tracking-widest italic">Live Audit Active</span>
              </div>
              <div className="flex gap-2">
                 <button className="p-2 border border-slate-100 rounded-xl hover:bg-slate-50"><Search size={18} className="text-slate-400" /></button>
                 <button className="p-2 border border-slate-100 rounded-xl hover:bg-slate-50"><Filter size={18} className="text-slate-400" /></button>
              </div>
           </div>

           <div className="space-y-4">
              <AnimatePresence mode="popLayout">
                {auditLogs.map((log, i) => (
                  <motion.div 
                    key={log.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="p-6 bg-white border border-slate-100 rounded-[2.5rem] hover:border-indigo-600 transition-all group relative overflow-hidden"
                  >
                    <div className="flex flex-col md:flex-row items-center gap-8 relative z-10">
                       <div className="flex items-center gap-6 md:w-64">
                          <div className={cn(
                            "w-14 h-14 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-105 shadow-sm",
                            log.integrity === 'valid' ? "bg-emerald-50 text-emerald-600" :
                            log.integrity === 'warning' ? "bg-amber-50 text-amber-600" :
                            "bg-rose-50 text-rose-600"
                          )}>
                             {log.integrity === 'valid' ? <CheckCircle2 size={28} /> : 
                              log.integrity === 'warning' ? <AlertTriangle size={28} /> : <ShieldAlert size={28} />}
                          </div>
                          <div>
                             <h4 className="text-lg font-black text-slate-900 uppercase tracking-tight leading-none mb-1">{log.user}</h4>
                             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{log.role} Access Profile</p>
                          </div>
                       </div>

                       <div className="flex-1 grid grid-cols-2 md:grid-cols-3 gap-6 border-l border-r border-slate-50 px-8">
                          <div>
                             <p className="text-[9px] font-black text-slate-300 uppercase tracking-widest mb-1">{t.action}</p>
                             <p className="text-xs font-bold text-slate-700">{log.action}</p>
                          </div>
                          <div>
                             <p className="text-[9px] font-black text-slate-300 uppercase tracking-widest mb-1">Target ID</p>
                             <p className="text-xs font-bold text-slate-700 font-mono">{log.resourceId}</p>
                          </div>
                          <div>
                             <p className="text-[9px] font-black text-slate-300 uppercase tracking-widest mb-1">Timestamp</p>
                             <p className="text-xs font-bold text-slate-400 font-mono">{log.timestamp.split(' ')[1]}</p>
                          </div>
                       </div>

                       <div className="md:w-48 text-right flex flex-col items-end gap-2">
                          <div className="flex items-center gap-2">
                             <MapPin size={10} className="text-slate-300" />
                             <span className="text-[10px] font-bold text-slate-500 uppercase">{log.location}</span>
                          </div>
                          <div className="flex items-center gap-2">
                             <Fingerprint size={10} className="text-slate-300" />
                             <span className="text-[9px] font-mono font-bold text-indigo-400">{log.ip}</span>
                          </div>
                       </div>

                       <button className="p-3 bg-slate-50 text-slate-300 rounded-xl hover:text-indigo-600 transition-colors">
                          <MoreVertical size={20} />
                       </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
           </div>
        </div>

        {/* Sidebar: Regulatory Controls */}
        <div className="space-y-8">
           <div className="p-8 bg-emerald-600 rounded-[3rem] text-white shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-10 scale-150 rotate-12 transition-transform group-hover:scale-[1.7] duration-1000">
                 <Lock size={120} />
              </div>
              <div className="relative z-10">
                 <div className="flex items-center gap-3 mb-8">
                    <div className="p-2 bg-white/20 rounded-xl">
                       <Zap size={24} />
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-[0.2em]">Automated Policy</span>
                 </div>
                 <h3 className="text-2xl font-black mb-4 leading-tight">{t.dynamicConsent}</h3>
                 <p className="text-sm text-emerald-100 font-medium mb-8 leading-relaxed">
                   Enforcing patient-centric data sovereignty. Auto-redaction of PII for research clusters is currently <b>Enabled</b>.
                 </p>
                 <button className="w-full py-4 bg-white text-emerald-600 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-[1.02] transition-transform shadow-xl">
                    Update Shield Policies
                 </button>
              </div>
           </div>

           <BiometricStatus />

           <div className="p-8 bg-rose-600/10 border border-rose-500/20 rounded-[3rem] text-center border-dashed">
              <div className="w-16 h-16 bg-rose-500 text-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-xl shadow-rose-500/30">
                 <ShieldAlert size={32} />
              </div>
              <h3 className="text-lg font-black text-white mb-1 uppercase tracking-tight">{t.lockdown}</h3>
              <p className="text-xs text-rose-400/80 font-bold mb-6 italic leading-relaxed">
                Emergency capability to sever cross-border data transfer or localize regional shards.
              </p>
              <button className="w-full py-3 bg-rose-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-rose-700 transition-all ring-4 ring-rose-500/20">
                 Initialize Red-Line
              </button>
           </div>
        </div>
      </div>
    </div>
  );
}
