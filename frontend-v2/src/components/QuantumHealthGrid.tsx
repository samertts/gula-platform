import React from 'react';
import { motion } from 'motion/react';
import { Shield, Fingerprint, Lock, Globe, Zap, Network, Database, Cpu } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function QuantumHealthGrid() {
  const { t } = useLanguage();

  const nodes = [
    { icon: Fingerprint, label: t.continuousAuth, status: 'Active', color: 'text-indigo-400' },
    { icon: Lock, label: t.zeroTrust, status: 'Enforced', color: 'text-emerald-400' },
    { icon: Shield, label: t.selfSovereignIdentity, status: 'Verified', color: 'text-indigo-400' },
    { icon: Database, label: t.immutableAudit, status: 'Synced', color: 'text-rose-400' },
  ];

  return (
    <div className="bg-slate-900 rounded-[3rem] p-8 text-white relative overflow-hidden group border border-white/5">
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/10 to-transparent pointer-events-none" />
      
      {/* Background Grid Animation */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none">
        <div className="grid grid-cols-12 h-full w-full">
           {Array.from({ length: 48 }).map((_, i) => (
             <div key={i} className="border-r border-b border-white h-12 w-full" />
           ))}
        </div>
      </div>

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-12">
           <div>
              <h3 className="text-xl font-black uppercase tracking-tight">{t.quantumEncryption}</h3>
              <div className="flex items-center gap-2 mt-1">
                 <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                 <span className="text-[10px] font-black uppercase tracking-widest text-emerald-400">Post-Quantum Cryptography Enabled</span>
              </div>
           </div>
           <div className="p-3 bg-white/5 rounded-2xl border border-white/10 text-indigo-400 shadow-xl shadow-indigo-900/20">
              <Network size={24} />
           </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
           {nodes.map((node, i) => (
             <motion.div 
               key={node.label}
               initial={{ opacity: 0, scale: 0.9 }}
               animate={{ opacity: 1, scale: 1 }}
               transition={{ delay: i * 0.1 }}
               className="p-6 bg-white/5 rounded-[2rem] border border-white/5 hover:bg-white/10 hover:border-white/10 transition-all group/node"
             >
                <node.icon size={20} className={cn("mb-4", node.color)} />
                <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-1">{node.status}</p>
                <h4 className="text-sm font-bold leading-tight">{node.label}</h4>
             </motion.div>
           ))}
        </div>

        <div className="p-8 bg-indigo-600/10 rounded-[2.5rem] border border-indigo-500/20 relative overflow-hidden">
           <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/20 blur-[50px] -mr-16 -mt-16" />
           <div className="relative z-10 flex flex-col lg:flex-row items-center gap-8">
              <div className="flex-1">
                 <div className="flex items-center gap-3 mb-4">
                    <Zap size={18} className="text-indigo-400" />
                    <h4 className="text-sm font-black uppercase tracking-tight">{t.realtimeSync}</h4>
                 </div>
                 <p className="text-xs text-white/60 leading-relaxed font-medium">
                    The health identity grid is synchronizing across 12 region-nodes using low-latency orbital arrays. Identity integrity verified with zero-knowledge proofs.
                 </p>
              </div>
              <div className="flex items-center gap-4">
                 <div className="text-right">
                    <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Latency</p>
                    <p className="text-2xl font-black font-mono">1.2ms</p>
                 </div>
                 <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center border border-white/10">
                    <Globe size={24} className="text-white/40" />
                 </div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
