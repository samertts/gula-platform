import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, AlertCircle, Shield, 
  Zap, Save, ArrowRight, History, 
  Dna, Beaker, Terminal, Keyboard
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';
import { toast } from 'sonner';
import { useLanguage } from '../../contexts/LanguageContext';

interface TestParameter {
  id: string;
  name: string;
  code: string;
  value: string;
  unit: string;
  referenceRange: string;
  status: 'normal' | 'high' | 'low' | 'critical' | 'none';
  previousValue?: string;
}

interface ResultEntryUIProps {
  taskId: string;
  sampleId: string;
  patientName: string;
  testName: string;
  onSave: (results: TestParameter[]) => void;
  onCancel: () => void;
}

export function ResultEntryUI({ taskId, sampleId, patientName, testName, onSave, onCancel }: ResultEntryUIProps) {
  const { t } = useLanguage();
  const [params, setParams] = useState<TestParameter[]>([
    { id: '1', name: 'Leukocytes (WBC)', code: 'WBC', value: '', unit: '10^3/µL', referenceRange: '4.5 - 11.0', status: 'none', previousValue: '7.2' },
    { id: '2', name: 'Erythrocytes (RBC)', code: 'RBC', value: '', unit: '10^6/µL', referenceRange: '4.5 - 5.9', status: 'none', previousValue: '5.1' },
    { id: '3', name: 'Hemoglobin (HGB)', code: 'HGB', value: '', unit: 'g/dL', referenceRange: '13.5 - 17.5', status: 'none', previousValue: '14.8' },
    { id: '4', name: 'Hematocrit (HCT)', code: 'HCT', value: '', unit: '%', referenceRange: '40.5 - 52.0', status: 'none', previousValue: '44.2' },
    { id: '5', name: 'Platelets (PLT)', code: 'PLT', value: '', unit: '10^3/µL', referenceRange: '150 - 450', status: 'none', previousValue: '210' },
  ]);

  const [activeIndex, setActiveIndex] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);

  const handleValueChange = (id: string, value: string) => {
    setParams(prev => prev.map(p => {
      if (p.id !== id) return p;
      
      let status: TestParameter['status'] = 'normal';
      const numVal = parseFloat(value);
      if (!isNaN(numVal)) {
          const [min, max] = p.referenceRange.split(' - ').map(parseFloat);
          if (numVal < min) status = 'low';
          else if (numVal > max) status = 'high';
          
          // Simulate a critical threshold
          if (p.code === 'WBC' && (numVal > 30 || numVal < 1)) status = 'critical';
          if (p.code === 'HGB' && numVal < 7) status = 'critical';
      } else {
          status = 'none';
      }
      
      return { ...p, value, status };
    }));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      setActiveIndex(prev => (prev + 1) % params.length);
      e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      setActiveIndex(prev => (prev - 1 + params.length) % params.length);
      e.preventDefault();
    } else if (e.key === 'Enter' && e.ctrlKey) {
      handleComplete();
      e.preventDefault();
    }
  };

  useEffect(() => {
    const input = document.getElementById(`param-input-${activeIndex}`);
    input?.focus();
  }, [activeIndex]);

  const handleComplete = () => {
    const unfilledCount = params.filter(p => !p.value).length;
    if (unfilledCount > 0) {
      toast.warning(`${unfilledCount} parameters are still empty`);
      return;
    }

    const criticalCount = params.filter(p => p.status === 'critical').length;
    if (criticalCount > 0) {
      toast.error(`Warning: ${criticalCount} critical results detected`, {
        description: "Protocol requires double-check for all critical values."
      });
    }

    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      onSave(params);
      toast.success('Results Synchronized', {
        description: `Task for ${sampleId} moved to validation phase.`
      });
    }, 1500);
  };

  return (
    <div className="flex flex-col lg:flex-row gap-8 min-h-[600px] bg-slate-50/50 p-2">
      {/* Test Entry Area */}
      <div className="flex-1 bg-white rounded-[3rem] border border-slate-200 shadow-2xl relative overflow-hidden flex flex-col">
        <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-slate-50/30">
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 bg-slate-900 rounded-[2rem] flex items-center justify-center text-white shadow-2xl shadow-slate-200 rotate-3 group-hover:rotate-0 transition-transform">
              <Terminal size={32} />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h3 className="text-2xl font-black text-slate-900 uppercase tracking-tighter">{sampleId}</h3>
                <div className="px-3 py-1 bg-indigo-600 text-white rounded-full text-[9px] font-black uppercase tracking-widest">{testName}</div>
              </div>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{patientName} • {t.resultEntry}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setShowShortcuts(!showShortcuts)}
              className="p-3 hover:bg-slate-100 rounded-2xl transition-colors text-slate-400"
              title={t.keyboardShortcuts}
            >
              <Keyboard size={20} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto no-scrollbar p-8 space-y-4" onKeyDown={handleKeyDown}>
          {params.map((param, index) => (
            <motion.div 
               key={param.id}
               initial={{ opacity: 0, x: -20 }}
               animate={{ opacity: 1, x: 0 }}
               transition={{ delay: index * 0.05 }}
               onClick={() => setActiveIndex(index)}
               className={cn(
                 "flex items-center gap-8 p-6 rounded-[2.5rem] border-2 transition-all cursor-pointer group",
                 activeIndex === index ? "bg-indigo-50/50 border-indigo-600 shadow-xl shadow-indigo-100/50" : "bg-white border-transparent hover:border-slate-100"
               )}
            >
              <div className="w-14 font-black text-slate-300 text-xs tracking-tighter group-active:scale-95 transition-transform">{param.code}</div>
              <div className="flex-1">
                 <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{param.name}</h4>
                 <div className="flex items-baseline gap-2">
                   <span className="text-[10px] font-bold text-slate-300">{t.referenceHighlight}</span>
                   <span className="text-[10px] font-black text-slate-900 group-hover:text-indigo-600 transition-colors">{param.referenceRange} {param.unit}</span>
                 </div>
              </div>

              <div className="w-48 relative">
                 <input 
                   id={`param-input-${index}`}
                   type="text"
                   value={param.value}
                   onChange={(e) => handleValueChange(param.id, e.target.value)}
                   className={cn(
                     "w-full bg-slate-50 border-2 rounded-2xl px-6 py-4 text-xl font-black text-center transition-all outline-none",
                     activeIndex === index ? "border-indigo-600 ring-4 ring-indigo-50" : "border-slate-100",
                     param.status === 'high' || param.status === 'low' ? "text-amber-600 bg-amber-50" : 
                     param.status === 'critical' ? "text-red-600 bg-red-50 animate-pulse" : "text-slate-900"
                   )}
                   placeholder="---"
                 />
                 {param.status === 'critical' && (
                   <AlertCircle size={18} className="absolute -right-8 top-1/2 -translate-y-1/2 text-red-600 animate-bounce" />
                 )}
              </div>

              <div className="w-32 text-right">
                 <span className="text-[10px] font-bold text-slate-400 block uppercase mb-1">{t.deltaCheck || 'Prev'}</span>
                 <div className="flex items-center justify-end gap-1.5">
                    <History size={12} className="text-slate-300" />
                    <span className="text-sm font-black text-slate-900">{param.previousValue || 'N/A'}</span>
                 </div>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="p-8 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between">
           <button 
             onClick={onCancel}
             className="px-8 py-5 border border-slate-200 text-slate-500 rounded-[2rem] font-black text-[10px] uppercase tracking-widest hover:bg-slate-100 active:scale-95 transition-all"
           >
             {t.cancel}
           </button>
           <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                 <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{t.labLoad}</p>
                 <div className="flex items-center gap-1.5 justify-end">
                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                    <span className="text-xs font-black text-slate-900 uppercase tracking-tighter">Cluster Sync Active</span>
                 </div>
              </div>
              <button 
                onClick={handleComplete}
                disabled={isSaving}
                className="px-10 py-5 bg-slate-900 text-white rounded-[2rem] font-black text-[10px] uppercase tracking-[0.2em] shadow-2xl shadow-slate-900/40 hover:bg-black hover:scale-105 active:scale-95 transition-all flex items-center gap-4 group"
              >
                {isSaving ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    {t.saveResults || 'Commit & Validate'}
                    <Shield size={18} className="group-hover:text-indigo-400 transition-colors" />
                  </>
                )}
              </button>
           </div>
        </div>
      </div>

      {/* AI Inspector & Context Sidebar */}
      <div className="w-full lg:w-96 space-y-6">
        <div className="bg-indigo-600 rounded-[3rem] p-8 text-white shadow-2xl shadow-indigo-100 relative overflow-hidden group">
           <div className="absolute top-0 right-0 p-8 opacity-[0.05] pointer-events-none scale-150 rotate-12">
              <Zap size={120} />
           </div>
           <div className="flex items-center gap-3 mb-8 relative z-10">
              <div className="p-3 bg-white/10 rounded-2xl border border-white/20">
                <Dna size={18} className="animate-pulse" />
              </div>
              <h3 className="text-sm font-black uppercase tracking-[0.2em]">Clinical AI Validator</h3>
           </div>

           <div className="space-y-6 relative z-10">
              <div className="p-6 bg-white/10 rounded-[2rem] border border-white/5 backdrop-blur-sm">
                 <p className="text-[10px] font-black uppercase tracking-widest opacity-60 mb-2">Automated Insight</p>
                 <p className="text-sm font-medium leading-relaxed italic">
                    "Pattern suggests mild inflammation. Correlating with patient's historical data from Jan 2024. No immediate high-risk outliers detected."
                 </p>
              </div>

              <div className="space-y-4">
                 <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest">
                    <span>Fidelity Score</span>
                    <span className="text-indigo-200">98.4%</span>
                 </div>
                 <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <motion.div 
                       initial={{ width: 0 }}
                       animate={{ width: '98%' }}
                       className="h-full bg-white shadow-[0_0_10px_white]"
                    />
                 </div>
              </div>

              <button className="w-full py-4 bg-white text-indigo-600 rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-indigo-900/20 hover:scale-105 active:scale-95 transition-all">
                 Full AI Breakdown
              </button>
           </div>
        </div>

        <div className="bg-white rounded-[3rem] border border-slate-200 p-8 shadow-sm">
           <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-6">{t.deviceStatus}</h3>
           <div className="space-y-4">
              {[
                { name: 'X-Gen Hemato-04', status: 'Online', perf: 100, color: 'emerald' },
                { name: 'Sysmex Calibrator', status: 'Active', perf: 92, color: 'indigo' },
                { name: 'Cluster Data Link', status: 'Stable', perf: 100, color: 'emerald' }
              ].map((device, i) => (
                <div key={i} className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100">
                   <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full bg-${device.color}-500 animate-pulse`} />
                      <span className="text-[10px] font-black text-slate-900 uppercase">{device.name}</span>
                   </div>
                   <span className="text-[10px] font-bold text-slate-400">{device.perf}%</span>
                </div>
              ))}
           </div>
           <button className="w-full mt-6 py-4 bg-slate-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-indigo-600 transition-all flex items-center justify-center gap-2">
              <Beaker size={14} /> {t.autoImport}
           </button>
        </div>

        <AnimatePresence>
          {showShortcuts && (
            <motion.div 
               initial={{ opacity: 0, y: 10 }}
               animate={{ opacity: 1, y: 0 }}
               exit={{ opacity: 0, y: 10 }}
               className="bg-slate-900 text-white p-8 rounded-[3rem] shadow-2xl relative"
            >
               <h4 className="text-[10px] font-black uppercase tracking-widest text-indigo-400 mb-6">Pro Navigation</h4>
               <div className="grid grid-cols-2 gap-4">
                  {[
                    { key: '↑/↓', desc: 'Navigate' },
                    { key: 'Tab', desc: 'Focus Value' },
                    { key: 'Ctrl+Enter', desc: 'Commit All' },
                    { key: 'Esc', desc: 'Discard' }
                  ].map((shortcut, i) => (
                    <div key={i} className="space-y-1">
                       <kbd className="px-2 py-1 bg-white/10 rounded text-[9px] font-black uppercase tracking-tighter">{shortcut.key}</kbd>
                       <p className="text-[8px] font-medium text-slate-400 uppercase tracking-widest">{shortcut.desc}</p>
                    </div>
                  ))}
               </div>
               <button onClick={() => setShowShortcuts(false)} className="absolute top-6 right-6 text-slate-500 hover:text-white transition-colors">
                  <X size={14} />
               </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function X({ size, className }: { size: number; className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
    </svg>
  );
}
