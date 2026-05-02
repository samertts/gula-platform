import React from 'react';
import { motion } from 'motion/react';
import { Activity, Zap, Shield, Heart, BrainCircuit } from 'lucide-react';
import { cn } from '../../lib/utils';

interface DigitalTwinProps {
  score: number;
  indicators: { label: string; value: number; color: string; icon: any }[];
  className?: string;
}

export function DigitalTwin({ score, indicators, className }: DigitalTwinProps) {
  return (
    <div className={cn("relative p-8 bg-slate-900 rounded-[3rem] overflow-hidden group", className)}>
      {/* Background Neural Network Simulation */}
      <div className="absolute inset-0 opacity-10">
         {[1,2,3,4,5].map(i => (
           <motion.div 
             key={i}
             animate={{ 
               scale: [1, 1.2, 1],
               opacity: [0.1, 0.3, 0.1],
               rotate: [0, 360]
             }}
             transition={{ duration: 10 + i * 2, repeat: Infinity, ease: 'linear' }}
             className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 border border-indigo-500/30 rounded-full"
             style={{ width: i * 80, height: i * 80 }}
           />
         ))}
      </div>

      <div className="relative z-10 flex flex-col md:flex-row items-center gap-12">
         {/* Main Sphere */}
         <div className="relative">
            <motion.div 
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
              className="w-64 h-64 border-2 border-dashed border-indigo-500/20 rounded-full p-4 p-8"
            >
               <div className="w-full h-full border-4 border-indigo-500/50 rounded-full flex items-center justify-center relative overflow-hidden shadow-[0_0_50px_rgba(79,70,229,0.3)]">
                  <div className="absolute inset-0 bg-indigo-600/10 backdrop-blur-2xl" />
                  <motion.div 
                    animate={{ y: [0, -10, 0] }}
                    transition={{ duration: 4, repeat: Infinity }}
                    className="relative z-10 flex flex-col items-center"
                  >
                     <span className="text-6xl font-black text-white tracking-tighter">{score}</span>
                     <span className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em]">Neural Sync</span>
                  </motion.div>

                  {/* Pulsing Core */}
                  <motion.div 
                    animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.6, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="absolute inset-0 bg-indigo-500/20 blur-2xl"
                  />
               </div>
            </motion.div>

            {/* Orbiting Elements */}
            {indicators.map((ind, i) => (
              <motion.div
                key={ind.label}
                animate={{ 
                  rotate: [0, 360] 
                }}
                transition={{ duration: 15 + i * 5, repeat: Infinity, ease: 'linear' }}
                className="absolute top-1/2 left-1/2 -ml-32 -mt-32 w-64 h-64 pointer-events-none"
              >
                 <motion.div 
                   animate={{ scale: [1, 1.1, 1] }}
                   transition={{ duration: 3, delay: i * 0.5, repeat: Infinity }}
                   className={cn(
                     "absolute top-0 left-1/2 -translate-x-1/2 w-8 h-8 rounded-xl flex items-center justify-center p-2 border shadow-lg backdrop-blur-xl pointer-events-auto cursor-help",
                     ind.color === 'emerald' ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-400" :
                     ind.color === 'indigo' ? "bg-indigo-500/20 border-indigo-500/40 text-indigo-400" :
                     "bg-amber-500/20 border-amber-500/40 text-amber-400"
                   )}
                 >
                    <ind.icon size={16} />
                 </motion.div>
              </motion.div>
            ))}
         </div>

         {/* Stats Panel */}
         <div className="flex-1 space-y-6 w-full">
            <div className="flex items-center justify-between">
               <h3 className="text-xl font-black text-white uppercase tracking-tight">Bio-Neural Matrix</h3>
               <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Active Link</span>
               </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
               {indicators.map((ind) => (
                 <div key={ind.label} className="p-4 bg-white/5 border border-white/5 rounded-2xl hover:bg-white/10 transition-all group/stat">
                    <div className="flex items-center justify-between mb-2">
                       <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{ind.label}</span>
                       <span className={cn("text-sm font-black", `text-${ind.color}-400`)}>{ind.value}%</span>
                    </div>
                    <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                       <motion.div 
                         initial={{ width: 0 }}
                         animate={{ width: `${ind.value}%` }}
                         className={cn("h-full rounded-full", `bg-${ind.color}-500 shadow-[0_0_10px_rgba(var(--${ind.color}-500-rgb),0.5)]`)} 
                       />
                    </div>
                 </div>
               ))}
            </div>

            <div className="p-4 bg-indigo-600/20 border border-indigo-500/30 rounded-2xl">
               <div className="flex items-center gap-3 mb-2">
                  <BrainCircuit size={16} className="text-indigo-400" />
                  <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">AI Synthesis</span>
               </div>
               <p className="text-xs text-indigo-100/60 leading-relaxed italic">
                 "Cellular regeneration appears optimal. Your neural fidelity is within the 98th percentile for your demographic segment."
               </p>
            </div>
         </div>
      </div>
    </div>
  );
}
