import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { Activity as ActivityIcon, Send, Sparkles, AlertCircle, Bot, User, Camera, Image as ImageIcon, X } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { getClinicalInsight } from '../services/geminiService';
import { cn } from '../lib/utils';

export function LabIntelligenceView() {
  const { t } = useLanguage();
  const [messages, setMessages] = useState<{ role: 'user' | 'ai'; text: string; image?: string }[]>([
    { role: 'ai', text: "GULA Clinical Intelligence online. Ready for data analysis, differential diagnosis assistance, or report digitization via GULA Vision." }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [attachedImage, setAttachedImage] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setAttachedImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSend = async () => {
    if (!input.trim() && !attachedImage) return;
    
    const userMessage = input || (attachedImage ? "Please analyze this report." : "");
    const imgData = attachedImage;
    
    setInput('');
    setAttachedImage(null);
    setMessages(prev => [...prev, { role: 'user', text: userMessage, image: imgData || undefined }]);
    setIsTyping(true);

    const context = "Current Patient Profile: Male, 45y. HbA1c: 7.2 (Elevated), LDL: 160 (High). BP: 145/92.";
    const response = await getClinicalInsight(userMessage, context, imgData || undefined);
    
    setMessages(prev => [...prev, { role: 'ai', text: response }]);
    setIsTyping(false);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto h-[calc(100vh-120px)] flex flex-col">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-600 text-white rounded-2xl shadow-lg shadow-indigo-200">
            <Sparkles size={32} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900">{t.intelligenceCanvas}</h1>
            <p className="text-slate-500">Multilingual Clinical Decision Support (CDSS)</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 rounded-xl border border-emerald-100 italic text-xs font-bold shadow-sm">
          <Camera size={14} /> GULA Vision Active
        </div>
      </div>

      <div className="flex-1 bg-white rounded-[32px] border border-slate-200 shadow-xl overflow-hidden flex flex-col">
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-6 space-y-6"
        >
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                key={i}
                className={cn(
                  "flex items-end gap-3",
                  msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                )}
              >
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm",
                  msg.role === 'user' ? "bg-slate-100" : "bg-indigo-600 text-white"
                )}>
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div className="flex flex-col gap-2 max-w-[80%]">
                  {msg.image && (
                    <div className="rounded-2xl overflow-hidden border border-slate-200 shadow-sm">
                      <img src={msg.image} alt="attached report" className="max-w-full h-auto max-h-64 object-cover" />
                    </div>
                  )}
                  <div className={cn(
                    "p-4 rounded-2xl text-sm leading-relaxed",
                    msg.role === 'user' 
                      ? "bg-slate-100 text-slate-800 rounded-br-none" 
                      : "bg-indigo-50/50 text-slate-900 border border-indigo-100 rounded-bl-none shadow-sm"
                  )}>
                    {msg.text}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {messages.length === 1 && (
            <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                { label: "Analyze Elevated HbA1c", prompt: "What are the common differential diagnoses for an HbA1c of 7.2 in a 45y male?" },
                { label: "Verify Viral Load Pattern", prompt: "Explain the clinical significance of a sudden 2-log increase in viral load." },
                { label: "Inventory Stock Alert", prompt: "GULA, suggest a reagent optimization strategy for Lab-South wing." },
                { label: "Read Medical Report", prompt: "Use GULA Vision to analyze the attached CBC report." }
              ].map((scenario, i) => (
                <button 
                  key={i}
                  onClick={() => {
                    setInput(scenario.prompt);
                    // Triggering send automatically for a better "quick" experience
                    setTimeout(() => document.getElementById('ai-send-btn')?.click(), 100);
                  }}
                  className="p-3 text-[10px] font-black uppercase tracking-widest text-indigo-600 bg-indigo-50/50 rounded-xl border border-indigo-100 hover:bg-indigo-600 hover:text-white transition-all text-left"
                >
                  {scenario.label}
                </button>
              ))}
            </div>
          )}
          {isTyping && (
            <div className="flex items-center gap-2 text-indigo-400">
              <ActivityIcon className="animate-pulse" size={16} />
              <span className="text-[10px] font-bold uppercase tracking-widest">GULA analyzing...</span>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-slate-100 bg-slate-50/50">
          {attachedImage && (
            <div className="mb-4 relative w-20 h-20 group">
              <img src={attachedImage} className="w-full h-full object-cover rounded-xl border-2 border-indigo-600" alt="preview" />
              <button 
                onClick={() => setAttachedImage(null)}
                className="absolute -top-2 -right-2 p-1 bg-red-600 text-white rounded-full shadow-lg"
              >
                <X size={12} />
              </button>
            </div>
          )}
          <div className="flex items-center gap-2">
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="p-4 bg-white border border-slate-200 rounded-2xl text-slate-400 hover:text-indigo-600 hover:border-indigo-600 transition-all shadow-sm"
            >
              <ImageIcon size={20} />
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept="image/*" 
              onChange={handleImageUpload}
            />
            <div className="relative flex-1 group">
              <input 
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask GULA or attach a report image..."
                className="w-full bg-white border border-slate-200 rounded-2xl py-4 pl-6 pr-14 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all shadow-sm group-hover:shadow-md"
              />
              <button 
                id="ai-send-btn"
                onClick={handleSend}
                className="absolute right-3 top-2 bottom-2 px-4 bg-indigo-600 text-white rounded-xl shadow-lg shadow-indigo-100 hover:scale-105 active:scale-95 transition-all"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <AlertCircle size={12} className="text-slate-400" />
            <span className="text-[10px] text-slate-400 font-medium">Model: GULA-3-Flash. Vision active. Not a medical substitute.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
