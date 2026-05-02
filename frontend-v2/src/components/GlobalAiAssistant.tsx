import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Bot, X, Sparkles, Zap, ShieldCheck, Activity, MessageSquare } from 'lucide-react';
import { cn } from '../lib/utils';
import { useLanguage } from '../contexts/LanguageContext';

export function GlobalAiAssistant() {
  const { t, isRtl } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [insights, setInsights] = useState<string[]>([]);

  const toggleOpen = () => setIsOpen(!isOpen);

  useEffect(() => {
    if (isOpen) {
      setIsThinking(true);
      const timer = setTimeout(() => {
        setInsights([
          "Bio-Grid synchronization is at 98.4% efficiency.",
          "Network latency in Karkh region observed at 14ms (Optimal).",
          "3 new lab samples pending relational validation.",
          "Neural backbone suggests higher resource allocation for respiratory vectors today."
        ]);
        setIsThinking(false);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  return (
    <div className={cn(
      "fixed bottom-8 z-[60]",
      isRtl ? "left-8" : "right-8"
    )}>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20, filter: 'blur(10px)' }}
            animate={{ opacity: 1, scale: 1, y: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, scale: 0.9, y: 20, filter: 'blur(10px)' }}
            className="mb-6 w-[380px] bg-white rounded-[2.5rem] shadow-[0_40px_80px_-20px_rgba(0,0,0,0.3)] border border-slate-100 overflow-hidden"
          >
            {/* Header */}
            <div className="p-6 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-900/40">
                  <Bot size={20} className="animate-pulse" />
                </div>
                <div>
                  <h4 className="text-sm font-black uppercase tracking-tight">GULA Mini</h4>
                  <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Active Intelligence</p>
                </div>
              </div>
              <button 
                onClick={toggleOpen}
                className="p-2 hover:bg-white/10 rounded-full transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {/* Content */}
            <div className="p-8 space-y-6 max-h-[400px] overflow-y-auto custom-scrollbar">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={14} className="text-indigo-600" />
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Live Projections</span>
              </div>

              {isThinking ? (
                <div className="space-y-4 py-4">
                  {[1, 2, 3].map(i => (
                    <motion.div 
                      key={i}
                      initial={{ opacity: 0.3 }}
                      animate={{ opacity: [0.3, 0.6, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                      className="h-4 bg-slate-100 rounded-full w-full"
                    />
                  ))}
                  <p className="text-[10px] font-black text-center text-indigo-500 uppercase tracking-widest mt-4">Synthesizing Bio-Telemetry...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {insights.map((insight, i) => (
                    <motion.div 
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex gap-4 group hover:bg-indigo-50 transition-colors"
                    >
                      <div className="w-2 h-2 rounded-full bg-indigo-600 mt-1.5 shrink-0" />
                      <p className="text-sm font-medium text-slate-700 leading-relaxed group-hover:text-indigo-900">
                        {insight}
                      </p>
                    </motion.div>
                  ))}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 mt-8">
                <button className="p-4 bg-indigo-600 rounded-2xl text-white flex flex-col items-center gap-2 group hover:scale-[1.02] transition-all">
                  <Zap size={20} className="group-hover:fill-indigo-300" />
                  <span className="text-[9px] font-black uppercase tracking-widest">Execute Sync</span>
                </button>
                <button className="p-4 bg-slate-900 rounded-2xl text-white flex flex-col items-center gap-2 group hover:scale-[1.02] transition-all">
                  <MessageSquare size={20} className="group-hover:text-indigo-400" />
                  <span className="text-[9px] font-black uppercase tracking-widest">Full Chat</span>
                </button>
              </div>
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 text-center">
              <div className="flex items-center justify-center gap-2 text-[9px] font-black text-emerald-600 uppercase tracking-widest">
                <ShieldCheck size={12} /> Privacy Preserved Protocol v4
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={toggleOpen}
        className={cn(
          "w-16 h-16 rounded-full flex items-center justify-center shadow-2xl transition-all relative group",
          isOpen ? "bg-rose-500 text-white" : "bg-indigo-600 text-white shadow-indigo-500/40"
        )}
      >
        {isOpen ? <X size={28} /> : <Bot size={28} />}
        {!isOpen && (
          <div className="absolute inset-0 rounded-full animate-ping bg-indigo-500 opacity-20" />
        )}
        <div className="absolute -top-1 -right-1 w-5 h-5 bg-emerald-500 border-2 border-slate-900 rounded-full flex items-center justify-center">
          <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
        </div>
      </motion.button>
    </div>
  );
}
