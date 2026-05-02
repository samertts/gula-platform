import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Bot, X, MessageSquare, Sparkles, 
  ChevronRight, HelpCircle, Lightbulb,
  Search, BookOpen, LifeBuoy, Mic, MicOff
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function HelpAssistant() {
  const { t, isRtl } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'docs' | 'tips'>('tips');
  const [isVocalActive, setIsVocalActive] = useState(false);

  const tips = [
    { id: 1, title: 'Quick Navigation', desc: 'Use Cmd/Ctrl + K to open the command palette anywhere.', icon: Search },
    { id: 2, title: 'Offline Access', desc: 'The system automatically saves your work during connectivity drops.', icon: BookOpen },
    { id: 3, title: 'Identity Levels', desc: 'Higher Assurance Levels (LOA) unlock more medical capabilities.', icon: Sparkles },
  ];

  return (
    <div className={cn("fixed bottom-8 z-50", isRtl ? "left-8" : "right-8")}>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            className="mb-4 w-[380px] bg-white rounded-[2.5rem] shadow-2xl border border-slate-100 overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="bg-slate-900 p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-500 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
                    <Bot size={24} />
                  </div>
                  <div>
                    <h3 className="font-black text-sm uppercase tracking-wider">{t.assistantWelcome}</h3>
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active Neural Link</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => setIsVocalActive(!isVocalActive)}
                    className={cn(
                      "p-2 rounded-xl transition-all border",
                      isVocalActive 
                        ? "bg-rose-500 text-white border-rose-400 shadow-lg shadow-rose-900/40" 
                        : "bg-white/5 text-slate-400 border-white/10 hover:bg-white/10"
                    )}
                  >
                    {isVocalActive ? <Mic size={18} className="animate-pulse" /> : <MicOff size={18} />}
                  </button>
                  <button 
                    onClick={() => setIsOpen(false)}
                    className="p-2 hover:bg-white/10 rounded-xl transition-colors"
                  >
                    <X size={20} />
                  </button>
                </div>
              </div>

              <div className="flex bg-white/10 p-1 rounded-xl">
                 {(['tips', 'chat', 'docs'] as const).map(tab => (
                   <button
                     key={tab}
                     onClick={() => setActiveTab(tab)}
                     title={tab === 'tips' ? t.tipsTooltip : tab === 'chat' ? t.chatTooltip : t.docsTooltip}
                     className={cn(
                       "flex-1 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all relative group/tab",
                       activeTab === tab ? "bg-white text-slate-900" : "text-slate-400 hover:text-white"
                     )}
                   >
                     {tab === 'tips' ? t.tipsTab : tab === 'chat' ? t.chatTab : t.docsTab}
                     
                     {/* Custom animated tooltip style indicator on hover */}
                     <span className="absolute -bottom-10 left-1/2 -translate-x-1/2 px-2 py-1 bg-slate-800 text-white text-[8px] rounded opacity-0 group-hover/tab:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-xl border border-white/10 hidden md:block">
                       {tab === 'tips' ? t.tipsTooltip : tab === 'chat' ? t.chatTooltip : t.docsTooltip}
                     </span>
                   </button>
                 ))}
              </div>
            </div>

            {/* Content Source */}
            <div className="max-h-[400px] overflow-y-auto p-6 bg-slate-50/50">
               {activeTab === 'tips' && (
                 <div className="space-y-4">
                   <p className="text-xs font-medium text-slate-500 mb-4">{t.howCanIHelp}</p>
                   {tips.map((tip, i) => (
                     <motion.div 
                       key={tip.id}
                       initial={{ opacity: 0, x: -10 }}
                       animate={{ opacity: 1, x: 0 }}
                       transition={{ delay: i * 0.1 }}
                       className="p-4 bg-white border border-slate-100 rounded-2xl flex gap-4 group cursor-pointer hover:border-indigo-600 transition-all shadow-sm"
                     >
                       <div className="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center text-slate-400 group-hover:text-indigo-600 transition-colors">
                         <tip.icon size={20} />
                       </div>
                       <div>
                         <h4 className="text-[11px] font-black uppercase tracking-tight text-slate-900 mb-0.5">{tip.title}</h4>
                         <p className="text-[10px] text-slate-500 font-medium leading-relaxed">{tip.desc}</p>
                       </div>
                     </motion.div>
                   ))}
                   
                   <button className="w-full py-4 bg-indigo-50 text-indigo-600 rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-indigo-100 transition-colors">
                     View All Tutorials
                   </button>
                 </div>
               )}

               {activeTab === 'chat' && (
                 <div className="text-center py-12 space-y-4">
                   <MessageSquare size={40} className="mx-auto text-slate-200" />
                   <div>
                     <p className="text-xs font-black text-slate-900 uppercase">Live Support Offline</p>
                     <p className="text-[10px] text-slate-500 font-medium mt-1">Our clinical experts are available 08:00 - 20:00 (KSA)</p>
                   </div>
                 </div>
               )}

               {activeTab === 'docs' && (
                 <div className="space-y-3">
                   {['User Manual', 'API Integration', 'Data Policies', 'Security Whitepaper'].map((doc, i) => (
                     <div key={doc} className="p-3 border border-slate-100 rounded-xl flex items-center justify-between hover:bg-white transition-colors group cursor-pointer">
                        <div className="flex items-center gap-3">
                           <BookOpen size={14} className="text-slate-400" />
                           <span className="text-[10px] font-black text-slate-700 uppercase tracking-tight">{doc}</span>
                        </div>
                        <ChevronRight size={14} className="text-slate-300 group-hover:text-indigo-600 group-hover:translate-x-1 transition-all" />
                     </div>
                   ))}
                 </div>
               )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-100 bg-white">
               <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                     <LifeBuoy size={12} className="text-slate-300" />
                     <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest">Support Node: BGD-01</span>
                  </div>
                  <span className="text-[8px] font-black text-emerald-500 uppercase tracking-widest">v4.2.1 Stable</span>
               </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "w-16 h-16 rounded-full flex items-center justify-center shadow-2xl transition-all duration-500 active:scale-95 group relative",
          isOpen ? "bg-slate-900 text-white rotate-90" : "bg-indigo-600 text-white hover:scale-110"
        )}
      >
        <div className="absolute inset-0 rounded-full bg-indigo-600 blur-xl opacity-0 group-hover:opacity-40 transition-opacity" />
        {isOpen ? <X size={28} /> : <HelpCircle size={28} />}
        {!isOpen && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-5 h-5 bg-rose-500 rounded-full border-4 border-white flex items-center justify-center"
          >
             <span className="w-1.5 h-1.5 bg-white rounded-full animate-ping" />
          </motion.div>
        )}
      </button>
    </div>
  );
}
