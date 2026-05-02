import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  FlaskConical, AlertCircle, CheckCircle2, TrendingUp, 
  ArrowRight, Download, Share2, Info, BrainCircuit,
  MessageSquare, Calendar, ChevronRight, Stethoscope
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';
import { LabTestResult } from '../../types/domain';
import { analyzeLabTrends } from '../../services/aiService';
import Markdown from 'react-markdown';
import { toast } from 'sonner';

export function SmartResultsView() {
  const { t } = useLanguage();
  const [selectedResult, setSelectedResult] = useState<LabTestResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);

  const mockResults: LabTestResult[] = [
    {
      id: 'r1',
      testName: 'Hemoglobin A1c (HbA1c)',
      value: '5.8',
      unit: '%',
      range: '4.0 - 5.6',
      flag: 'H',
      status: 'completed',
      labName: 'Central Diagnostic Center',
      labId: 'LAB-092'
    },
    {
      id: 'r2',
      testName: 'Vitamin D',
      value: '22',
      unit: 'ng/mL',
      range: '30 - 100',
      flag: 'L',
      status: 'completed',
      labName: 'Central Diagnostic Center',
      labId: 'LAB-092'
    },
    {
      id: 'r3',
      testName: 'LDL Cholesterol',
      value: '95',
      unit: 'mg/dL',
      range: '0 - 100',
      flag: 'N',
      status: 'completed',
      labName: 'Central Diagnostic Center',
      labId: 'LAB-092'
    }
  ];

  const handleExplain = async (result: LabTestResult) => {
    setSelectedResult(result);
    setIsAnalyzing(true);
    try {
      const explanation = await analyzeLabTrends([result]);
      setAiExplanation(explanation);
    } catch (error) {
      setAiExplanation("I'm having trouble analyzing this right now. Please consult your physician for a detailed interpretation.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getInterpretation = (flag: string) => {
    switch (flag) {
      case 'H': return { label: 'High', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-100', icon: AlertCircle };
      case 'L': return { label: 'Low', color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100', icon: Info };
      default: return { label: 'Normal', color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100', icon: CheckCircle2 };
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto p-4 md:p-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
        <div>
          <span className="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-600 mb-2 block">{t.resultsInterpretation}</span>
          <h1 className="text-3xl lg:text-4xl font-black text-slate-900 tracking-tighter leading-none">{t.labResults}</h1>
          <p className="text-slate-500 mt-2 font-medium">Clear, AI-powered understanding of your clinical data.</p>
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <button className="flex-1 md:flex-none px-6 py-3 bg-white border border-slate-200 rounded-2xl text-xs font-black uppercase tracking-widest hover:bg-slate-50 transition-all flex items-center justify-center gap-2">
            <Download size={16} /> {t.exportReport}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Results List */}
        <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {mockResults.map((result) => {
            const interp = getInterpretation(result.flag || 'N');
            return (
              <motion.div 
                key={result.id}
                whileHover={{ y: -4 }}
                className={cn(
                  "bg-white rounded-[2.5rem] p-8 border hover:shadow-xl transition-all group overflow-hidden relative",
                  interp.border,
                  selectedResult?.id === result.id ? "ring-2 ring-indigo-500 shadow-xl" : "shadow-sm"
                )}
              >
                {/* Background Decoration */}
                <div className={cn(
                  "absolute -bottom-8 -right-8 w-32 h-32 opacity-5 rounded-full",
                  interp.bg
                )} />
                
                <div className="flex justify-between items-start mb-6">
                  <div className={cn("p-4 rounded-3xl", interp.bg, interp.color)}>
                    <interp.icon size={28} />
                  </div>
                  <div className="text-right">
                    <span className={cn(
                      "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border",
                      interp.bg, interp.color, interp.border
                    )}>
                      {interp.label}
                    </span>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-slate-900 tracking-tight leading-tight">{result.testName}</h3>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-slate-900">{result.value}</span>
                    <span className="text-sm font-bold text-slate-400">{result.unit}</span>
                  </div>
                  
                  <div className="bg-slate-50 rounded-2xl p-4 space-y-2">
                    <div className="flex justify-between text-[10px] font-black uppercase text-slate-400 tracking-widest">
                      <span>{t.normalRange}</span>
                      <span>Target Level</span>
                    </div>
                    <div className="flex justify-between font-mono text-sm text-slate-600">
                      <span>{result.range}</span>
                      <span className="text-emerald-600 font-bold">In Range</span>
                    </div>
                  </div>

                  <button 
                    onClick={() => handleExplain(result)}
                    className="w-full py-4 bg-slate-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-3 group-hover:bg-indigo-600 transition-colors"
                  >
                    <BrainCircuit size={16} /> {t.interpretation}
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* AI Interpretation Panel */}
        <AnimatePresence>
          {selectedResult && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="lg:col-span-12 bg-slate-900 rounded-[3rem] p-10 text-white shadow-2xl relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
                <BrainCircuit size={200} />
              </div>

              <div className="relative z-10 grid grid-cols-1 md:grid-cols-12 gap-12">
                <div className="md:col-span-7 space-y-8">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center border border-white/10">
                      <BrainCircuit size={32} className="text-indigo-400" />
                    </div>
                    <div>
                      <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-400 mb-1">GULA Intelligence</h4>
                      <h3 className="text-2xl font-black tracking-tight italic">Analyzing: {selectedResult.testName}</h3>
                    </div>
                  </div>

                  <div className="prose prose-invert prose-sm max-w-none">
                    {isAnalyzing ? (
                      <div className="flex flex-col gap-4">
                        <div className="h-4 bg-white/10 rounded-full w-full animate-pulse" />
                        <div className="h-4 bg-white/10 rounded-full w-[90%] animate-pulse" />
                        <div className="h-4 bg-white/10 rounded-full w-[95%] animate-pulse" />
                      </div>
                    ) : (
                      <div className="text-lg text-slate-300 leading-relaxed font-medium">
                        <Markdown>{aiExplanation || t.analyzingData}</Markdown>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-4 pt-4">
                    <button className="flex-1 min-w-[200px] py-4 bg-white text-slate-900 rounded-3xl font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 hover:bg-slate-100 transition-all">
                      <Stethoscope size={18} /> {t.consultDoctor}
                    </button>
                    <button className="flex-1 min-w-[200px] py-4 bg-slate-800 text-white rounded-3xl font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 border border-white/10 hover:bg-slate-700 transition-all">
                      <MessageSquare size={18} /> Chat with AI
                    </button>
                  </div>
                </div>

                <div className="md:col-span-5 space-y-10 border-l border-white/5 pl-12 flex flex-col justify-center">
                  <div className="space-y-6">
                    <h5 className="text-[10px] font-black uppercase tracking-[.25em] text-white/40">Clinical Timeline Context</h5>
                    <div className="space-y-6 relative">
                      <div className="absolute left-0 top-2 bottom-2 w-px bg-white/5" />
                      {[
                        { label: 'Previous Panel', value: '5.9%', date: 'Jan 12', trend: 'down' },
                        { label: 'Current Level', value: '5.8%', date: 'Apr 20', trend: 'down' }
                      ].map((item, i) => (
                        <div key={i} className="relative pl-8 group/item">
                          <div className={cn(
                            "absolute left-[-4px] top-1.5 w-2 h-2 rounded-full border-2 border-slate-900 z-10",
                            item.trend === 'down' ? 'bg-emerald-500' : 'bg-red-500'
                          )} />
                          <div className="flex justify-between items-center group-hover/item:translate-x-1 transition-transform">
                            <div>
                              <p className="text-[10px] font-black uppercase text-white/40">{item.label}</p>
                              <p className="text-xl font-black text-white">{item.value}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-slate-500 font-bold">{item.date}</p>
                              <div className={cn(
                                "flex items-center gap-1 text-[10px] font-black uppercase",
                                item.trend === 'down' ? 'text-emerald-400' : 'text-red-400'
                              )}>
                                <TrendingUp size={10} className={item.trend === 'down' ? 'rotate-180' : ''} /> 
                                {item.trend === 'down' ? 'Stable Improvement' : 'Abnormal Rise'}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="p-6 bg-white/5 border border-white/10 rounded-[2rem]">
                    <div className="flex items-center gap-3 mb-3">
                       <Info size={16} className="text-indigo-400" />
                       <span className="text-[10px] font-black uppercase tracking-widest">Medical Disclaimer</span>
                    </div>
                    <p className="text-[9px] text-slate-500 leading-relaxed italic">
                      This AI interpretation is based on standard clinical guidelines and your history. It is NOT a definitive diagnosis. Your physician is the primary authority for clinical decisions.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer Support */}
      <div className="bg-slate-50 p-10 rounded-[3rem] border border-slate-200 flex flex-col md:flex-row items-center justify-between gap-8 mt-12">
        <div className="flex items-center gap-6">
          <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-xl border border-slate-100">
            <FlaskConical size={32} className="text-indigo-600" />
          </div>
          <div>
            <h4 className="text-xl font-bold text-slate-900 tracking-tight">Missing a result?</h4>
            <p className="text-sm text-slate-500 font-medium">Connect additional laboratories or upload PDF results for AI ingestion.</p>
          </div>
        </div>
        <div className="flex gap-4">
          <button className="px-8 py-4 bg-slate-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl">Connect Lab</button>
          <button className="px-8 py-4 bg-white border border-slate-200 text-slate-900 rounded-2xl font-black text-xs uppercase tracking-widest shadow-sm">Upload PDF</button>
        </div>
      </div>
    </div>
  );
}
