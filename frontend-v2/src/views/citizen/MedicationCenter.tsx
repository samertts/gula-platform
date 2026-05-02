import React, { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Pill, Plus, Clock, CheckCircle2, AlertCircle, 
  Trash2, Calendar, TrendingUp, Info, Activity,
  Download, BrainCircuit, Bell
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';

interface Medication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  reminder: string;
  lastTaken?: string;
  warning?: string;
  type: 'prescription' | 'supplement';
  adherence: number;
}

export function MedicationCenter() {
  const { t } = useLanguage();
  const [meds, setMeds] = useState<Medication[]>([
    { id: '1', name: 'Metformin', dosage: '500mg', frequency: 'Twice daily', reminder: '08:00, 20:00', lastTaken: 'Today, 08:15', warning: 'Take with food', type: 'prescription', adherence: 98 },
    { id: '2', name: 'Vitamin D3', dosage: '2000 IU', frequency: 'Once daily', reminder: '09:00', lastTaken: 'Today, 09:05', type: 'supplement', adherence: 100 },
    { id: '3', name: 'Lisinopril', dosage: '10mg', frequency: 'Once daily', reminder: '08:00', warning: 'Avoid high potassium', type: 'prescription', adherence: 85 }
  ]);

  return (
    <div className="space-y-10 max-w-7xl mx-auto p-4 md:p-8 animate-in fade-in duration-500 pb-20">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 text-indigo-900">
        <div className="editorial-stack">
          <span className="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-600 mb-2 block">{t.medicationAdherence}</span>
          <h1 className="text-4xl font-black tracking-tighter leading-none italic">{t.medicineCabinet}</h1>
          <p className="text-slate-500 mt-2 font-medium">Manage your prescriptions and supplements with AI-powered reminders.</p>
        </div>
        <div className="flex gap-3 w-full md:w-auto">
           <button className="flex-1 md:flex-none px-8 py-4 bg-slate-900 text-white rounded-[2rem] font-black text-xs uppercase tracking-widest shadow-xl flex items-center justify-center gap-3 hover:scale-[1.02] transition-all">
              <Plus size={18} /> {t.addMedication}
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Adherence Overview */}
        <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-3 gap-8">
           <StatCard label="Weekly Adherence" value="94%" trend="+2%" icon={Activity} color="text-indigo-600" />
           <StatCard label="Active Medications" value={String(meds.length)} trend="Stable" icon={Pill} color="text-emerald-600" />
           <StatCard label="Next Refill" value="12 Days" trend="Metformin" icon={Calendar} color="text-amber-600" />
        </div>

        {/* Medication Grid */}
        <div className="lg:col-span-8 flex flex-col gap-6">
           <div className="flex items-center justify-between px-4">
              <h3 className="text-xl font-black text-slate-900 tracking-tighter italic">Ongoing Therapy</h3>
              <div className="flex gap-2">
                 <button className="p-2 text-slate-400 hover:text-indigo-600 transition-colors"><Bell size={20} /></button>
                 <button className="p-2 text-slate-400 hover:text-indigo-600 transition-colors"><Download size={20} /></button>
              </div>
           </div>
           
           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
               <AnimatePresence mode="popLayout">
                 {meds.map((med) => (
                   <motion.div 
                     key={med.id}
                     layout
                     initial={{ opacity: 0, scale: 0.95 }}
                     animate={{ opacity: 1, scale: 1 }}
                     className="bg-white p-8 rounded-[3rem] border border-slate-200 shadow-sm relative group overflow-hidden"
                   >
                     <div className={cn(
                        "absolute top-0 right-0 p-6 opacity-5",
                        med.type === 'prescription' ? "text-indigo-600" : "text-emerald-600"
                     )}>
                        <Pill size={80} />
                     </div>

                     <div className="flex items-center gap-6 mb-8">
                        <div className={cn(
                          "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg border",
                          med.type === 'prescription' ? "bg-indigo-50 border-indigo-100 text-indigo-600" : "bg-emerald-50 border-emerald-100 text-emerald-600"
                        )}>
                          <Pill size={28} />
                        </div>
                        <div>
                           <h4 className="text-xl font-black text-slate-900 tracking-tighter leading-none mb-1">{med.name}</h4>
                           <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{med.dosage} • {med.frequency}</p>
                        </div>
                     </div>

                     <div className="space-y-4 relative z-10">
                        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-transparent hover:border-slate-100 transition-all">
                           <div className="flex items-center gap-2 text-[10px] font-black uppercase text-slate-400 tracking-widest">
                              <Clock size={12} /> Daily reminders
                           </div>
                           <span className="text-[10px] font-black text-indigo-600">{med.reminder}</span>
                        </div>

                        {med.lastTaken ? (
                          <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-2xl">
                             <div className="flex items-center gap-2 text-[10px] font-black uppercase text-emerald-600 tracking-widest">
                                <CheckCircle2 size={12} /> Confirmed Today
                             </div>
                             <span className="text-[10px] font-black text-emerald-700">{med.lastTaken.split(',')[1]}</span>
                          </div>
                        ) : (
                          <button className="w-full py-4 bg-indigo-600 text-white rounded-[1.5rem] font-black text-[10px] uppercase tracking-widest shadow-lg shadow-indigo-100 hover:bg-slate-900 transition-all">
                             Take Now
                          </button>
                        )}

                        {med.warning && (
                          <div className="p-4 bg-red-50 border border-red-100/50 rounded-2xl flex items-start gap-3">
                             <AlertCircle size={14} className="text-red-600 shrink-0 mt-0.5" />
                             <p className="text-[9px] font-bold text-red-700 leading-relaxed uppercase tracking-tighter italic">
                                Inter-Action Warning: {med.warning}
                             </p>
                          </div>
                        )}
                        
                        <div className="pt-4 flex items-center justify-between border-t border-slate-100">
                           <div className="flex items-center gap-2">
                              <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                 <motion.div 
                                    initial={{ width: 0 }}
                                    animate={{ width: `${med.adherence}%` }}
                                    className="h-full bg-indigo-500 rounded-full"
                                 />
                              </div>
                              <span className="text-[9px] font-black uppercase text-slate-400">Adherence: {med.adherence}%</span>
                           </div>
                           <button className="p-2 text-slate-300 hover:text-red-500 transition-colors"><Trash2 size={16} /></button>
                        </div>
                     </div>
                   </motion.div>
                 ))}
               </AnimatePresence>
           </div>
        </div>

        {/* AI Insight Sidebar */}
        <div className="lg:col-span-4 space-y-8">
           <div className="bg-slate-900 text-white rounded-[3.5rem] p-10 relative overflow-hidden group shadow-2xl">
              <div className="absolute top-0 right-0 p-10 opacity-10 group-hover:rotate-12 transition-transform">
                <BrainCircuit size={140} />
              </div>
              <h3 className="text-xl font-black uppercase tracking-widest mb-8 italic">AI Pharmacist</h3>
              <div className="space-y-6 relative z-10">
                 <p className="text-lg font-medium leading-relaxed italic text-indigo-100">
                    "I noticed you missed your **Lisinopril** twice last week. Maintaining consistent blood pressure medication is crucial for long-term cardiac stability."
                 </p>
                 <div className="p-6 bg-white/5 border border-white/10 rounded-[2rem] flex items-start gap-4">
                    <Info size={20} className="text-indigo-400 shrink-0" />
                    <div>
                       <h5 className="text-[10px] font-black uppercase tracking-widest mb-1 text-indigo-400">Optimization Tip</h5>
                       <p className="text-[11px] text-slate-400 leading-relaxed">Try taking your medications immediately after your morning coffee to build a habitual anchor.</p>
                    </div>
                 </div>
                 <button className="w-full py-4 bg-indigo-600 text-white rounded-[1.5rem] font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-3">
                    Consult AI Assistant <TrendingUp size={16} />
                 </button>
              </div>
           </div>

           <div className="bg-white border border-slate-200 rounded-[3.5rem] p-10 space-y-8">
              <h3 className="text-xl font-black tracking-tight leading-none italic">Refill Status</h3>
              <div className="space-y-6">
                 {[
                   { name: 'Metformin', status: 'Low Stock', balance: '4 Pills', color: 'bg-amber-100 text-amber-700' },
                   { name: 'Vitamin D3', status: 'Optimal', balance: '22 Pills', color: 'bg-emerald-100 text-emerald-700' }
                 ].map((refill, i) => (
                   <div key={i} className="flex items-center justify-between">
                      <div>
                         <p className="text-sm font-bold text-slate-900">{refill.name}</p>
                         <p className="text-[10px] text-slate-400 font-bold uppercase">{refill.balance} remaining</p>
                      </div>
                      <span className={cn("px-3 py-1 rounded-full text-[9px] font-black uppercase", refill.color)}>
                         {refill.status}
                      </span>
                   </div>
                 ))}
                 <button className="w-full py-4 bg-slate-900 text-white rounded-[2rem] font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 shadow-lg shadow-slate-200">
                    Order Refills <Plus size={16} />
                 </button>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, trend, icon: Icon, color }: any) {
  return (
    <div className="bg-white p-8 rounded-[3rem] border border-slate-200 shadow-sm relative overflow-hidden group">
       <div className={cn("absolute bottom-0 right-0 p-8 opacity-5 transition-transform group-hover:scale-125", color)}>
          <Icon size={100} />
       </div>
       <div className="relative z-10">
          <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-2">{label}</p>
          <div className="flex items-baseline gap-3">
             <span className={cn("text-4xl font-black tracking-tighter leading-none italic", color)}>{value}</span>
             <span className="text-xs font-bold text-slate-400">{trend}</span>
          </div>
       </div>
    </div>
  );
}
