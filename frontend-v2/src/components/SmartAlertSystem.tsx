import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { AlertCircle, Zap, ArrowRight, ShieldAlert, X, CheckCircle2 } from 'lucide-react';
import { cn } from '../lib/utils';
import { useLanguage } from '../contexts/LanguageContext';

export interface Alert {
  id: string;
  type: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  timestamp: string;
}

interface SmartAlertSystemProps {
  alerts: Alert[];
  onDismiss: (id: string) => void;
}

export function SmartAlertSystem({ alerts, onDismiss }: SmartAlertSystemProps) {
  const { isRtl } = useLanguage();

  return (
    <div className="space-y-4 mb-10">
      <div className="flex items-center justify-between mb-2">
         <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-rose-100 flex items-center justify-center">
               <ShieldAlert size={16} className="text-rose-600" />
            </div>
            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-400">Decision Intelligence Queue</h3>
         </div>
         <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">{alerts.length} Active Protocols</span>
      </div>

      <AnimatePresence mode="popLayout">
        {alerts.map((alert) => (
          <motion.div
            key={alert.id}
            layout
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={cn(
              "p-6 rounded-[2rem] border-2 shadow-sm relative overflow-hidden group transition-all",
              alert.type === 'critical' 
                ? "bg-rose-50 border-rose-100" 
                : alert.type === 'warning'
                ? "bg-amber-50 border-amber-100"
                : "bg-indigo-50 border-indigo-100"
            )}
          >
            {/* Background Accent */}
            <div className={cn(
              "absolute top-0 right-0 p-8 opacity-[0.03] group-hover:scale-110 transition-transform",
              alert.type === 'critical' ? "text-rose-600" : "text-indigo-600"
            )}>
              <Zap size={100} />
            </div>

            <div className="relative z-10 flex items-start justify-between gap-6">
              <div className="flex gap-4">
                <div className={cn(
                  "w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 shadow-lg",
                  alert.type === 'critical' ? "bg-rose-600 text-white shadow-rose-200" : "bg-amber-500 text-white shadow-amber-200"
                )}>
                  {alert.type === 'critical' ? <AlertCircle size={24} /> : <Zap size={24} />}
                </div>
                
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h4 className={cn(
                      "text-sm font-black uppercase tracking-tight",
                      alert.type === 'critical' ? "text-rose-900" : "text-amber-900"
                    )}>{alert.title}</h4>
                    <span className="text-[9px] font-black opacity-30 uppercase tracking-widest">{alert.timestamp}</span>
                  </div>
                  <p className="text-xs font-medium text-slate-600 max-w-xl leading-relaxed">
                    {alert.description}
                  </p>
                  
                  {alert.actionLabel && (
                    <div className="flex gap-3 mt-4">
                       <button 
                         onClick={alert.onAction}
                         className={cn(
                           "px-5 py-2.5 rounded-xl text-[9px] font-black uppercase tracking-widest flex items-center gap-2 transition-all hover:scale-105 active:scale-95 shadow-xl",
                           alert.type === 'critical' ? "bg-rose-600 text-white shadow-rose-200" : "bg-indigo-600 text-white shadow-indigo-200"
                         )}
                       >
                         {alert.actionLabel} <ArrowRight size={14} />
                       </button>
                       <button className="px-5 py-2.5 bg-white border border-slate-100 text-slate-400 rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-slate-50 transition-all">
                          De-escalate
                       </button>
                    </div>
                  )}
                </div>
              </div>

              <button 
                onClick={() => onDismiss(alert.id)}
                className="p-2 text-slate-300 hover:text-rose-500 transition-colors"
              >
                <X size={18} />
              </button>
            </div>
          </motion.div>
        ))}
        {alerts.length === 0 && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }}
            className="p-10 border-2 border-dashed border-slate-100 rounded-[2.5rem] flex flex-col items-center justify-center text-center"
          >
             <CheckCircle2 size={32} className="text-emerald-500 mb-3 opacity-30" />
             <p className="text-xs font-black uppercase tracking-widest text-slate-300">No Critical Insights Requiring Immediate Action</p>
             <p className="text-[10px] font-medium text-slate-400 mt-1">System status is operational. All nodes are within safety parameters.</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
