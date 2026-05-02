import React, { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  ShieldAlert, ShieldCheck, Fingerprint, Lock, 
  Smartphone, Monitor, Globe, Clock, 
  Eye, Download, Key, AlertTriangle,
  History as HistoryIcon, Info, ChevronRight, Activity as ActivityIcon,
  MapPin
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';

export function SecurityAuditView() {
  const { t } = useLanguage();
  const [mfaEnabled, setMfaEnabled] = useState(true);

  const activeSessions = [
    { id: 's1', device: 'MacBook Pro 16"', location: 'Riyadh, SA', ip: '192.168.1.45', status: 'current', icon: Monitor },
    { id: 's2', device: 'iPhone 15 Pro', location: 'Jeddah, SA', ip: '92.45.12.3', status: 'active', icon: Smartphone },
  ];

  const auditLogs = [
    { id: 'l1', action: 'Medical Data Accessed', actor: 'Dr. Sarah Smith', context: 'Center B - Oncology', timestamp: '2024-04-20 14:22:10', risk: 'low' },
    { id: 'l2', action: 'Identity Verification (LoA3)', actor: 'Samer (You)', context: 'Self-Service Portal', timestamp: '2024-04-18 09:12:00', risk: 'low' },
    { id: 'l3', action: 'Sensitive Data Export', actor: 'Admin Admin', context: 'Security Override', timestamp: '2024-04-15 22:45:00', risk: 'medium' },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 min-h-screen bg-slate-50/30">
      <div className="flex items-center justify-between">
        <div>
           <h1 className="text-3xl font-black text-slate-900 tracking-tight">{t.security} & {t.auditTrail}</h1>
           <p className="text-slate-500 font-medium">Manage your digital identity and track data access footprint.</p>
        </div>
        <div className="flex gap-4">
           <div className="px-6 py-3 bg-white border border-slate-200 rounded-2xl flex items-center gap-3">
              <ShieldCheck className="text-emerald-500" size={20} />
              <span className="text-xs font-black text-slate-900 tracking-widest uppercase">Safe & Hardened</span>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
         <div className="lg:col-span-8 space-y-8">
            {/* MFA & Hardening Hub */}
            <div className="bg-white rounded-[2.5rem] border border-slate-200 p-10 shadow-sm relative overflow-hidden">
               <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
                  <Fingerprint size={180} />
               </div>
               <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-10">
                  <div className="space-y-6">
                     <div className="w-16 h-16 bg-indigo-50 rounded-[1.5rem] flex items-center justify-center text-indigo-600 shadow-inner">
                        <Key size={32} />
                     </div>
                     <h3 className="text-2xl font-bold tracking-tight">Identity Hardening</h3>
                     <p className="text-sm text-slate-500 leading-relaxed">
                        Enhance your privacy with biometric multi-factor authentication. Every clinical access request will require your direct approval.
                     </p>
                     
                     <div className="flex items-center justify-between p-6 bg-slate-50 rounded-3xl border border-slate-100">
                        <div className="flex items-center gap-4">
                           <Smartphone className="text-slate-400" />
                           <div>
                              <p className="text-sm font-bold text-slate-900">{t.mfa}</p>
                              <p className="text-[10px] font-bold text-emerald-600 uppercase">Protection Active</p>
                           </div>
                        </div>
                        <button 
                           onClick={() => setMfaEnabled(!mfaEnabled)}
                           className={cn(
                              "w-14 h-8 rounded-full p-1 transition-all",
                              mfaEnabled ? "bg-indigo-600" : "bg-slate-300"
                           )}
                        >
                           <motion.div 
                              animate={{ x: mfaEnabled ? 24 : 0 }}
                              className="w-6 h-6 bg-white rounded-full shadow-md"
                           />
                        </button>
                     </div>
                  </div>

                  <div className="space-y-6 flex flex-col justify-center">
                     <div className="space-y-4">
                        {[
                           { label: 'Passkey Support', status: 'Enabled', icon: ShieldCheck, color: 'text-emerald-500' },
                           { label: 'Email Encryption', status: 'PGP/Active', icon: Lock, color: 'text-emerald-500' },
                           { label: 'Panic Mode Access', status: 'Ready', icon: AlertTriangle, color: 'text-amber-500' }
                        ].map((item, idx) => (
                           <div key={idx} className="flex items-center justify-between p-4 border border-slate-100 rounded-2xl hover:bg-slate-50 transition-all cursor-pointer group">
                             <div className="flex items-center gap-3">
                                <item.icon className={item.color} size={18} />
                                <span className="text-xs font-bold text-slate-700">{item.label}</span>
                             </div>
                             <span className="text-[9px] font-black uppercase text-slate-400 group-hover:text-indigo-600">{item.status}</span>
                           </div>
                        ))}
                     </div>
                  </div>
               </div>
            </div>

            {/* Audit Trail - Action Engine component */}
            <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden">
               <div className="p-8 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                     <HistoryIcon className="text-slate-400" />
                     <h3 className="text-xl font-bold tracking-tight">{t.auditTrail}</h3>
                  </div>
                  <button className="flex items-center gap-2 px-6 py-2 bg-slate-900 text-white rounded-xl font-bold text-xs uppercase tracking-widest hover:scale-105 transition-all">
                     <Download size={14} /> Export Logs
                  </button>
               </div>
               <div className="p-8 space-y-4">
                  {auditLogs.map((log) => (
                     <div key={log.id} className="p-6 bg-slate-50/50 hover:bg-white border border-slate-100 hover:border-indigo-100 rounded-[2rem] transition-all flex items-center justify-between group">
                        <div className="flex items-center gap-6">
                           <div className={cn(
                              "w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-indigo-50",
                              log.risk === 'medium' ? "bg-amber-500" : "bg-slate-900"
                           )}>
                              {log.risk === 'medium' ? <AlertTriangle size={20} /> : <Eye size={20} />}
                           </div>
                           <div>
                              <p className="font-bold text-slate-900">{log.action}</p>
                              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{log.actor} • {log.context}</p>
                           </div>
                        </div>
                        <div className="text-right">
                           <p className="text-[10px] font-black text-slate-400 mb-1">{log.timestamp}</p>
                           <span className={cn(
                              "text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded",
                              log.risk === 'medium' ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"
                           )}>
                              {log.risk} Risk
                           </span>
                        </div>
                     </div>
                  ))}
               </div>
            </div>
         </div>

         <div className="lg:col-span-4 space-y-8">
            {/* Active Sessions */}
            <div className="bg-slate-900 rounded-[2.5rem] p-8 text-white shadow-2xl shadow-slate-200">
               <h3 className="text-lg font-bold mb-8 flex items-center gap-3">
                  <Globe className="text-indigo-400" /> {t.activeSessions}
               </h3>
               <div className="space-y-6">
                  {activeSessions.map(session => (
                     <div key={session.id} className="relative pl-14 group">
                        <div className="absolute left-0 top-0 w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center group-hover:bg-indigo-500 group-hover:text-white transition-all">
                           <session.icon size={20} />
                        </div>
                        <div className="flex items-center justify-between">
                           <div>
                              <p className="font-bold text-sm">{session.device}</p>
                              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-loose">{session.location} • {session.ip}</p>
                           </div>
                           {session.status === 'current' && (
                              <span className="text-[9px] font-black text-indigo-400 border border-indigo-400/30 px-2 py-1 rounded">THIS DEVICE</span>
                           )}
                        </div>
                     </div>
                  ))}
               </div>
               <button className="w-full mt-10 py-4 border-2 border-white/10 hover:border-red-500/50 hover:bg-red-500/10 text-white rounded-2xl font-bold flex items-center justify-center gap-3 transition-colors">
                  Terminate All Other Sessions
               </button>
            </div>

            {/* Privacy Score Card */}
            <div className="bg-indigo-600 rounded-[2.5rem] p-8 text-white shadow-2xl shadow-indigo-100 relative overflow-hidden group">
               <div className="absolute bottom-0 right-0 translate-x-1/4 translate-y-1/4 opacity-10 group-hover:scale-110 transition-transform">
                  <ShieldCheck size={140} />
               </div>
               <h3 className="text-lg font-bold mb-4">Security Posture</h3>
               <div className="flex items-baseline gap-2 mb-6">
                  <span className="text-4xl font-black">94%</span>
                  <span className="text-xs font-bold text-indigo-200 uppercase tracking-widest">Resilience</span>
               </div>
               <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden mb-6">
                  <div className="w-[94%] h-full bg-white shadow-[0_0_15px_rgba(255,255,255,0.7)]" />
               </div>
               <p className="text-sm text-indigo-100 leading-relaxed border-t border-white/10 pt-6">
                  Your profile is fully hardened. All clinical data access requires real-time LoA-3 verification.
               </p>
            </div>
         </div>
      </div>
    </div>
  );
}
