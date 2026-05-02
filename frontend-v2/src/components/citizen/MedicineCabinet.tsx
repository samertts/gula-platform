import React, { useState } from 'react';
import { Pill, Plus, AlertCircle, Clock, CheckCircle2, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';

interface Medication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  reminder: string;
  lastTaken?: string;
  warning?: string;
}

export function MedicineCabinet() {
  const { t } = useLanguage();
  const [meds, setMeds] = useState<Medication[]>([
    { id: '1', name: 'Metformin', dosage: '500mg', frequency: 'Twice daily', reminder: '08:00, 20:00', lastTaken: 'Today, 08:15', warning: 'Take with food' },
    { id: '2', name: 'Vitamin D3', dosage: '2000 IU', frequency: 'Once daily', reminder: '09:00', lastTaken: 'Today, 09:05' },
    { id: '3', name: 'Lisinopril', dosage: '10mg', frequency: 'Once daily', reminder: '08:00', warning: 'Avoid high potassium' }
  ]);

  return (
    <div className="bg-white rounded-[2.5rem] border border-slate-200 p-8 shadow-sm">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl">
            <Pill size={24} />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight">{t.medicineCabinet}</h3>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active Prescriptions</p>
          </div>
        </div>
        <button className="p-4 bg-slate-900 text-white rounded-2xl hover:scale-105 active:scale-95 transition-all shadow-lg flex items-center gap-2">
          <Plus size={20} />
          <span className="text-xs font-bold uppercase tracking-widest px-2">{t.addMedication}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <AnimatePresence>
          {meds.map((med) => (
            <motion.div
              key={med.id}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="group p-6 bg-slate-50 rounded-3xl border border-transparent hover:border-indigo-100 hover:bg-white transition-all relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="p-2 text-slate-400 hover:text-red-500 transition-colors">
                  <Trash2 size={16} />
                </button>
              </div>

              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-indigo-600 shadow-sm border border-slate-100">
                  <Pill size={24} />
                </div>
                <div>
                  <h4 className="font-bold text-slate-900">{med.name}</h4>
                  <p className="text-xs text-slate-400 font-medium">{med.dosage} • {med.frequency}</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-white/50 rounded-xl">
                  <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    <Clock size={12} /> {t.reminders}
                  </div>
                  <span className="text-[10px] font-black text-indigo-600">{med.reminder}</span>
                </div>

                {med.lastTaken ? (
                  <div className="flex items-center justify-between p-3 bg-emerald-50 rounded-xl">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-emerald-600 uppercase tracking-widest">
                      <CheckCircle2 size={12} /> Last Taken
                    </div>
                    <span className="text-[10px] font-black text-emerald-700">{med.lastTaken}</span>
                  </div>
                ) : (
                  <button className="w-full py-3 bg-indigo-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-700 transition-colors">
                    Mark as Taken
                  </button>
                )}

                {med.warning && (
                  <div className="flex items-center gap-2 p-3 bg-amber-50 rounded-xl border border-amber-100/50">
                    <AlertCircle size={12} className="text-amber-600 shrink-0" />
                    <span className="text-[9px] font-bold text-amber-700 leading-tight uppercase tracking-tighter italic">
                      {t.interactionWarning}: {med.warning}
                    </span>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
