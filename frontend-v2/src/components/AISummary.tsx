import React, { useState, useRef, useEffect } from 'react';
import { BrainCircuit, Loader2, Sparkles, X, ChevronRight, Send, MessageSquare } from 'lucide-react';
import { analyzeLabTrends, askFollowUp } from '../services/aiService';
import { motion, AnimatePresence } from 'motion/react';
import Markdown from 'react-markdown';
import { cn } from '../lib/utils';

interface Message {
  role: 'assistant' | 'user';
  content: string;
}

interface AISummaryProps {
  findings: string;
  testTitle: string;
}

export function AISummary({ findings, testTitle }: AISummaryProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [question, setQuestion] = useState('');
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const parseResponse = (text: string) => {
    const questionsMatch = text.match(/SUGGESTED_QUESTIONS:\n([\s\S]*)/i);
    if (questionsMatch) {
      const questionsText = questionsMatch[1];
      const questions = questionsText
        .split('\n')
        .map(q => q.replace(/^- /, '').trim())
        .filter(q => q && q.length > 0)
        .slice(0, 3);
      
      const cleanContent = text.split('---')[0].trim();
      return { cleanContent, questions };
    }
    return { cleanContent: text, questions: [] };
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) scrollToBottom();
  }, [messages, isOpen]);

  const handleSummarize = async () => {
    setIsOpen(true);
    if (messages.length > 0) return;
    
    setIsLoading(true);
    setSuggestedQuestions([]);
    try {
      const result = await analyzeLabTrends([{ title: testTitle, findings }]);
      const { cleanContent, questions } = parseResponse(result);
      setMessages([{ role: 'assistant', content: cleanContent }]);
      setSuggestedQuestions(questions);
    } catch (error) {
      setMessages([{ role: 'assistant', content: "Unable to generate summary at this time. Please consult with your clinical lead." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    const userMsg = question;
    setQuestion('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);
    setSuggestedQuestions([]);
    
    try {
      const context = messages.map(m => `${m.role}: ${m.content}`).join('\n');
      const response = await askFollowUp(context, userMsg);
      const { cleanContent, questions } = parseResponse(response);
      setMessages(prev => [...prev, { role: 'assistant', content: cleanContent }]);
      setSuggestedQuestions(questions);
    } catch (error) {
       setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I couldn't process that question right now." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <button 
        onClick={handleSummarize}
        className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-600 hover:text-white transition-all rounded-lg text-[10px] font-black uppercase tracking-widest shadow-sm"
      >
        <BrainCircuit size={14} />
        GULA AI Advisor
      </button>

      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md">
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white w-full max-w-2xl rounded-[3rem] shadow-2xl border border-slate-100 overflow-hidden relative flex flex-col max-h-[85vh]"
            >
              <div className="p-8 bg-indigo-600 text-white relative overflow-hidden shrink-0">
                <div className="absolute top-0 right-0 p-12 opacity-10 rotate-12 shrink-0">
                   <Sparkles size={120} />
                </div>
                <div className="relative z-10 flex items-center justify-between">
                   <div className="flex items-center gap-3">
                      <div className="p-2 bg-white/10 rounded-xl">
                         <BrainCircuit size={24} />
                      </div>
                      <div>
                        <h3 className="text-xl font-black italic tracking-tight">Clinical AI Advisor.</h3>
                        <p className="text-[10px] uppercase font-bold tracking-widest opacity-80">Interactive Diagnostic Session</p>
                      </div>
                   </div>
                   <button 
                     onClick={() => setIsOpen(false)}
                     className="p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
                   >
                     <X size={20} />
                   </button>
                </div>
              </div>

              <div className="p-0 flex-1 overflow-y-auto custom-scrollbar bg-slate-50/30">
                <div className="p-8 space-y-6">
                  {messages.length === 0 && isLoading && (
                    <div className="flex flex-col items-center justify-center py-20 gap-6">
                      <div className="relative">
                         <Loader2 size={48} className="text-indigo-600 animate-spin" />
                         <Sparkles size={20} className="absolute -top-2 -right-2 text-indigo-400 animate-pulse" />
                      </div>
                      <div className="text-center font-black uppercase text-[10px] tracking-widest text-slate-400 italic">
                         Booting Clinical Intelligence...
                      </div>
                    </div>
                  )}

                  {messages.map((msg, i) => (
                    <motion.div 
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={cn(
                        "flex gap-4 p-6 rounded-[2rem] border shadow-sm",
                        msg.role === 'assistant' 
                          ? "bg-white border-slate-100" 
                          : "bg-indigo-600 text-white border-indigo-700 ml-12"
                      )}
                    >
                      {msg.role === 'assistant' && (
                        <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
                          <BrainCircuit size={16} className="text-indigo-600" />
                        </div>
                      )}
                      <div className={cn(
                        "markdown-body text-sm leading-relaxed font-medium flex-1",
                        msg.role === 'user' ? "text-white prose-invert" : "text-slate-600"
                      )}>
                        <Markdown>{msg.content}</Markdown>
                      </div>
                    </motion.div>
                  ))}
                  
                  {isLoading && messages.length > 0 && (
                    <div className="flex gap-4 p-6 bg-slate-50 rounded-[2rem] border border-slate-100 italic animate-pulse">
                      <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center shrink-0">
                        <Loader2 size={16} className="text-slate-400 animate-spin" />
                      </div>
                      <span className="text-xs font-black uppercase text-slate-400 tracking-widest self-center">AI is thinking...</span>
                    </div>
                  )}

                  {!isLoading && suggestedQuestions.length > 0 && (
                    <div className="space-y-3 px-2">
                       <p className="text-[9px] font-black uppercase text-slate-400 tracking-[0.2em] ml-2">Suggested Follow-ups</p>
                       <div className="flex flex-wrap gap-2">
                         {suggestedQuestions.map((q, idx) => (
                           <button 
                             key={idx}
                             onClick={() => {
                               setQuestion(q);
                               // Use form trigger logic here
                               setTimeout(() => {
                                 const submitBtn = document.getElementById('ai-submit-btn');
                                 submitBtn?.click();
                               }, 100);
                             }}
                             className="px-4 py-2.5 bg-indigo-50 text-indigo-600 border border-indigo-100 rounded-xl text-[10px] font-bold hover:bg-indigo-600 hover:text-white transition-all flex items-center gap-2 group animate-in fade-in slide-in-from-bottom-2"
                           >
                             <Sparkles size={12} className="text-indigo-400 group-hover:text-white" />
                             {q}
                           </button>
                         ))}
                       </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>
              </div>

              <div className="p-6 bg-white border-t border-slate-100 shrink-0">
                <form onSubmit={handleAsk} className="relative group">
                  <input 
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask a follow-up question..."
                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-600 rounded-2xl py-4 pl-6 pr-14 text-sm font-bold text-slate-900 outline-none transition-all placeholder:text-slate-300"
                  />
                  <button 
                    id="ai-submit-btn"
                    type="submit"
                    disabled={!question.trim() || isLoading}
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-slate-900 text-white rounded-xl flex items-center justify-center hover:bg-indigo-600 transition-all disabled:opacity-30 disabled:hover:bg-slate-900"
                  >
                    <Send size={18} />
                  </button>
                </form>
                <div className="flex items-center gap-2 mt-4 ml-2">
                   <MessageSquare size={12} className="text-indigo-400" />
                   <p className="text-[9px] font-black uppercase text-slate-300 tracking-tighter">Enter a specific clinical query based on the above findings</p>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
