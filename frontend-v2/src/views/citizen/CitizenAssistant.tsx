import React, { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  BrainCircuit, Send, User, Bot, Sparkles, 
  Mic, Paperclip, ChevronRight, MessageSquare,
  Thermometer, Beaker, Pill, History, Info,
  AlertCircle, ShieldCheck, Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';
import Markdown from 'react-markdown';
import { GoogleGenerativeAI } from '@google/generative-ai';

export function CitizenAssistant() {
  const { t } = useLanguage();
  const [messages, setMessages] = useState<{ role: 'user' | 'ai'; content: string }[]>([
    { role: 'ai', content: "Hello Samer. I am your GULA Health Intelligence assistant. I have secure access to your clinical records, medication adherence data, and latest lab panels. How can I help you understand your health today?" }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput("");
    setIsTyping(true);

    // Simulate AI logic for now or connect to API
    setTimeout(() => {
      let response = "";
      if (userMsg.toLowerCase().includes('result') || userMsg.toLowerCase().includes('lab')) {
        response = "Your latest **HbA1c level (5.8%)** is slightly above the optimal range (4.0-5.6%). This indicates a pre-diabetic trend. I recommend scheduling a follow-up with your endocrinologist to discuss your Metformin dosage.";
      } else if (userMsg.toLowerCase().includes('symptom')) {
        response = "I can help with Triage. Please describe your symptoms. Are you experiencing any chest pain, shortness of breath, or sudden dizziness?";
      } else {
        response = "I've analyzed your medical journey. Your health score is currently 85/100. You've been 100% adherent to your Vitamin D supplementation this week. Would you like to see your metabolic trends?";
      }
      setMessages(prev => [...prev, { role: 'ai', content: response }]);
      setIsTyping(false);
    }, 1500);
  };

  const suggestions = [
    { label: "Explain my last lab results", icon: Beaker },
    { label: "Am I following my treatment plan?", icon: Pill },
    { label: "I have a headache and fatigue", icon: Thermometer },
    { label: "Show my health trends", icon: History }
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-5xl mx-auto p-4 md:p-8 animate-in fade-in duration-500">
      <div className="flex-1 bg-white rounded-[3rem] border border-slate-200 shadow-sm flex flex-col overflow-hidden relative">
        {/* Header */}
        <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-indigo-600 text-white rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-100">
              <BrainCircuit size={24} />
            </div>
            <div>
              <h3 className="text-xl font-black text-slate-900 tracking-tighter italic">GULA AI Assistant</h3>
              <div className="flex items-center gap-2">
                 <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                 <span className="text-[9px] font-black uppercase text-slate-400 tracking-widest">Medical Engine 4.0 Active</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
             <div className="px-3 py-1 bg-white border border-slate-200 rounded-lg text-[9px] font-black uppercase text-slate-500 shadow-sm flex items-center gap-1.5">
                <ShieldCheck size={12} className="text-emerald-500" /> Secure Context
             </div>
          </div>
        </div>

        {/* Message Area */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-8 space-y-8 no-scrollbar"
        >
          {messages.map((msg, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex gap-4 max-w-[85%]",
                msg.role === 'user' ? "ml-auto flex-row-reverse" : ""
              )}
            >
              <div className={cn(
                "w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-sm transition-transform hover:scale-110",
                msg.role === 'ai' ? "bg-indigo-600 text-white" : "bg-slate-900 text-white"
              )}>
                {msg.role === 'ai' ? <BrainCircuit size={18} /> : <User size={18} />}
              </div>
              <div className={cn(
                "p-6 rounded-[2rem] text-sm leading-relaxed",
                msg.role === 'ai' 
                  ? "bg-slate-50 text-slate-900 border border-slate-100" 
                  : "bg-indigo-600 text-white shadow-xl shadow-indigo-100"
              )}>
                <Markdown>{msg.content}</Markdown>
              </div>
            </motion.div>
          ))}
          {isTyping && (
            <div className="flex gap-4 max-w-[85%]">
              <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center animate-pulse">
                <BrainCircuit size={18} />
              </div>
              <div className="p-6 rounded-[2rem] bg-slate-50 border border-slate-100 flex gap-2">
                 <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" />
                 <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce delay-75" />
                 <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce delay-150" />
              </div>
            </div>
          )}
        </div>

        {/* Suggestions Bar */}
        <div className="px-8 pb-4">
          <div className="flex gap-3 overflow-x-auto no-scrollbar pb-2">
            {suggestions.map((s, i) => (
              <button 
                key={i}
                onClick={() => {
                  setInput(s.label);
                }}
                className="flex-none flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 rounded-2xl text-[10px] font-bold text-slate-600 hover:border-indigo-600 hover:text-indigo-600 transition-all shadow-sm"
              >
                <s.icon size={12} /> {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <div className="p-8 bg-slate-50/50 border-t border-slate-100">
           <div className="flex gap-4 bg-white p-2 rounded-[2.5rem] border border-slate-200 shadow-xl shadow-slate-100/50 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all">
              <button className="p-4 text-slate-400 hover:text-indigo-600 transition-colors">
                 <Paperclip size={20} />
              </button>
              <input 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask about your health, records, or symptoms..."
                className="flex-1 bg-transparent border-none outline-none text-slate-900 placeholder:text-slate-400 font-medium px-2"
              />
              <button className="p-4 text-slate-400 hover:text-indigo-600 transition-colors">
                 <Mic size={20} />
              </button>
              <button 
                onClick={handleSend}
                disabled={!input.trim()}
                className="w-12 h-12 bg-indigo-600 text-white rounded-[1.25rem] flex items-center justify-center hover:bg-slate-900 transition-all shadow-lg active:scale-95 disabled:opacity-50"
              >
                 <Send size={20} />
              </button>
           </div>
           <div className="mt-4 flex items-center justify-center gap-6">
              <div className="flex items-center gap-2 opacity-50 grayscale hover:grayscale-0 hover:opacity-100 transition-all cursor-help">
                 <Zap size={12} className="text-amber-500" />
                 <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Fast Mode</span>
              </div>
              <div className="flex items-center gap-2 opacity-50 grayscale hover:grayscale-0 hover:opacity-100 transition-all cursor-help">
                 <BrainCircuit size={12} className="text-indigo-500" />
                 <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Clinical Reasoning</span>
              </div>
           </div>
        </div>
      </div>

      <div className="mt-8 flex items-center justify-between p-6 bg-indigo-50 rounded-[2rem] border border-indigo-100">
         <div className="flex items-center gap-4">
            <div className="p-3 bg-white rounded-xl">
               <AlertCircle size={20} className="text-indigo-600" />
            </div>
            <p className="text-xs text-indigo-900 font-medium italic">
               "Your privacy is our priority. All conversations are end-to-end encrypted and used only for your personal health insights."
            </p>
         </div>
         <button className="text-[10px] font-black uppercase tracking-widest text-indigo-600 hover:underline">Privacy Policy</button>
      </div>
    </div>
  );
}
