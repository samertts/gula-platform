import React, { useState, useEffect } from 'react';
import { 
  Pill, AlertTriangle, CheckCircle2, 
  Trash2, Plus, Zap, Info, ShieldCheck,
  Search, Calculator
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';

interface PrescriptionItem {
  id: string;
  drug: string;
  dosage: string;
  frequency: string;
  duration: string;
  route: string;
  interactionAlert?: string;
  doseWarning?: string;
}

export function PrescriptionBuilder() {
  const [items, setItems] = useState<PrescriptionItem[]>([]);
  const [isSignModalOpen, setIsSignModalOpen] = useState(false);
  const [activeSearch, setActiveSearch] = useState('');
  
  const drugDatabase = [
    { name: 'Metformin', class: 'Biguanide', interactions: ['Contrast Media'] },
    { name: 'Lisinopril', class: 'ACE Inhibitor', interactions: ['Potassium Supplements'] },
    { name: 'Warfarin', class: 'Anticoagulant', interactions: ['NSAIDs', 'Vitamin K'] },
    { name: 'Amoxicillin', class: 'Antibiotic', interactions: [] },
  ];

  const addDrug = (drugName: string) => {
    const newItem: PrescriptionItem = {
      id: Math.random().toString(36).substr(2, 9),
      drug: drugName,
      dosage: '500mg',
      frequency: 'BID',
      duration: '7 days',
      route: 'Oral'
    };
    
    // Simple Interaction Check
    const currentDrugs = items.map(i => i.drug);
    if (drugName === 'Warfarin' && currentDrugs.includes('Metformin')) {
      newItem.interactionAlert = 'Potential interaction with Metformin detected. Monitor closely.';
    }

    setItems([...items, newItem]);
    setActiveSearch('');
  };

  const removeDrug = (id: string) => {
    setItems(items.filter(i => i.id !== id));
  };

  return (
    <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden flex flex-col min-h-[600px]">
      <div className="p-8 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold flex items-center gap-3">
            <Pill className="text-emerald-600" />
            Clinical Prescription Builder
          </h3>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Weight-Adjusted Dosing Hub v2.0</p>
        </div>
        <div className="flex items-center gap-3">
           <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-600 border border-emerald-100 rounded-xl">
              <ShieldCheck size={16} />
              <span className="text-[10px] font-black uppercase tracking-widest text-[8px]">Interaction Guard Active</span>
           </div>
        </div>
      </div>

      <div className="flex-1 p-8 space-y-8">
        {/* Drug Search */}
        <div className="relative group">
          <div className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-400">
            <Search size={20} />
          </div>
          <input 
            type="text"
            value={activeSearch}
            onChange={(e) => setActiveSearch(e.target.value)}
            placeholder="Search pharmacopeia by generic or brand name..."
            className="w-full bg-slate-100 border border-transparent rounded-2xl py-6 pl-16 pr-8 text-sm focus:bg-white focus:border-emerald-500 transition-all focus:ring-4 focus:ring-emerald-50"
          />
          
          <AnimatePresence>
            {activeSearch && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-3xl shadow-2xl z-20 overflow-hidden p-2"
              >
                {drugDatabase.filter(d => d.name.toLowerCase().includes(activeSearch.toLowerCase())).map(drug => (
                  <button 
                    key={drug.name}
                    onClick={() => addDrug(drug.name)}
                    className="w-full flex items-center justify-between p-4 hover:bg-slate-50 rounded-2xl transition-all"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center">
                        <Pill size={18} />
                      </div>
                      <div className="text-left">
                        <p className="text-sm font-bold text-slate-900">{drug.name}</p>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{drug.class}</p>
                      </div>
                    </div>
                    <Plus size={18} className="text-slate-300" />
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Selected Drugs */}
        <div className="space-y-4">
          <AnimatePresence mode="popLayout">
            {items.map((item) => (
              <motion.div 
                key={item.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="p-6 bg-slate-50 border border-slate-100 rounded-[2rem] hover:border-emerald-200 transition-all relative group"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="flex items-center gap-6">
                    <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center text-emerald-600 shadow-sm border border-slate-200/50">
                      <Pill size={28} />
                    </div>
                    <div>
                      <h4 className="text-lg font-black text-slate-900 tracking-tight">{item.drug}</h4>
                      <div className="flex gap-4 mt-1">
                        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase">
                          <Calculator size={12} /> Standard Dose: 500mg
                        </div>
                        <div className="flex items-center gap-2 text-[10px] font-bold text-emerald-600 uppercase">
                           <Zap size={12} /> Optimized for weight
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {['Dosage', 'Frequency', 'Duration', 'Route'].map((label) => (
                      <div key={label} className="bg-white px-4 py-2 rounded-xl border border-slate-200">
                        <span className="text-[8px] font-black uppercase text-slate-400 block mb-0.5">{label}</span>
                        <input 
                          type="text" 
                          defaultValue={label === 'Dosage' ? item.dosage : label === 'Frequency' ? item.frequency : label === 'Duration' ? item.duration : item.route}
                          className="bg-transparent text-[10px] font-bold text-slate-900 focus:outline-none w-16"
                        />
                      </div>
                    ))}
                    <button 
                      onClick={() => removeDrug(item.id)}
                      className="p-3 bg-rose-50 text-rose-500 rounded-xl hover:bg-rose-500 hover:text-white transition-all flex items-center justify-center"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                {item.interactionAlert && (
                  <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-center gap-4 text-amber-900">
                    <AlertTriangle size={20} className="text-amber-600 shrink-0" />
                    <p className="text-[10px] font-bold uppercase tracking-tight">{item.interactionAlert}</p>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {items.length === 0 && (
            <div className="text-center py-20 bg-slate-50 border border-dashed border-slate-200 rounded-[2.5rem]">
               <Pill size={48} className="text-slate-200 mx-auto mb-4" />
               <p className="text-slate-400 font-bold">No medications added to the buffer. Search pharmacopeia to begin.</p>
            </div>
          )}
        </div>
      </div>

      <div className="p-8 border-t border-slate-100 bg-slate-50/30 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white rounded-xl border border-slate-200 flex items-center gap-2">
            <Info size={14} className="text-indigo-400" />
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Total Buffer: {items.length} Drugs</span>
          </div>
        </div>
        <button 
          disabled={items.length === 0}
          onClick={() => setIsSignModalOpen(true)}
          className={cn(
            "px-10 py-5 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all shadow-xl flex items-center gap-3",
            items.length > 0 ? "bg-indigo-600 text-white shadow-indigo-200 hover:scale-[1.02] active:scale-95" : "bg-slate-200 text-slate-400 cursor-not-allowed"
          )}
        >
          Finalize & Sign [F] <CheckCircle2 size={18} />
        </button>
      </div>

      {/* Signature Modal */}
      <AnimatePresence>
        {isSignModalOpen && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsSignModalOpen(false)}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-md"
            />
            <motion.div 
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative bg-white w-full max-w-xl rounded-[3rem] shadow-2xl p-12"
            >
              <div className="text-center mb-10">
                <div className="w-20 h-20 bg-indigo-50 text-indigo-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
                  <ShieldCheck size={40} />
                </div>
                <h3 className="text-2xl font-black text-slate-900 tracking-tight">Clinical Authentication</h3>
                <p className="text-xs text-slate-400 font-bold mt-2 uppercase tracking-widest">Digital Signature Required for Prescription</p>
              </div>

              <div className="space-y-6">
                 <div className="p-6 bg-slate-50 border border-slate-100 rounded-[2rem]">
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-4">Review Order Batch</p>
                    <div className="space-y-2">
                       {items.map(i => (
                         <div key={i.id} className="flex justify-between items-center bg-white p-3 rounded-xl border border-slate-100">
                            <span className="text-xs font-bold text-slate-900">{i.drug}</span>
                            <span className="text-[10px] font-black text-slate-400 uppercase">{i.dosage} • {i.duration}</span>
                         </div>
                       ))}
                    </div>
                 </div>

                 <div className="space-y-2">
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 pl-2">Medical PIN</p>
                    <input 
                      type="password" 
                      placeholder="••••"
                      className="w-full bg-slate-100 border border-transparent rounded-[1.5rem] py-6 text-center text-4xl tracking-[1em] focus:bg-white focus:border-indigo-600 transition-all"
                    />
                 </div>

                 <button 
                   onClick={() => setIsSignModalOpen(false)}
                   className="w-full py-6 bg-indigo-600 text-white rounded-[1.5rem] font-black text-xs uppercase tracking-widest shadow-2xl shadow-indigo-200 hover:bg-indigo-700 transition-all"
                 >
                   Confirm Clinical Sign-off
                 </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
