import React, { useState, useRef, useEffect } from 'react';
import { Search, BrainCircuit, Sparkles, Send, Stethoscope, AlertTriangle, ArrowRight, User, Bot } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useLanguage } from '../../contexts/LanguageContext';
import { getClinicalInsight } from '../../services/geminiService';
import { cn } from '../../lib/utils';

export function SymptomChecker() {
  const { t } = useLanguage();
  const [messages, setMessages] = useState<{ role: 'user' | 'ai'; text: string }[]>([
    { role: 'ai', text: "GULA Health Intelligence online. Describe your symptoms for a triage analysis." }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleCheck = async (customInput?: string) => {
    const messageText = customInput || input;
    if (!messageText.trim()) return;
    
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: messageText }]);
    setLoading(true);
    
    const insight = await getClinicalInsight(
      `Symptom description: ${messageText}. Provide triage: Urgency (Emergency/Urgent/Non-Urgent), potential patterns, and next steps.`,
      "System: Medical Triage Support. Safety first. Always include disclaimer."
    );
    
    setMessages(prev => [...prev, { role: 'ai', text: insight }]);
    setLoading(false);
  };

  return (
    <div className="bg-slate-900 rounded-[3rem] p-6 md:p-10 text-white relative overflow-hidden group min-h-[600px] flex flex-col">
      <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none group-hover:scale-110 transition-transform">
        <Stethoscope size={200} />
      </div>

      <div className="relative z-10 flex-1 flex flex-col">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-indigo-500/20 border border-indigo-500/30 rounded-full mb-6 w-fit">
          <Sparkles size={14} className="text-indigo-400" />
          <span className="text-[10px] font-black uppercase tracking-[0.2em]">{t.symptomChecker}</span>
        </div>

        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto space-y-6 mb-8 pr-2 no-scrollbar max-h-[450px]"
        >
          {messages.map((msg, i) => (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={i}
              className={cn(
                "flex items-start gap-4",
                msg.role === 'user' ? "flex-row-reverse" : "flex-row"
              )}
            >
              <div className={cn(
                "w-8 h-8 rounded-xl flex items-center justify-center shrink-0",
                msg.role === 'user' ? "bg-white/10" : "bg-indigo-600 shadow-xl"
              )}>
                {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
              </div>
              <div className={cn(
                "p-4 rounded-2xl text-xs leading-relaxed max-w-[85%]",
                msg.role === 'user' 
                  ? "bg-white/5 text-white rounded-tr-none border border-white/5" 
                  : "bg-white/10 text-slate-100 rounded-tl-none border border-white/10 shadow-sm"
              )}>
                {msg.text}
              </div>
            </motion.div>
          ))}
          {loading && (
            <div className="flex items-center gap-3 text-indigo-400">
               <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                  <BrainCircuit size={16} />
               </motion.div>
               <span className="text-[10px] font-black uppercase tracking-widest animate-pulse">GULA Analyzing...</span>
            </div>
          )}
        </div>

        <div className="relative group/input mt-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleCheck()}
            placeholder={t.describeSymptom}
            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-6 pr-14 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all shadow-xl"
          />
          <button
            onClick={() => handleCheck()}
            disabled={loading || !input.trim()}
            className="absolute right-2 top-2 bottom-2 px-4 bg-indigo-600 text-white rounded-xl shadow-lg hover:scale-105 active:scale-95 transition-all disabled:opacity-50"
          >
            <Send size={18} />
          </button>
        </div>

        <div className="mt-6 flex items-center gap-3 text-slate-500">
          <AlertTriangle size={14} className="text-amber-500" />
          <p className="text-[9px] font-bold uppercase tracking-widest italic opacity-60">
            AI Triage is for guidance only. In an emergency, call 991 or head to the nearest ER.
          </p>
        </div>
      </div>
    </div>
  );
}
