import React from 'react';
import { motion } from 'motion/react';
import { Brain, CheckCircle, AlertTriangle, Shield, Info, Network, Zap } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function ExplainableAI() {
  const { t } = useLanguage();

  return (
    <div className="h-full bg-slate-50 flex flex-col p-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto w-full space-y-8">
        <div className="flex items-center gap-4 mb-8">
           <div className="p-4 bg-indigo-600 text-white rounded-[2rem] shadow-xl shadow-indigo-100">
              <Brain size={32} />
           </div>
           <div>
              <h3 className="text-2xl font-black uppercase tracking-tight text-slate-900">{t.explainableAI}</h3>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-widest leading-loose">Demystifying Medical Reasoning Engine Logic</p>
           </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
           <div className="bg-white p-8 rounded-[3rem] border border-slate-100 shadow-sm space-y-6">
              <div className="flex items-center gap-3 text-indigo-600">
                 <Shield size={20} />
                 <h4 className="text-sm font-black uppercase tracking-tight">{t.clinicalGuardrails} Status</h4>
              </div>
              <div className="space-y-4">
                 {[
                   { label: 'Drug-Drug Conflict', status: 'Safe', color: 'text-emerald-500' },
                   { label: 'Guideline Alignment', status: '94%', color: 'text-indigo-500' },
                   { label: 'Identity Integrity', status: 'Locked', color: 'text-emerald-500' },
                   { label: 'Diagnostic Drift', status: 'Low', color: 'text-indigo-500' },
                 ].map((g, i) => (
                   <div key={i} className="flex justify-between items-center p-4 bg-slate-50 rounded-2xl">
                      <span className="text-xs font-bold text-slate-500">{g.label}</span>
                      <span className={cn("text-xs font-black uppercase tracking-widest", g.color)}>{g.status}</span>
                   </div>
                 ))}
              </div>
           </div>

           <div className="bg-slate-900 p-8 rounded-[3rem] text-white space-y-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-10">
                 <Zap size={100} />
              </div>
              <div className="relative z-10">
                 <h4 className="text-sm font-black uppercase tracking-tight text-indigo-400 mb-6">Inference Logic Map</h4>
                 <div className="space-y-4">
                    <p className="text-xs text-slate-400 leading-relaxed">
                       The current diagnosis for <span className="text-white font-bold">Infiltrative Pneumonia</span> was reached by weighting the following features:
                    </p>
                    <div className="space-y-3">
                       <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold uppercase text-slate-500">Clinical Symptoms</span>
                          <span className="text-[10px] font-bold text-indigo-400">42% Weight</span>
                       </div>
                       <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: '42%' }} className="h-full bg-indigo-500" />
                       </div>
                    </div>
                    <div className="space-y-3">
                       <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold uppercase text-slate-500">Radiology Metadata</span>
                          <span className="text-[10px] font-bold text-indigo-400">38% Weight</span>
                       </div>
                       <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: '38%' }} className="h-full bg-emerald-500" />
                       </div>
                    </div>
                 </div>
              </div>
           </div>
        </div>

        <div className="p-8 bg-white border border-slate-100 rounded-[3rem] shadow-sm">
           <div className="flex items-center gap-4 mb-8">
              <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
                 <AlertTriangle size={24} />
              </div>
              <div>
                 <h4 className="text-lg font-black uppercase tracking-tight text-slate-900">Suggested Action Verifier</h4>
                 <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest font-mono">Verifying clinical intent against L6 protocol</p>
              </div>
           </div>
           
           <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { title: 'Sputum Culture', reason: 'High CRP requires specific pathogen ID.', probability: '92%' },
                { title: 'Empirical Antibiotics', reason: 'Symptoms and Imaging suggest community acquired.', probability: '85%' },
                { title: 'Isolation Protocol', reason: 'Recent local cluster of atypical markers.', probability: '12%' },
              ].map((rec, i) => (
                <div key={i} className="p-6 bg-slate-50 rounded-3xl border border-transparent hover:border-indigo-100 transition-all flex flex-col justify-between">
                   <div>
                      <h5 className="text-xs font-black text-slate-900 uppercase mb-2">{rec.title}</h5>
                      <p className="text-[10px] text-slate-500 leading-relaxed">{rec.reason}</p>
                   </div>
                   <div className="mt-6 pt-4 border-t border-slate-100 flex justify-between items-center">
                      <span className="text-[9px] font-black uppercase text-indigo-600">Relevance</span>
                      <span className="text-sm font-black text-slate-900">{rec.probability}</span>
                   </div>
                </div>
              ))}
           </div>
        </div>
      </div>
    </div>
  );
}
