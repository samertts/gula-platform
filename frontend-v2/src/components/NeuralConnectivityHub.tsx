import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Radio, Globe, Zap, Cpu, Server, Activity } from 'lucide-react';
import { cn } from '../lib/utils';

interface Node {
  id: string;
  name: string;
  type: 'analyzer' | 'storage' | 'cloud';
  status: 'active' | 'syncing' | 'idle';
  load: number;
  packets: number;
}

const INITIAL_NODES: Node[] = [
  { id: 'N-BA', name: 'Basrah Core', type: 'analyzer', status: 'active', load: 82, packets: 1420 },
  { id: 'N-BG', name: 'Baghdad Central', type: 'cloud', status: 'active', load: 95, packets: 5600 },
  { id: 'N-NI', name: 'Nineveh Node', type: 'analyzer', status: 'syncing', load: 45, packets: 890 },
  { id: 'N-ER', name: 'Erbil Bio-Grid', type: 'analyzer', status: 'active', load: 68, packets: 2100 },
  { id: 'N-ST', name: 'Strategic Reserve', type: 'storage', status: 'idle', load: 12, packets: 0 },
];

export function NeuralConnectivityHub() {
  const [nodes, setNodes] = useState<Node[]>(INITIAL_NODES);
  const [activePulse, setActivePulse] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setNodes(prev => prev.map(node => ({
        ...node,
        load: Math.min(100, Math.max(0, node.load + (Math.random() * 10 - 5))),
        packets: node.status === 'active' ? node.packets + Math.floor(Math.random() * 50) : node.packets,
        status: Math.random() > 0.95 ? (node.status === 'idle' ? 'active' : 'idle') : node.status
      })));
      setActivePulse(prev => (prev + 1) % 100);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-900 rounded-[3rem] p-10 text-white relative overflow-hidden shadow-2xl">
      <div className="absolute top-0 right-0 p-12 opacity-[0.03] pointer-events-none scale-150">
         <Radio size={300} />
      </div>
      
      <div className="relative z-10 flex flex-col lg:flex-row gap-12">
        <div className="lg:w-1/3 space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-indigo-600 rounded-[1.5rem] flex items-center justify-center shadow-2xl shadow-indigo-500/20">
               <Globe size={28} className="text-white animate-pulse" />
            </div>
            <div>
               <h3 className="text-2xl font-black uppercase tracking-tight">Neural Connectivity</h3>
               <p className="text-indigo-400 text-[10px] font-black uppercase tracking-[0.2em]">National Bio-Grid Sync v12.4</p>
            </div>
          </div>
          <p className="text-sm text-slate-400 font-medium leading-relaxed">
            Real-time telemetry from remote diagnostic nodes. Relational data validation is being processed through GULA's neural backbone.
          </p>
          <div className="grid grid-cols-2 gap-4">
             <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
                <span className="text-[9px] font-black text-slate-500 uppercase block mb-1">Global Load</span>
                <div className="text-xl font-black">84.2%</div>
             </div>
             <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
                <span className="text-[9px] font-black text-slate-500 uppercase block mb-1">Grid Latency</span>
                <div className="text-xl font-black">12ms</div>
             </div>
          </div>
        </div>

        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
           {nodes.map((node) => (
             <motion.div 
               key={node.id}
               className={cn(
                 "p-6 rounded-[2rem] border transition-all relative overflow-hidden group hover:scale-[1.02]",
                 node.status === 'active' ? "bg-indigo-600 border-indigo-500" : "bg-white/5 border-white/10"
               )}
             >
                <div className="flex justify-between items-start mb-4">
                   <div className={cn(
                     "p-3 rounded-xl",
                     node.status === 'active' ? "bg-white/20" : "bg-white/5"
                   )}>
                      {node.type === 'analyzer' ? <Activity size={18} /> : 
                       node.type === 'cloud' ? <Server size={18} /> : <Cpu size={18} />}
                   </div>
                   <div className="flex items-center gap-1.5">
                      <div className={cn(
                        "w-1.5 h-1.5 rounded-full animate-pulse",
                        node.status === 'active' ? "bg-emerald-400" : 
                        node.status === 'syncing' ? "bg-amber-400" : "bg-slate-500"
                      )} />
                      <span className="text-[8px] font-black uppercase tracking-widest opacity-60">{node.status}</span>
                   </div>
                </div>

                <div className="space-y-1 mb-6">
                   <h4 className="text-xs font-black uppercase tracking-tight">{node.name}</h4>
                   <p className="text-[8px] font-black opacity-50 uppercase tracking-widest">{node.id}</p>
                </div>

                <div className="space-y-3">
                   <div className="flex justify-between text-[9px] font-black uppercase opacity-60">
                      <span>Node Load</span>
                      <span>{Math.round(node.load)}%</span>
                   </div>
                   <div className="w-full bg-black/20 h-1 rounded-full overflow-hidden">
                      <motion.div 
                         initial={{ width: 0 }}
                         animate={{ width: `${node.load}%` }}
                         className={cn(
                           "h-full transition-all",
                           node.status === 'active' ? "bg-white" : "bg-indigo-500"
                         )}
                      />
                   </div>
                </div>

                {node.status === 'active' && (
                  <div className="absolute bottom-4 right-6 flex flex-col items-end">
                     <span className="text-[8px] font-black uppercase opacity-40">Telemetry Stream</span>
                     <span className="text-[10px] font-black">{node.packets.toLocaleString()} PKTS</span>
                  </div>
                )}
             </motion.div>
           ))}
        </div>
      </div>

      {/* Visual pulse line at the bottom */}
      <div className="absolute bottom-0 left-0 w-full h-1 bg-white/5 overflow-hidden">
         <motion.div 
           className="w-1/4 h-full bg-indigo-500 blur-sm"
           animate={{ x: ['-100%', '400%'] }}
           transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
         />
      </div>
    </div>
  );
}
