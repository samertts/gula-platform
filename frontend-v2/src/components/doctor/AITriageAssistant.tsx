import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { BrainCircuit, Send, Loader2, AlertCircle, CheckCircle2, ChevronRight, Stethoscope } from 'lucide-react';
import { generateSmartDiagnosis } from '../../services/aiService';
import Markdown from 'react-markdown';
import { cn } from '../../lib/utils';
import { useLanguage } from '../../contexts/LanguageContext';

interface AITriageAssistantProps {
  patientId: string;
  patientData: string;
}

export function AITriageAssistant({ patientId, patientData }: AITriageAssistantProps) {
  const [symptoms, setSymptoms] = useState('');
  const [insight, setInsight] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { t } = useLanguage();

  const handleTriage = async () => {
    if (!symptoms.trim()) return;
    
    setIsLoading(true);
    try {
      const result = await generateSmartDiagnosis(patientData, symptoms);
      setInsight(result);
    } catch (error) {
      console.error("Triage Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-xl shadow-slate-200/50 overflow-hidden group">
      <div className="p-8 border-b border-slate-50 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:scale-110 transition-transform text-indigo-600">
          <BrainCircuit size={120} />
        </div>
        
        <div className="flex items-center gap-4 relative z-10">
          <div className="w-14 h-14 bg-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-indigo-100">
            <BrainCircuit size={28} />
          </div>
          <div>
            <h3 className="text-xl font-black text-slate-900 tracking-tight">AI Clinical Co-Pilot</h3>
            <p className="text-[10px] font-black uppercase tracking-widest text-indigo-500 italic">Advanced Differential Diagnosis Engine</p>
          </div>
        </div>
      </div>

      <div className="p-8 space-y-6">
        <div className="space-y-4">
          <label className="text-xs font-black uppercase tracking-widest text-slate-400">Reported Symptoms & Observations</label>
          <div className="relative group">
            <textarea
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              placeholder="Enter symptoms, vital signs anomalies, or patient complaints..."
              className="w-full h-32 p-6 bg-slate-50 border-2 border-transparent rounded-[2rem] text-sm font-medium focus:bg-white focus:border-indigo-100 focus:ring-0 transition-all resize-none"
            />
            <button
              onClick={handleTriage}
              disabled={isLoading || !symptoms.trim()}
              className={cn(
                "absolute bottom-4 right-4 p-4 rounded-2xl transition-all shadow-lg active:scale-95 disabled:opacity-50 disabled:scale-100",
                isLoading ? "bg-slate-100 text-slate-400" : "bg-indigo-600 text-white shadow-indigo-200 hover:bg-black"
              )}
            >
              {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
            </button>
          </div>
        </div>

        <AnimatePresence mode="wait">
          {insight ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative"
            >
              <div className="p-8 bg-indigo-50 rounded-[2.5rem] border border-indigo-100 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-6 opacity-[0.05] text-indigo-600">
                  <Stethoscope size={60} />
                </div>
                
                <div className="flex items-center gap-3 mb-6">
                   <div className="px-3 py-1 bg-indigo-600 text-white rounded-full text-[9px] font-black uppercase tracking-widest">
                      Preliminary Analysis
                   </div>
                   <span className="text-[10px] font-bold text-slate-400">Generated for Patient ID: {patientId}</span>
                </div>

                <div className="prose prose-slate prose-sm max-w-none prose-headings:font-black prose-headings:uppercase prose-headings:tracking-widest prose-headings:text-[10px] prose-headings:text-indigo-600 markdown-body">
                  <Markdown>{insight}</Markdown>
                </div>

                <div className="mt-8 pt-8 border-t border-indigo-100/50 flex flex-wrap gap-4">
                   <button className="px-5 py-2.5 bg-white rounded-xl text-[9px] font-black uppercase tracking-widest text-indigo-600 hover:bg-indigo-600 hover:text-white transition-all shadow-sm">
                      Apply to Record
                   </button>
                   <button className="px-5 py-2.5 bg-white rounded-xl text-[9px] font-black uppercase tracking-widest text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition-all shadow-sm">
                      Flag for Review
                   </button>
                </div>
              </div>

              <div className="mt-4 p-4 bg-amber-50 rounded-2xl flex items-center gap-3 border border-amber-100">
                 <AlertCircle size={16} className="text-amber-600 shrink-0" />
                 <p className="text-[9px] font-bold text-amber-800 leading-tight">
                    DISCLAIMER: This is a physician support tool. Analysis is based purely on the text provided. Final clinical judgment rests with the licensed professional.
                 </p>
              </div>
            </motion.div>
          ) : !isLoading && (
            <div className="p-10 border-2 border-dashed border-slate-100 rounded-[2rem] flex flex-col items-center justify-center text-center">
               <div className="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center text-slate-300 mb-4">
                  <BrainCircuit size={24} />
               </div>
               <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Awaiting Clinical Inputs</p>
               <p className="text-[9px] font-medium text-slate-300 mt-2 max-w-[200px]">Input symptoms above to receive real-time AI-driven triage assistance.</p>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
