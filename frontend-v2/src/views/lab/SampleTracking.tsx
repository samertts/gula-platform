import React, { useState } from 'react';
import { 
  Search, Scan, Beaker, CheckCircle2, 
  Truck, Microscope, ShieldCheck, Clock,
  ArrowRight, MoreVertical, History, MapPin,
  QrCode, Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';
import { useLanguage } from '../../contexts/LanguageContext';

interface SampleStep {
  id: string;
  name: string;
  status: 'completed' | 'current' | 'pending' | 'warning';
  timestamp: string;
  user?: string;
  location?: string;
  notes?: string;
}

interface SampleRecord {
  id: string;
  patientName: string;
  patientId: string;
  type: string;
  collectedAt: string;
  priority: 'routine' | 'urgent' | 'stat';
  steps: SampleStep[];
}

export function SampleTracking() {
  const { t } = useLanguage();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSample, setActiveSample] = useState<SampleRecord | null>({
    id: 'SMP-8832-QL',
    patientName: 'Ahmed Mohammed Ali',
    patientId: 'PAT-0044-K',
    type: 'Whole Blood (EDTA)',
    collectedAt: '2024-03-20 08:30 AM',
    priority: 'stat',
    steps: [
      { id: '1', name: t.collected || 'Collected', status: 'completed', timestamp: '08:35 AM', user: 'Nurse Laila', location: 'Ward 4, Node Alpha' },
      { id: '2', name: 'Dispatched', status: 'completed', timestamp: '08:42 AM', user: 'Courier-Logistics', location: 'Pneumatic Tube System' },
      { id: '3', name: t.inLab || 'In Lab', status: 'completed', timestamp: '08:45 AM', user: 'Lab Reception', location: 'Central Sorting' },
      { id: '4', name: 'Processing', status: 'current', timestamp: 'Executing', user: 'Robot-Arm-04', location: 'Hematology Analyzer A1', notes: 'Analyzer calibration confirmed.' },
      { id: '5', name: t.verified || 'Verified', status: 'pending', timestamp: 'ETA 09:10 AM' },
      { id: '6', name: t.delivered || 'Delivered', status: 'pending', timestamp: 'ETA 09:15 AM' },
    ]
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-12">
      {/* Header & Scanner Integration */}
      <div className="flex flex-col lg:flex-row items-center justify-between gap-8 bg-slate-900 rounded-[3.5rem] p-12 text-white shadow-2xl relative overflow-hidden group">
         <div className="absolute top-0 right-0 p-12 opacity-[0.03] pointer-events-none scale-150 rotate-12">
            <QrCode size={240} />
         </div>

         <div className="relative z-10 flex items-center gap-8">
            <div className="w-20 h-20 bg-indigo-600 rounded-[2.5rem] flex items-center justify-center text-white shadow-2xl shadow-indigo-500/20 group-hover:scale-110 transition-transform">
               <Scan size={40} className="animate-pulse" />
            </div>
            <div>
               <h1 className="text-4xl font-black tracking-tighter uppercase leading-none mb-2">{t.scanBarcode}</h1>
               <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">Neural Scanner Ready</span>
               </div>
            </div>
         </div>

         <div className="relative z-10 w-full lg:w-96">
            <div className="relative group">
               <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-white transition-colors" size={24} />
               <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Enter Sample ID or Scan..."
                  className="w-full bg-white/5 border-2 border-white/10 rounded-[2rem] py-6 pl-20 pr-8 text-xl font-black tracking-tighter text-white outline-none focus:border-indigo-600 focus:bg-white/10 transition-all placeholder:text-slate-600"
               />
               <div className="absolute right-6 top-1/2 -translate-y-1/2 flex gap-2">
                  <kbd className="px-2 py-1 bg-white/10 rounded text-[9px] font-black uppercase tracking-tighter opacity-40 italic">Ctrl+S</kbd>
               </div>
            </div>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
         {/* Sample Data & Metadata */}
         <div className="lg:col-span-4 space-y-6">
            <AnimatePresence mode="wait">
               {activeSample && (
                  <motion.div 
                     initial={{ opacity: 0, y: 20 }}
                     animate={{ opacity: 1, y: 0 }}
                     className="bg-white rounded-[3rem] border border-slate-200 p-8 shadow-sm flex flex-col items-center text-center group"
                  >
                     <div className={cn(
                        "w-32 h-32 rounded-[3.5rem] flex items-center justify-center text-white shadow-2xl mb-8 group-hover:scale-105 transition-transform",
                        activeSample.priority === 'stat' ? 'bg-red-600 shadow-red-200' : 'bg-slate-900 shadow-slate-200'
                     )}>
                        <QrCode size={56} />
                     </div>
                     
                     <h3 className="text-3xl font-black text-slate-900 uppercase tracking-tighter mb-2">{activeSample.id}</h3>
                     <div className="px-6 py-2 bg-slate-900 text-white rounded-full text-[10px] font-black uppercase tracking-[0.2em] mb-8">
                        {activeSample.type}
                     </div>

                     <div className="w-full space-y-4 text-left border-t border-slate-100 pt-8">
                        <div className="p-6 bg-slate-50 rounded-3xl">
                           <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">Patient Subject</span>
                           <p className="text-lg font-black text-slate-900 tracking-tight leading-none">{activeSample.patientName}</p>
                           <p className="text-[10px] font-bold text-indigo-600 mt-1 uppercase">{activeSample.patientId}</p>
                        </div>
                        
                        <div className="p-6 bg-slate-50 rounded-3xl">
                           <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">Collection Instance</span>
                           <p className="text-sm font-bold text-slate-900">{activeSample.collectedAt}</p>
                        </div>
                     </div>

                     <button className="w-full mt-8 py-5 bg-white border-2 border-slate-900 text-slate-900 rounded-3xl font-black text-[10px] uppercase tracking-widest hover:bg-slate-900 hover:text-white active:scale-95 transition-all flex items-center justify-center gap-3">
                        {t.printLabel || 'Generate Bio-ID Tag'} <QrCode size={16} />
                     </button>
                  </motion.div>
               )}
            </AnimatePresence>

            <div className="bg-indigo-600 rounded-[3rem] p-8 text-white shadow-2xl shadow-indigo-100 relative overflow-hidden">
               <div className="absolute top-0 right-0 p-8 opacity-[0.05] pointer-events-none scale-150 rotate-12">
                  <Zap size={120} />
               </div>
               <h3 className="text-sm font-black uppercase tracking-[0.2em] mb-8 relative z-10">Integration Link</h3>
               <div className="space-y-4 relative z-10">
                  <div className="flex justify-between items-center text-xs">
                     <span className="opacity-60 font-medium">Physician Node</span>
                     <span className="font-black uppercase text-emerald-400">Synced</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                     <span className="opacity-60 font-medium">Global Grid</span>
                     <span className="font-black uppercase text-emerald-400">Authenticated</span>
                  </div>
               </div>
            </div>
         </div>

         {/* Lifecycle Timeline */}
         <div className="lg:col-span-8 space-y-6">
            <div className="bg-white rounded-[3rem] border border-slate-200 p-12 shadow-sm relative">
               <div className="absolute top-12 right-12">
                  <div className="flex gap-2">
                     <button className="p-3 bg-slate-50 rounded-2xl text-slate-400 hover:text-indigo-600 transition-all border border-transparent hover:border-slate-100">
                        <History size={18} />
                     </button>
                     <button className="p-3 bg-slate-50 rounded-2xl text-slate-400 hover:text-indigo-600 transition-all border border-transparent hover:border-slate-100">
                        <MoreVertical size={18} />
                     </button>
                  </div>
               </div>

               <h2 className="text-2xl font-black text-slate-900 tracking-tight uppercase mb-12 flex items-center gap-3">
                  <Clock className="text-indigo-600" /> Operational Lifecycle
               </h2>

               <div className="relative">
                  {/* Vertical Line */}
                  <div className="absolute left-6 top-4 bottom-4 w-1 bg-slate-100 rounded-full" />

                  <div className="space-y-12">
                     {activeSample?.steps.map((step, idx) => (
                        <div key={step.id} className="relative flex gap-10">
                           <div className={cn(
                              "relative z-10 w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 shadow-2xl transition-all duration-500",
                              step.status === 'completed' ? "bg-emerald-600 text-white shadow-emerald-100 scale-90" : 
                              step.status === 'current' ? "bg-indigo-600 text-white shadow-indigo-200 scale-110 ring-4 ring-indigo-50" : 
                              "bg-slate-100 text-slate-300"
                           )}>
                              {step.status === 'completed' ? <CheckCircle2 size={24} /> : 
                               step.status === 'current' ? <Zap size={24} className="animate-pulse" /> : 
                               <Clock size={24} />}
                           </div>

                           <div className="flex-1 pb-4 border-b border-slate-50">
                              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                                 <div>
                                    <h4 className={cn(
                                       "text-xl font-black uppercase tracking-tight",
                                       step.status === 'pending' ? "text-slate-300" : "text-slate-900"
                                    )}>
                                       {step.name}
                                    </h4>
                                    {step.status === 'current' && (
                                       <span className="text-[9px] font-black text-indigo-600 uppercase tracking-widest bg-indigo-50 px-2 py-0.5 rounded-full mt-1 inline-block animate-pulse">In Progress</span>
                                    )}
                                 </div>
                                 <div className="flex items-center gap-1.5 text-[10px] font-black text-slate-400 uppercase tracking-widest whitespace-nowrap">
                                    <Clock size={12} />
                                    {step.timestamp}
                                 </div>
                              </div>
                              
                              <AnimatePresence>
                                 {(step.status === 'completed' || step.status === 'current') && (
                                    <motion.div 
                                       initial={{ height: 0, opacity: 0 }}
                                       animate={{ height: 'auto', opacity: 1 }}
                                       className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-4 overflow-hidden"
                                    >
                                       <div className="flex items-center gap-3">
                                          <div className="w-8 h-8 bg-slate-50 rounded-xl flex items-center justify-center text-slate-400 border border-slate-100">
                                             <MapPin size={14} />
                                          </div>
                                          <span className="text-[10px] font-black text-slate-500 uppercase tracking-tight">{step.location}</span>
                                       </div>
                                       <div className="flex items-center gap-3 text-right sm:justify-end">
                                          <span className="text-[10px] font-black text-slate-500 uppercase tracking-tight">{step.user}</span>
                                          <div className="w-8 h-8 bg-slate-50 rounded-xl flex items-center justify-center text-slate-400 border border-slate-100">
                                             <ShieldCheck size={14} />
                                          </div>
                                       </div>
                                    </motion.div>
                                 )}
                              </AnimatePresence>

                              {step.notes && (
                                 <div className="mt-4 p-4 bg-slate-50 rounded-2xl italic text-xs text-slate-500 border-l-2 border-indigo-600">
                                    "{step.notes}"
                                 </div>
                              )}
                           </div>
                        </div>
                     ))}
                  </div>
               </div>

               <div className="mt-16 flex items-center gap-4 p-8 bg-emerald-50 rounded-[2.5rem] border border-emerald-100 shadow-xl shadow-emerald-50/50">
                  <div className="w-14 h-14 bg-emerald-600 rounded-[1.25rem] flex items-center justify-center text-white shadow-lg">
                     <CheckCircle2 size={32} />
                  </div>
                  <div className="flex-1">
                     <h4 className="text-sm font-black text-emerald-900 uppercase tracking-tight">Zero-Delay Pipeline Active</h4>
                     <p className="text-[10px] font-bold text-emerald-700/60 uppercase tracking-widest leading-none mt-1">Sample is ahead of predicted TAT schedule by 4.2 minutes.</p>
                  </div>
                  <button className="px-8 py-4 bg-emerald-600 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-emerald-700 transition-all active:scale-95 shadow-lg shadow-emerald-200">
                     Detailed Analytics
                  </button>
               </div>
            </div>
         </div>
      </div>
    </div>
  );
}
