import React, { useState, useEffect } from 'react';
import { 
  FileText, Save, History, Sparkles, 
  Mic, User, Activity, AlertCircle, CheckCircle2,
  Undo2
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';
import { toast } from 'sonner';

export function ClinicalNotes() {
  const [note, setNote] = useState({
    subjective: '',
    objective: '',
    assessment: '',
    plan: ''
  });
  const [history, setHistory] = useState<typeof note[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isListening, setIsListening] = useState(false);

  const handleSave = () => {
    setIsSaving(true);
    // Simulate API call
    setTimeout(() => {
      setIsSaving(false);
      setLastSaved(new Date());
    }, 800);
  };

  // Auto-save every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (note.subjective || note.objective || note.assessment || note.plan) {
        handleSave();
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [note]);

  // Save on component unmount
  useEffect(() => {
    return () => {
      // In a real app, we would perform a synchronous save or use navigator.sendBeacon
      // For this simulation, we'll just log it
      console.log('Component unmounting, saving clinical notes...');
    };
  }, [note]);

  const updateNote = (newNote: typeof note) => {
    setHistory(prev => [...prev, note].slice(-20)); // Keep last 20 changes
    setNote(newNote);
  };

  const undo = () => {
    if (history.length > 0) {
      const prevNote = history[history.length - 1];
      setHistory(prev => prev.slice(0, -1));
      setNote(prevNote);
      toast.success('Undone last change');
    } else {
      toast.error('Nothing to undo');
    }
  };

  const handleAIComplete = () => {
    toast.success('AI Suggestion: Consider acute bronchitis based on objective findings.');
    updateNote({
      ...note,
      assessment: note.assessment + (note.assessment ? ' ' : '') + 'Differential diagnosis includes acute bronchitis vs pneumonia.'
    });
  };

  return (
    <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden flex flex-col min-h-[700px]">
      <div className="p-8 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold flex items-center gap-3 text-slate-900">
            <FileText className="text-blue-600" />
            Smart Clinical Documentation
          </h3>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">SOAP Structure • Real-time Validation</p>
        </div>
        <div className="flex items-center gap-4">
           {lastSaved && (
             <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-widest">
               Last synced {lastSaved.toLocaleTimeString()}
             </span>
           )}
           <div className="flex gap-2">
              <button 
                onClick={handleAIComplete}
                className="p-3 bg-indigo-50 text-indigo-600 rounded-2xl hover:bg-indigo-600 hover:text-white transition-all shadow-sm"
                title="AI Assist"
              >
                <Sparkles size={18} />
              </button>
              <button className="p-3 bg-white border border-slate-200 text-slate-400 rounded-2xl hover:bg-slate-50 transition-all">
                 <History size={18} />
              </button>
           </div>
        </div>
      </div>

      <div className="flex-1 p-10 space-y-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
           {/* Subjective */}
           <div className="space-y-4">
              <div className="flex items-center justify-between">
                 <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center gap-2">
                    <User size={12} className="text-blue-500" /> Subjective (Patient Complaints)
                 </h4>
                 <button onClick={() => setIsListening(!isListening)} className={cn("p-2 rounded-xl transition-all", isListening ? "bg-rose-50 text-rose-500 animate-pulse" : "bg-slate-50 text-slate-400 hover:text-blue-500")}>
                    <Mic size={14} />
                 </button>
              </div>
              <textarea 
                value={note.subjective}
                onChange={(e) => updateNote({...note, subjective: e.target.value})}
                placeholder="Patient reports persistent cough for 3 weeks..."
                className="w-full h-40 bg-slate-50 border-none rounded-[2rem] p-6 text-sm font-medium text-slate-700 focus:ring-4 focus:ring-blue-50 transition-all resize-none"
              />
           </div>

           {/* Objective */}
           <div className="space-y-4">
              <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center gap-2">
                 <Activity size={12} className="text-rose-500" /> Objective (Observations/Vitals)
              </h4>
              <textarea 
                value={note.objective}
                onChange={(e) => updateNote({...note, objective: e.target.value})}
                placeholder="Temp 38.2C, BP 145/90, Crackles in RUL..."
                className="w-full h-40 bg-slate-50 border-none rounded-[2rem] p-6 text-sm font-medium text-slate-700 focus:ring-4 focus:ring-rose-50 transition-all resize-none"
              />
           </div>

           {/* Assessment */}
           <div className="space-y-4">
              <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center gap-2">
                 <AlertCircle size={12} className="text-amber-500" /> Assessment (Clinical Reasoning)
              </h4>
              <textarea 
                value={note.assessment}
                onChange={(e) => updateNote({...note, assessment: e.target.value})}
                placeholder="Probable community acquired pneumonia..."
                className="w-full h-40 bg-slate-50 border-none rounded-[2rem] p-6 text-sm font-medium text-slate-700 focus:ring-4 focus:ring-amber-50 transition-all resize-none"
              />
           </div>

           {/* Plan */}
           <div className="space-y-4">
              <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 flex items-center gap-2">
                 <CheckCircle2 size={12} className="text-emerald-500" /> Plan (Next Steps)
              </h4>
              <textarea 
                value={note.plan}
                onChange={(e) => updateNote({...note, plan: e.target.value})}
                placeholder="Start Amoxicillin, order follow-up X-ray in 2 weeks..."
                className="w-full h-40 bg-slate-50 border-none rounded-[2rem] p-6 text-sm font-medium text-slate-700 focus:ring-4 focus:ring-emerald-50 transition-all resize-none"
              />
           </div>
        </div>
      </div>

      <div className="p-8 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between">
        <div className="flex items-center gap-4">
           <button 
             onClick={undo}
             disabled={history.length === 0}
             className="flex items-center gap-2 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
           >
              <Undo2 size={16} />
              <span className="text-[10px] font-black uppercase tracking-widest">Undo Changes</span>
           </button>
        </div>
        <div className="flex gap-4">
           <button 
             onClick={handleSave}
             className="px-10 py-5 bg-slate-900 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-800 transition-all shadow-xl shadow-slate-200 flex items-center gap-2"
           >
             {isSaving ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Save size={18} />}
             Save Final Note
           </button>
        </div>
      </div>

      <AnimatePresence>
        {isListening && (
          <motion.div 
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-12 left-1/2 -translate-x-1/2 bg-slate-900 text-white px-8 py-4 rounded-full shadow-2xl flex items-center gap-6 z-[110]"
          >
             <div className="flex gap-1">
                {[1, 2, 3, 4].map(i => (
                  <motion.div 
                    key={i}
                    animate={{ height: [8, 20, 8] }}
                    transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.1 }}
                    className="w-1 bg-indigo-400 rounded-full"
                  />
                ))}
             </div>
             <span className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-200">Listening to Clinical Dictation...</span>
             <button onClick={() => setIsListening(false)} className="text-[10px] font-black uppercase bg-white/10 hover:bg-white/20 px-4 py-2 rounded-full transition-all">Stop</button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
