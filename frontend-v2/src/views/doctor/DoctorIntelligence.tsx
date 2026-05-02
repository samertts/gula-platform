import React, { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Sparkles, Send, Bot, User, 
  Stethoscope, Microscope, Beaker,
  AlertCircle, Activity as ActivityIcon, BrainCircuit,
  MessageSquare, History as HistoryIcon, FileText, Zap,
  Settings
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { getClinicalInsight } from '../../services/geminiService';
import { cn } from '../../lib/utils';
import { OrganAnalysis } from '../../components/OrganAnalysis';
import { ExplainableAI } from '../../components/ExplainableAI';

import { DoctorPriorityQueue } from '../../components/doctor/DoctorPriorityQueue';
import { AdvancedTriageDetails } from '../../components/doctor/AdvancedTriageDetails';

export function DoctorIntelligence() {
  const { t } = useLanguage();
  const [activeView, setActiveView] = useState<'chat' | 'analysis' | 'explainable' | 'triage'>('chat');
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState<{ role: 'user' | 'ai'; text: string; data?: any }[]>([
    { role: 'ai', text: "GULA Medical Brain (v4.0) initialized. I have indexed the current patient's clinical history, recent lab results, and local disease trends. How can I assist with your clinical reasoning today?" }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setIsTyping(true);

    const context = "Current Patient Profile: Male, 52y. History of Hypertension. Current Symptoms: Fatigue, persistent cough (3 weeks), night sweats. Lab: CRP 42 (High), WBC 11.2 (Slightly high). Chest X-Ray: Infiltrate in RUL.";
    const response = await getClinicalInsight(userMessage, context);
    
    setMessages(prev => [...prev, { role: 'ai', text: response }]);
    setIsTyping(false);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto h-[calc(100vh-120px)] flex gap-8">
      {/* Sidebar Tooling */}
      <div className="hidden lg:flex w-80 flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
         <div className="bg-slate-900 rounded-[32px] p-6 text-white shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-[50px] -mr-16 -mt-16 group-hover:scale-150 transition-transform" />
            <h3 className="text-sm font-black uppercase tracking-widest text-indigo-400 mb-4 relative z-10">Patient Evidence</h3>
            <div className="space-y-3 relative z-10">
               <div className="p-3 bg-white/5 rounded-xl border border-white/10 flex items-center gap-3 hover:bg-white/10 transition-colors">
                  <div className="text-emerald-400"><Microscope size={16} /></div>
                  <span className="text-xs font-medium">Lab Results (3) Integrated</span>
               </div>
               <div className="p-3 bg-white/5 rounded-xl border border-white/10 flex items-center gap-3 hover:bg-white/10 transition-colors">
                  <div className="text-amber-400"><FileText size={16} /></div>
                  <span className="text-xs font-medium">Imaging Metadata Indexed</span>
               </div>
               <div className="p-3 bg-white/5 rounded-xl border border-white/10 flex items-center gap-3 hover:bg-white/10 transition-colors">
                  <div className="text-indigo-400"><HistoryIcon size={16} /></div>
                  <span className="text-xs font-medium">Family History Contextualized</span>
               </div>
            </div>
         </div>

         <div className="bg-white rounded-[32px] p-6 border border-slate-200 shadow-sm">
            <h3 className="text-sm font-black uppercase tracking-widest text-slate-400 mb-4">Reasoning Modes</h3>
            <div className="space-y-2">
               {[
                 { id: 'chat', label: 'Clinical Chat Engine' },
                 { id: 'analysis', label: t.organAnalysis },
                 { id: 'explainable', label: t.explainableAI },
                 { id: 'triage', label: t.priorityQueue },
               ].map((mode) => (
                 <button 
                   key={mode.id}
                   onClick={() => setActiveView(mode.id as any)}
                   className={cn(
                     "w-full text-left p-4 rounded-2xl transition-all text-xs font-bold border flex items-center justify-between group",
                     activeView === mode.id ? "bg-indigo-600 text-white border-indigo-500 shadow-lg shadow-indigo-100" : "bg-slate-50 text-slate-600 border-transparent hover:border-indigo-100"
                   )}
                 >
                   <span>{mode.label}</span>
                   <Zap size={12} className={cn("transition-opacity", activeView === mode.id ? "opacity-100" : "opacity-0")} />
                 </button>
               ))}
            </div>
         </div>

         <div className="mt-auto p-6 bg-slate-900 border border-slate-800 rounded-[32px] text-white overflow-hidden relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="flex items-center gap-3 mb-2 text-indigo-400 relative z-10">
               <Zap size={16} className="animate-pulse" />
               <h4 className="text-xs font-black uppercase tracking-widest">Model Status</h4>
            </div>
            <p className="text-[10px] text-slate-400 font-medium relative z-10 italic">Secured: GULA-Clinical-L4. Processing latent knowledge via regional RAG nodes. Ready for inference.</p>
         </div>
      </div>

      {/* Main Intelligence Interface */}
      <div className="flex-1 bg-white rounded-[40px] border border-slate-200 shadow-xl overflow-hidden flex flex-col relative">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-white z-10 shrink-0">
           <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-100">
                 <BrainCircuit size={24} />
              </div>
              <div>
                 <h2 className="text-lg font-bold text-slate-900 tracking-tight">Intelligence Canvas</h2>
                 <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Augmented Medical Reasoning</p>
              </div>
           </div>
           <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-600 rounded-full border border-emerald-100">
                 <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                 <span className="text-[9px] font-black uppercase tracking-widest">Secure Path</span>
              </div>
              <div className="flex gap-2">
                 <button className="p-2 text-slate-400 hover:text-indigo-600 transition-colors"><MessageSquare size={20} /></button>
                 <button className="p-2 text-slate-400 hover:text-indigo-600 transition-colors"><Settings size={20} /></button>
              </div>
           </div>
        </div>

        <div className="flex-1 overflow-hidden relative">
          <AnimatePresence mode="wait">
            {activeView === 'chat' ? (
              <motion.div 
                key="chat"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="h-full flex flex-col"
              >
                <div 
                  ref={scrollRef}
                  className="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth"
                >
                  <AnimatePresence>
                    {messages.map((msg, i) => (
                      <motion.div
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        key={i}
                        className={cn(
                          "flex gap-6",
                          msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                        )}
                      >
                        <div className={cn(
                          "w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 shadow-sm border",
                          msg.role === 'user' ? "bg-white border-slate-200" : "bg-indigo-600 text-white border-indigo-500"
                        )}>
                          {msg.role === 'user' ? <User size={24} /> : <Bot size={24} />}
                        </div>
                        
                        <div className={cn(
                          "max-w-[75%] p-6 rounded-[2.5rem] text-sm leading-relaxed shadow-sm",
                          msg.role === 'user' 
                            ? "bg-slate-900 text-white rounded-tr-none" 
                            : "bg-indigo-50/40 text-slate-900 border border-indigo-50 rounded-tl-none font-medium"
                        )}>
                          <div className="whitespace-pre-wrap">{msg.text}</div>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  {isTyping && (
                    <div className="flex items-center gap-3 text-indigo-400 pl-4">
                      <div className="flex gap-1.5">
                         <motion.div animate={{ opacity: [1, 0.4, 1] }} transition={{ repeat: Infinity, duration: 1.5 }} className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
                         <motion.div animate={{ opacity: [1, 0.4, 1] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.2 }} className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
                         <motion.div animate={{ opacity: [1, 0.4, 1] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.4 }} className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
                      </div>
                      <span className="text-[10px] font-black uppercase tracking-[0.2em]">Medical Brain thinking...</span>
                    </div>
                  )}
                </div>

                <div className="p-8 border-t border-slate-100 bg-slate-50/50">
                  <AnimatePresence>
                    {isListening && (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="mb-8 flex flex-col items-center justify-center p-6 bg-slate-900 rounded-[2rem] text-white"
                      >
                         <div className="flex gap-2 items-center mb-4">
                            {[1, 2, 3, 4, 5, 6].map(i => (
                               <motion.div 
                                 key={i}
                                 animate={{ height: [12, 32, 12] }}
                                 transition={{ repeat: Infinity, duration: 1, delay: i * 0.1 }}
                                 className="w-1.5 bg-indigo-500 rounded-full"
                               />
                            ))}
                         </div>
                         <p className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-400">Capturing Clinical Audio Stream</p>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div className="relative group">
                    <input 
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                      placeholder="Query history or ask for clinical correlation..."
                      className="w-full bg-white border border-slate-200 rounded-[28px] py-6 pl-8 pr-32 text-sm focus:outline-none focus:ring-4 focus:ring-indigo-100 focus:border-indigo-600 transition-all shadow-sm group-hover:shadow-md"
                    />
                    <div className="absolute right-4 top-4 bottom-4 flex gap-2">
                       <button 
                         onClick={() => setIsListening(!isListening)}
                         className={cn(
                           "px-4 rounded-[20px] transition-all flex items-center justify-center",
                           isListening ? "bg-rose-50 text-rose-500 border border-rose-100 shadow-xl shadow-rose-100" : "bg-slate-50 text-slate-400 hover:text-indigo-600 border border-slate-100"
                         )}
                       >
                         <Bot size={20} className={cn(isListening && "animate-pulse")} />
                       </button>
                       <button 
                         onClick={handleSend}
                         className="px-6 bg-indigo-600 text-white rounded-[20px] shadow-lg shadow-indigo-100 hover:scale-105 active:scale-95 transition-all flex items-center justify-center"
                       >
                         <Send size={20} />
                       </button>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center justify-between px-2">
                    <div className="flex items-center gap-2">
                       <AlertCircle size={12} className="text-indigo-400" />
                       <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Neural Inference Path Enabled</span>
                    </div>
                    <div className="flex items-center gap-2">
                       <div className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                       <span className="text-[10px] text-slate-300 font-black uppercase tracking-widest">Active Consult</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : activeView === 'analysis' ? (
              <motion.div 
                key="analysis"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="h-full"
              >
                <OrganAnalysis />
              </motion.div>
            ) : activeView === 'explainable' ? (
              <motion.div 
                key="explainable"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="h-full"
              >
                <ExplainableAI />
              </motion.div>
            ) : (
              <motion.div 
                key="triage"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="h-full p-8 space-y-8 overflow-y-auto custom-scrollbar"
              >
                <DoctorPriorityQueue />
                <AdvancedTriageDetails patientName="Ahmed K." />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
