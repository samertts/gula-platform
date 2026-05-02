import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  History, 
  Shield, 
  User, 
  ExternalLink, 
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { AuditLogEntry } from '../types/domain';
import { cn } from '../lib/utils';

interface AuditLogViewerProps {
  logs: AuditLogEntry[];
  isLoading?: boolean;
}

export const AuditLogViewer: React.FC<AuditLogViewerProps> = ({ logs, isLoading }) => {
  const { t } = useLanguage();

  const getSeverityStyles = (severity: AuditLogEntry['metadata']['severity']) => {
    switch (severity) {
      case 'critical': return 'bg-red-50 text-red-600 border-red-100';
      case 'warning': return 'bg-amber-50 text-amber-600 border-amber-100';
      default: return 'bg-blue-50 text-blue-600 border-blue-100';
    }
  };

  const getSeverityIcon = (severity: AuditLogEntry['metadata']['severity']) => {
    switch (severity) {
      case 'critical': return <Shield className="text-red-500" size={14} />;
      case 'warning': return <AlertTriangle className="text-amber-500" size={14} />;
      default: return <Info className="text-blue-500" size={14} />;
    }
  };

  return (
    <div className="bg-white rounded-[40px] border border-slate-100 shadow-sm overflow-hidden">
      <div className="p-8 border-b border-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-4">
           <div className="w-12 h-12 bg-slate-900 text-white rounded-2xl flex items-center justify-center shadow-xl shadow-slate-100">
              <History size={24} />
           </div>
           <div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight uppercase">Immutable System Audit Logs</h2>
              <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mt-1">Legally binding execution trace</p>
           </div>
        </div>

        <div className="flex items-center gap-3">
           <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input 
                type="text" 
                placeholder="Search hash, user, or action..."
                className="pl-12 pr-4 py-3 bg-slate-50 border-none rounded-2xl text-xs font-bold focus:ring-4 focus:ring-slate-100 transition-all w-64"
              />
           </div>
           <button className="p-3 bg-white border border-slate-100 rounded-2xl text-slate-400 hover:text-slate-900 transition-all">
              <Filter size={18} />
           </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-slate-50/50">
              <th className="px-8 py-4 text-[9px] font-black uppercase tracking-widest text-slate-400">Timestamp</th>
              <th className="px-8 py-4 text-[9px] font-black uppercase tracking-widest text-slate-400">Actor</th>
              <th className="px-8 py-4 text-[9px] font-black uppercase tracking-widest text-slate-400">Action</th>
              <th className="px-8 py-4 text-[9px] font-black uppercase tracking-widest text-slate-400">Resource</th>
              <th className="px-8 py-4 text-[9px] font-black uppercase tracking-widest text-slate-400">Integrity Hash</th>
              <th className="px-8 py-4 text-[9px] font-black uppercase tracking-widest text-slate-400"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {logs.map((log) => (
              <motion.tr 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                key={log.id} 
                className="group hover:bg-slate-50/80 transition-colors"
              >
                <td className="px-8 py-5">
                   <div className="flex flex-col">
                      <span className="text-[10px] font-black text-slate-900">{new Date(log.timestamp).toLocaleDateString()}</span>
                      <span className="text-[9px] font-bold text-slate-400">{new Date(log.timestamp).toLocaleTimeString()}</span>
                   </div>
                </td>
                <td className="px-8 py-5">
                   <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
                         <User size={14} />
                      </div>
                      <div className="flex flex-col min-w-0">
                         <span className="text-[10px] font-black text-slate-900 truncate">Samer (Root)</span>
                         <span className="text-[9px] font-bold text-slate-400 truncate">{log.userEmail}</span>
                      </div>
                   </div>
                </td>
                <td className="px-8 py-5">
                   <div className={cn("inline-flex items-center gap-2 px-3 py-1 rounded-lg border text-[9px] font-black uppercase tracking-widest", getSeverityStyles(log.metadata.severity))}>
                      {getSeverityIcon(log.metadata.severity)}
                      {log.action.replace('_', ' ')}
                   </div>
                </td>
                <td className="px-8 py-5">
                   <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest bg-slate-100 px-2 py-0.5 rounded-md">
                        {log.resource}
                      </span>
                      <span className="text-[10px] font-medium text-slate-400">#{log.resourceId.slice(0, 8)}</span>
                   </div>
                </td>
                <td className="px-8 py-5">
                   <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full" />
                      <code className="text-[9px] font-mono text-slate-400">SHA256: {log.id.slice(0, 12)}...</code>
                   </div>
                </td>
                <td className="px-8 py-5 text-right">
                   <button className="p-2 text-slate-300 hover:text-indigo-600 transition-colors">
                      <ExternalLink size={16} />
                   </button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>

        {logs.length === 0 && !isLoading && (
          <div className="py-32 text-center">
             <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6">
                <Shield className="text-slate-200" size={32} />
             </div>
             <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">No Security Events</h3>
             <p className="text-xs text-slate-400 mt-2">All data governance protocols are active and optimal.</p>
          </div>
        )}
      </div>
    </div>
  );
};
