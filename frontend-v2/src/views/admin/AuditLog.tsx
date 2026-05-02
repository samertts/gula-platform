import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  History, Search, Filter, ArrowUpRight, 
  Shield, User, Clock, AlertTriangle,
  Download, ExternalLink, Activity,
  Lock,
  Globe,
  Database
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '../../lib/utils';
import { AuditService } from '../../services/AuditService';
import { AuditLogViewer } from '../../components/AuditLogViewer';
import { AuditLogEntry } from '../../types/domain';

export const AuditLog: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      setIsLoading(true);
      const data = await AuditService.getLogs();
      setLogs(data as AuditLogEntry[]);
      setIsLoading(false);
    };
    fetchLogs();
  }, []);

  const stats = [
    { label: 'Integrity Points', value: '1,024', icon: Database, color: 'bg-indigo-50 text-indigo-600' },
    { label: 'Security Level', value: 'Level 4', icon: Shield, color: 'bg-emerald-50 text-emerald-600' },
    { label: 'Global Nodes', value: '882', icon: Globe, color: 'bg-blue-50 text-blue-600' },
    { label: 'Encryption', value: 'AES-256', icon: Lock, color: 'bg-amber-50 text-amber-600' }
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-indigo-600 mb-1">
            <Shield size={20} className="animate-pulse" />
            <span className="text-[10px] font-black uppercase tracking-[0.2em]">National Security Center</span>
          </div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight uppercase">System Audit Architecture.</h1>
          <p className="text-slate-500 font-medium max-w-md">Monitoring immutable transaction ledger and cross-entity activity with zero-trust enforcement.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="px-6 py-3 bg-white border border-slate-200 rounded-2xl text-slate-600 hover:bg-slate-50 transition-all shadow-sm flex items-center gap-2 font-black text-[10px] uppercase tracking-widest">
            <Download size={16} /> Export Governance Report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            key={i} 
            className="p-6 bg-white border border-slate-100 rounded-[32px] shadow-sm flex flex-col justify-between h-36 group hover:border-indigo-100 transition-all"
          >
             <div className={cn("inline-flex p-3 rounded-2xl transition-all group-hover:scale-110", stat.color)}>
                <stat.icon size={20} />
             </div>
             <div>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
                <p className="text-2xl font-black text-slate-900 tracking-tight uppercase">{stat.value}</p>
             </div>
          </motion.div>
        ))}
      </div>

      <AuditLogViewer logs={logs} isLoading={isLoading} />

      <div className="flex items-center justify-between p-8 bg-slate-900 rounded-[40px] text-white overflow-hidden relative">
         <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-30 pointer-events-none" />
         <div className="relative z-10">
            <h3 className="text-lg font-black uppercase tracking-tight mb-2">Immutable Ledger Status</h3>
            <p className="text-xs text-indigo-300 font-medium opacity-80">All logs are signed and stored in a multi-region encrypted cluster.</p>
         </div>
         <div className="relative z-10 flex items-center gap-4">
            <div className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-xl border border-white/10">
               <div className="w-2 h-2 bg-green-500 rounded-full animate-ping" />
               <span className="text-[10px] font-black uppercase tracking-widest">Global Sync Active</span>
            </div>
            <button className="px-6 py-3 bg-white text-slate-900 font-black text-[10px] uppercase tracking-[0.2em] rounded-xl hover:scale-105 transition-all">
               Verify Chain
            </button>
         </div>
      </div>
    </div>
  );
};
