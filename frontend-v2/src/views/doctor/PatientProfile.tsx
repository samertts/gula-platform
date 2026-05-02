import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useLanguage } from '../../contexts/LanguageContext';
import { Skeleton } from '../../components/ui/Skeleton';
import { 
  ArrowLeft, Activity as ActivityIcon, FlaskConical, Pill, 
  Calendar, CheckCircle2, AlertCircle, ChevronRight,
  TrendingUp, Download, Share2, ClipboardList,
  Stethoscope, Send, Plus, Zap, FileText, Search,
  History as HistoryIcon, Beaker, MapPin, BrainCircuit, Layers, Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';
import { LabTestResult } from '../../types/domain';

import { ClinicalSummaryBento } from '../../components/doctor/ClinicalSummaryBento';
import { AITriageAssistant } from '../../components/doctor/AITriageAssistant';
import { PrescriptionBuilder } from '../../components/doctor/PrescriptionBuilder';
import { ClinicalNotes } from '../../components/doctor/ClinicalNotes';

export function PatientProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<'timeline' | 'lab' | 'radiology' | 'prescriptions' | 'notes' | 'ai' | 'history' | 'synthesis' | 'triage'>('synthesis');
  const [showAppointmentModal, setShowAppointmentModal] = useState(false);
  const [showTrendModal, setShowTrendModal] = useState(false);
  const [historyFilter, setHistoryFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(false);

  // Mock patient data
  const patient = {
    name: "Ahmed Mansour",
    id: "P-9021",
    nationalHealthId: "GULA-882-99-XC",
    age: 42,
    gender: "Male",
    blood: "A+",
    weight: "78kg",
    height: "176cm",
    lastVisit: "2024-04-12",
    clinicalSummary: "Patient presenting with recurrent abdominal pain and fatigue. History of mild hypertension."
  };

  // Check for low bandwidth preference
  useEffect(() => {
    const isLow = localStorage.getItem('gula_low_bandwidth') === 'true';
    if (isLow) {
      setIsLoading(true);
      const timer = setTimeout(() => setIsLoading(false), 2000);
      return () => clearTimeout(timer);
    }
  }, []);

  const criticalAlerts = [
    { id: 'a1', text: "Last HbA1c (7.2%) indicates poorly controlled glycemic index.", type: 'warning' },
    { id: 'a2', text: "Scheduled for Re-test: Lipids Panel in 48h.", type: 'info' }
  ];

  const timeline = [
    { date: '2024-04-12', type: 'visit', title: 'Consultation: Abdominal Pain', provider: 'Dr. Sarah (General)', status: 'completed' },
    { date: '2024-04-12', type: 'order', title: 'Comprehensive Metabolic Panel', provider: 'National Lab', status: 'ordered' },
    { date: '2024-04-14', type: 'result', title: 'CMP Results Available', provider: 'National Lab', status: 'available', flag: 'H' },
    { date: '2024-04-15', type: 'prescription', title: 'Metformin 500mg', provider: 'General Clinic', status: 'active' },
  ];

  const medicalHistory = [
    { id: 'h1', date: '2023-11-20', type: 'diagnosis', title: 'Type 2 Diabetes Mellitus', provider: 'Endocrinology Center', description: 'Confirmed with A1c 7.1. Started lifestyle management education.' },
    { id: 'h2', date: '2023-08-15', type: 'lab', title: 'Lipid Profile', provider: 'National Lab', description: 'Elevated LDL (160) and Triglycerides. BMI calculated at 26.5.' },
    { id: 'h3', date: '2023-05-10', type: 'imaging', title: 'Abdominal Ultrasound', provider: 'Duhok Medical Imaging', description: 'Negative for gallstones. Normal liver parenchymal echogenicity.' },
    { id: 'h4', date: '2024-01-05', type: 'prescription', title: 'Lisinopril 10mg', provider: 'City General Clinic', description: 'Daily morning dose for blood pressure regulation (Stage 1 Hypertension).' },
    { id: 'h5', date: '2022-09-12', type: 'diagnosis', title: 'Stage 1 Hypertension', provider: 'City General Clinic', description: 'Persistent BP readings above 140/90. Recommended sodium restriction.' },
  ];

  const filteredHistory = historyFilter === 'all' 
    ? medicalHistory 
    : medicalHistory.filter(item => item.type === historyFilter);

  const results: LabTestResult[] = [
    { id: 'r1', testName: 'Glucose (Fasting)', value: '126', unit: 'mg/dL', range: '70 - 99', flag: 'H', status: 'completed', labName: 'National Lab', labId: 'L-001' },
    { id: 'r2', testName: 'Creatinine', value: '0.9', unit: 'mg/dL', range: '0.7 - 1.3', flag: 'N', status: 'completed', labName: 'National Lab', labId: 'L-001' },
    { id: 'r3', testName: 'AST (SGOT)', value: '45', unit: 'U/L', range: '10 - 40', flag: 'H', status: 'completed', labName: 'National Lab', labId: 'L-001' },
  ];

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      if (key === 't') setActiveTab('timeline');
      if (key === 'l') setActiveTab('lab');
      if (key === 'r') setActiveTab('radiology');
      if (key === 'p') setActiveTab('prescriptions');
      if (key === 'n') setActiveTab('notes');
      if (key === 'a') setActiveTab('ai');
      if (key === 'g') setActiveTab('triage');
      if (key === 'h') setActiveTab('history');
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 min-h-screen bg-slate-50/20 pb-20">
      {/* Allergy Radar & Safety Banner */}
      <div className="bg-rose-600 p-3 flex items-center justify-between px-8 rounded-2xl shadow-lg shadow-rose-200/50 relative overflow-hidden group">
         <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
         <div className="flex items-center gap-4 relative z-10">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center text-white animate-pulse">
               <AlertCircle size={18} />
            </div>
            <div className="flex items-baseline gap-2">
               <span className="text-[10px] font-black uppercase tracking-widest text-white/60">Allergy Alert:</span>
               <span className="text-sm font-black text-white uppercase tracking-tight">Penicillin, Shellfish, Latex</span>
            </div>
         </div>
         <div className="flex items-center gap-6 relative z-10">
            <div className="flex items-center gap-2">
               <div className="w-2 h-2 rounded-full bg-emerald-400" />
               <span className="text-[10px] font-black uppercase tracking-widest text-white/80">Weight-adjusted Dosing Active</span>
            </div>
            <div className="w-px h-4 bg-white/20" />
            <button className="text-[10px] font-black uppercase tracking-widest text-white hover:underline decoration-white/30 underline-offset-4">
               View Full Risk Profile
            </button>
         </div>
      </div>

      {/* Top Decision Hub Strip */}
      <div className="bg-slate-900 rounded-[2.5rem] p-6 text-white flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl shadow-slate-200">
         <div className="flex items-center gap-6">
            <button onClick={() => navigate(-1)} className="p-3 bg-white/10 hover:bg-white/20 rounded-2xl transition-all">
              <ArrowLeft size={20} />
            </button>
            <div className="min-w-[200px]">
               {isLoading ? (
                 <div className="space-y-2">
                   <Skeleton className="h-8 w-48 bg-white/10" />
                   <Skeleton className="h-4 w-32 bg-white/5" />
                 </div>
               ) : (
                 <>
                   <div className="flex items-center gap-3">
                      <h1 className="text-2xl font-bold">{patient.name}</h1>
                      <span className="px-3 py-1 bg-white/10 rounded-full text-[10px] font-black uppercase tracking-widest">{patient.id}</span>
                      <span className="px-3 py-1 bg-indigo-500/20 text-indigo-200 border border-indigo-500/30 rounded-full text-[10px] font-black uppercase tracking-widest">
                        ID: {patient.nationalHealthId}
                      </span>
                   </div>
                   <div className="flex gap-4 mt-1 opacity-60 text-xs font-medium">
                      <span>{patient.age}y • {patient.gender}</span>
                      <span>{patient.blood} Group</span>
                   </div>
                 </>
               )}
            </div>
         </div>

         <div className="flex-1 max-w-xl hidden md:block">
            <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
               {criticalAlerts.map(alert => (
                 <div key={alert.id} className="flex items-start gap-2 mb-2 last:mb-0">
                    <AlertCircle size={14} className={alert.type === 'warning' ? 'text-amber-400' : 'text-indigo-400'} />
                    <p className="text-[10px] leading-tight font-medium">{alert.text}</p>
                 </div>
               ))}
            </div>
         </div>

         <div className="flex gap-3">
            <button 
              onClick={() => setShowAppointmentModal(true)}
              className="flex items-center gap-3 px-6 py-4 bg-white/10 hover:bg-white/20 text-white rounded-2xl font-bold text-sm transition-all shadow-xl shadow-slate-900/40"
            >
               <Calendar size={18} /> {t.scheduleAppointment}
            </button>
            <div className="bg-indigo-600 px-6 py-4 rounded-2xl text-center shadow-xl shadow-indigo-900/20">
               <span className="block text-[8px] font-bold uppercase tracking-widest opacity-60">Last Glucose</span>
               <span className="text-xl font-black">126 H</span>
            </div>
            <button className="flex items-center gap-3 px-6 py-4 bg-emerald-600 text-white rounded-2xl font-bold text-sm shadow-xl shadow-emerald-900/20 hover:scale-[1.02] active:scale-95 transition-all">
               <Zap size={18} /> Quick Order [O]
            </button>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
         {/* Left Column: Context Sidebar */}
         <div className="lg:col-span-3 space-y-6">
            <div className="bg-white p-2 rounded-[2.5rem] border border-slate-200 shadow-sm">
               <div className="flex flex-col gap-1">
                  {[
                    { id: 'synthesis', label: t.clinicalSummary, icon: Sparkles, color: 'text-indigo-600' },
                    { id: 'timeline', label: t.timeline, icon: HistoryIcon, color: 'text-slate-400' },
                    { id: 'history', label: t.medicalHistory, icon: ClipboardList, color: 'text-rose-400' },
                    { id: 'lab', label: t.labResults, icon: Beaker, color: 'text-indigo-400' },
                    { id: 'radiology', label: t.radiology, icon: Layers, color: 'text-amber-400' },
                    { id: 'prescriptions', label: t.prescriptions, icon: Pill, color: 'text-emerald-400' },
                    { id: 'notes', label: t.notes, icon: FileText, color: 'text-blue-400' },
                    { id: 'triage', label: 'AI Triage', icon: Stethoscope, color: 'text-rose-500' },
                    { id: 'ai', label: t.aiInsight, icon: BrainCircuit, color: 'text-purple-400' },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={cn(
                        "w-full flex items-center gap-4 px-6 py-4 rounded-2xl text-sm font-bold transition-all relative group",
                        activeTab === tab.id 
                          ? "bg-slate-900 text-white shadow-xl shadow-slate-200" 
                          : "text-slate-500 hover:bg-slate-50"
                      )}
                    >
                      <tab.icon size={20} className={activeTab === tab.id ? 'text-white' : tab.color} />
                      <span className="flex-1 text-left">{tab.label}</span>
                      {activeTab === tab.id && (
                        <motion.div layoutId="active-tab-indicator" className="w-1.5 h-6 bg-indigo-500 rounded-full absolute left-0" />
                      )}
                    </button>
                  ))}
               </div>
            </div>

            <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm space-y-8">
               <div>
                  <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">Clinical Overview</h3>
                  <p className="text-sm text-slate-600 leading-relaxed italic">"{patient.clinicalSummary}"</p>
               </div>

               <div className="space-y-4 pt-6 border-t border-slate-50">
                  <div className="flex justify-between items-center">
                     <span className="text-xs text-slate-400 font-medium tracking-tight">BMI</span>
                     <span className="text-sm font-bold text-slate-800">24.2</span>
                  </div>
                  <div className="flex justify-between items-center">
                     <span className="text-xs text-slate-400 font-medium tracking-tight">Vitals Latency</span>
                     <span className="text-xs font-black text-emerald-600 uppercase">Synced 4m ago</span>
                  </div>
               </div>

               <button className="w-full py-4 border-2 border-indigo-600 text-indigo-600 rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-indigo-50 transition-all">
                  Request LoA-3 Identity
               </button>
            </div>

            <div className="bg-slate-50 p-6 rounded-[2rem] space-y-4">
               <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Medical Guardians</h3>
               <div className="space-y-3">
                  {['Family Pharmacy', 'National Lab'].map(prov => (
                     <div key={prov} className="flex items-center gap-3 p-3 bg-white rounded-xl border border-slate-100">
                        <div className="w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center text-slate-400">
                           <MapPin size={16} />
                        </div>
                        <span className="text-xs font-bold text-slate-700">{prov}</span>
                     </div>
                  ))}
               </div>
            </div>
         </div>

         {/* Right Column: Decision Hub Content */}
         <div className="lg:col-span-9">
            <AnimatePresence mode="wait">
              {activeTab === 'synthesis' && (
                <motion.div
                  key="synthesis"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <ClinicalSummaryBento />
                </motion.div>
              )}
              {activeTab === 'timeline' && (
                 <motion.div 
                   key="timeline"
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   exit={{ opacity: 0, x: -20 }}
                   className="space-y-6"
                 >
                    <div className="bg-white rounded-[2.5rem] border border-slate-200 p-10 shadow-sm">
                       <h3 className="text-xl font-bold mb-10 flex items-center gap-3">
                          <HistoryIcon className="text-indigo-600" />
                          Smart Clinical Timeline
                       </h3>
                       
                       <div className="relative space-y-12">
                          <div className="absolute left-10 top-0 bottom-0 w-px bg-slate-100" />
                          {timeline.map((item, i) => (
                             <div key={i} className="relative pl-12 group flex gap-8">
                                <div className={cn(
                                   "absolute left-[34px] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full z-10 border-2 border-white",
                                   item.type === 'visit' ? 'bg-indigo-600' : 
                                   item.type === 'result' ? 'bg-emerald-600' : 'bg-slate-300'
                                )} />
                                <div className="text-right w-24 flex-shrink-0">
                                   <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{item.date.split('-')[1]} - {item.date.split('-')[2]}</p>
                                   <p className="text-xs font-bold text-slate-300">{item.date.split('-')[0]}</p>
                                </div>
                                
                                <div className="flex-1 bg-slate-50 p-6 rounded-[2rem] border border-transparent hover:border-indigo-100 hover:bg-indigo-50/20 transition-all flex items-center justify-between">
                                   <div className="flex items-center gap-6">
                                      <div className={cn(
                                         "w-12 h-12 rounded-2xl flex items-center justify-center",
                                         item.type === 'visit' ? 'bg-indigo-100 text-indigo-600' :
                                         item.type === 'result' ? 'bg-emerald-100 text-emerald-600' : 'bg-white text-slate-400'
                                      )}>
                                         {item.type === 'visit' && <Stethoscope size={24} />}
                                         {item.type === 'result' && <Beaker size={24} />}
                                         {item.type === 'order' && <FlaskConical size={24} />}
                                         {item.type === 'prescription' && <Pill size={24} />}
                                      </div>
                                      <div>
                                         <h4 className="font-bold text-slate-900">{item.title}</h4>
                                         <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{item.provider}</p>
                                      </div>
                                   </div>
                                   <div className="text-right">
                                      <span className={cn(
                                         "text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded",
                                         item.status === 'ordered' ? 'bg-amber-100 text-amber-700' :
                                         item.status === 'available' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'
                                      )}>
                                         {item.status}
                                      </span>
                                      {item.flag && <span className="ml-2 text-red-600 font-black">! {item.flag}</span>}
                                   </div>
                                </div>
                             </div>
                          ))}
                       </div>
                    </div>
                 </motion.div>
               )}

               {activeTab === 'history' && (
                 <motion.div 
                   key="history"
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   exit={{ opacity: 0, x: -20 }}
                   className="space-y-6"
                 >
                    <div className="bg-white rounded-[2.5rem] border border-slate-200 p-10 shadow-sm">
                       <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
                          <div>
                            <h3 className="text-xl font-bold flex items-center gap-3">
                               <ClipboardList className="text-rose-600" />
                               Comprehensive Medical History
                            </h3>
                            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">Found {filteredHistory.length} record(s)</p>
                          </div>
                          
                             <div className="flex flex-wrap gap-4 items-center">
                                <button className="px-4 py-2 bg-rose-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-rose-100 flex items-center gap-2 hover:scale-[1.02] active:scale-95 transition-all">
                                   <Plus size={14} /> {t.addHistoricalRecord}
                                </button>
                                <div className="relative">
                                   <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
                                <input 
                                  type="text" 
                                  placeholder="Search history..."
                                  className="pl-9 pr-4 py-2 bg-slate-50 border border-slate-100 rounded-xl text-xs focus:ring-2 focus:ring-rose-500 transition-all w-48"
                                />
                             </div>
                             
                             <div className="flex gap-1 bg-slate-50 p-1 rounded-2xl border border-slate-100">
                                {['all', 'diagnosis', 'lab', 'imaging', 'prescription'].map((filter) => (
                                   <button
                                     key={filter}
                                     onClick={() => setHistoryFilter(filter)}
                                     className={cn(
                                       "px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
                                       historyFilter === filter 
                                         ? "bg-white text-rose-600 shadow-sm" 
                                         : "text-slate-400 hover:text-slate-600"
                                     )}
                                   >
                                      {filter}
                                   </button>
                                ))}
                             </div>
                          </div>
                       </div>
                       
                       <div className="space-y-4">
                          {filteredHistory.map((item) => (
                             <div key={item.id} className="p-6 bg-slate-50 rounded-[2rem] border border-transparent hover:border-rose-100 hover:bg-rose-50/10 transition-all">
                                <div className="flex items-start justify-between mb-4">
                                   <div className="flex items-center gap-4">
                                      <div className={cn(
                                         "w-10 h-10 rounded-xl flex items-center justify-center",
                                         item.type === 'diagnosis' ? 'bg-rose-100 text-rose-600' :
                                         item.type === 'lab' ? 'bg-indigo-100 text-indigo-600' :
                                         item.type === 'imaging' ? 'bg-amber-100 text-amber-600' : 'bg-emerald-100 text-emerald-600'
                                      )}>
                                         {item.type === 'diagnosis' && <AlertCircle size={20} />}
                                         {item.type === 'lab' && <Beaker size={20} />}
                                         {item.type === 'imaging' && <Layers size={20} />}
                                         {item.type === 'prescription' && <Pill size={20} />}
                                      </div>
                                      <div>
                                         <h4 className="font-bold text-slate-900">{item.title}</h4>
                                         <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{item.provider}</p>
                                      </div>
                                   </div>
                                   <div className="text-right">
                                      <p className="text-sm font-black text-slate-900">{item.date}</p>
                                      <span className={cn(
                                         "text-[8px] font-black uppercase tracking-[0.2em] px-2 py-0.5 rounded-full mt-1 inline-block",
                                         item.type === 'diagnosis' ? 'bg-rose-100 text-rose-600' :
                                         item.type === 'lab' ? 'bg-indigo-100 text-indigo-600' :
                                         item.type === 'imaging' ? 'bg-amber-100 text-amber-600' : 'bg-emerald-100 text-emerald-600'
                                      )}>
                                         {item.type}
                                      </span>
                                   </div>
                                </div>
                                <div className="pl-14">
                                   <p className="text-xs text-slate-600 leading-relaxed bg-white/50 p-4 rounded-2xl border border-slate-200/50">
                                      {item.description}
                                   </p>
                                </div>
                             </div>
                          ))}

                          {filteredHistory.length === 0 && (
                            <div className="text-center py-20 bg-slate-50 rounded-[2rem] border border-dashed border-slate-200">
                               <Search size={48} className="text-slate-300 mx-auto mb-4" />
                               <p className="text-slate-500 font-bold">No records found for the selected filter.</p>
                            </div>
                          )}
                       </div>
                    </div>
                 </motion.div>
               )}

               {activeTab === 'lab' && (
                 <motion.div 
                   key="lab"
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   exit={{ opacity: 0, x: -20 }}
                   className="space-y-6"
                 >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-right">
                       <div className="bg-indigo-600 rounded-[2rem] p-8 text-white shadow-xl shadow-indigo-100 cursor-pointer hover:bg-indigo-700 transition-all" onClick={() => setShowTrendModal(true)}>
                          <h4 className="text-sm font-bold flex items-center gap-2 mb-6 rtl:flex-row-reverse">
                             <TrendingUp size={16} fill="currentColor" /> Longitudinal View [L]
                          </h4>
                          <div className="flex items-end gap-2 h-32 flex-row-reverse">
                             {[40, 70, 45, 90, 65, 80, 50].map((h, i) => (
                                <div key={i} className="flex-1 bg-white/20 rounded-lg hover:bg-white/40 transition-all cursor-pointer" style={{ height: `${h}%` }} />
                             ))}
                          </div>
                          <p className="mt-6 text-[10px] font-bold uppercase tracking-widest text-indigo-200">Comparing last 7 Blood Panels</p>
                       </div>

                       <div className="bg-white rounded-[2rem] border border-slate-200 p-8 shadow-sm">
                          <h4 className="text-sm font-bold text-slate-900 mb-6 flex items-center justify-between">
                             <span className="text-[10px] font-bold text-red-600 px-2 py-1 bg-red-50 rounded">2 Critical</span>
                             Clinical Alerts
                          </h4>
                          <div className="space-y-4">
                             <div className="flex gap-4 p-4 bg-red-50 rounded-2xl border border-red-100 flex-row-reverse">
                                <AlertCircle className="text-red-600" size={20} />
                                <p className="text-xs text-red-900 font-medium leading-relaxed">AST/ALT levels trending upward. Rule out drug-induced liver injury (DILI).</p>
                             </div>
                          </div>
                       </div>
                    </div>

                    <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden">
                       <div className="p-8 border-b border-slate-100 flex items-center justify-between">
                          <h3 className="font-bold text-slate-900">Lab Reports - Production Mode</h3>
                          <div className="flex gap-2">
                             <button className="flex items-center gap-2 px-6 py-2 border-2 border-indigo-600 text-indigo-600 rounded-xl font-bold text-xs uppercase hover:bg-indigo-50 transition-all">
                                <Share2 size={14} /> Shared with Center B
                             </button>
                             <button className="p-2 border border-slate-200 rounded-xl hover:border-indigo-600 hover:text-indigo-600 transition-all">
                                <Download size={20} />
                             </button>
                          </div>
                       </div>
                       <table className="w-full text-right">
                          <thead className="bg-slate-50 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
                             <tr>
                                <th className="px-8 py-5">{t.testName}</th>
                                <th className="px-8 py-5">{t.result}</th>
                                <th className="px-8 py-5">Unit</th>
                                <th className="px-8 py-5">{t.range}</th>
                                <th className="px-8 py-5 text-left">{t.status}</th>
                             </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                             {results.map((res) => (
                                <tr key={res.id} className="hover:bg-slate-50 transition-colors group">
                                   <td className="px-8 py-6">
                                      <div className="flex items-center gap-3 justify-end">
                                         <div className={cn(
                                            "w-2 h-2 rounded-full",
                                            res.flag === 'H' ? 'bg-red-500' : 'bg-emerald-500'
                                         )} />
                                         <span className="font-bold text-slate-900">{res.testName}</span>
                                      </div>
                                   </td>
                                   <td className={cn(
                                      "px-8 py-6 font-black text-lg",
                                      res.flag === 'H' ? 'text-red-600' : 'text-slate-900'
                                   )}>{res.value}</td>
                                   <td className="px-8 py-6 text-xs text-slate-400 font-bold">{res.unit}</td>
                                   <td className="px-8 py-6 text-sm text-slate-600 font-medium tracking-tight">{res.range}</td>
                                   <td className="px-8 py-6 text-left">
                                      {res.flag === 'H' && <span className="px-3 py-1 bg-red-100 text-red-700 text-[10px] font-black uppercase rounded">Abnormal High</span>}
                                      {res.flag === 'N' && <span className="px-3 py-1 bg-slate-100 text-slate-500 text-[10px] font-black uppercase rounded">Normal</span>}
                                   </td>
                                </tr>
                             ))}
                          </tbody>
                       </table>
                    </div>
                 </motion.div>
               )}

               {activeTab === 'radiology' && (
                 <motion.div 
                   key="radiology"
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   exit={{ opacity: 0, x: -20 }}
                   className="space-y-6"
                 >
                    <div className="bg-white rounded-[2.5rem] border border-slate-200 p-10 shadow-sm">
                       <h3 className="text-xl font-bold mb-10 flex items-center gap-3">
                          <Layers className="text-amber-600" />
                          Diagnostic Imaging (Radiology)
                       </h3>
                       <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {[
                            { name: 'Abdominal CT Scan', date: '2024-04-10', status: 'Finalized', result: 'Mild splenomegaly noted.' },
                            { name: 'Chest X-Ray', date: '2024-03-15', status: 'Finalized', result: 'Clear lung fields.' }
                          ].map((scan, i) => (
                             <div key={i} className="p-6 bg-slate-50 rounded-3xl border border-slate-100 hover:border-amber-200 transition-all cursor-pointer">
                                <div className="flex justify-between items-start mb-4">
                                   <div className="w-12 h-12 bg-amber-100 rounded-2xl flex items-center justify-center text-amber-600">
                                      <Layers size={24} />
                                   </div>
                                   <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-50 px-2 py-1 rounded">{scan.status}</span>
                                </div>
                                <h4 className="font-black text-slate-900 mb-1">{scan.name}</h4>
                                <p className="text-[10px] text-slate-400 font-bold uppercase mb-4">{scan.date}</p>
                                <p className="text-xs text-slate-600 leading-relaxed bg-white p-4 rounded-xl border border-slate-200/50 italic">"{scan.result}"</p>
                             </div>
                          ))}
                       </div>
                    </div>
                 </motion.div>
               )}

               {activeTab === 'prescriptions' && (
                 <motion.div 
                   key="prescriptions"
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   exit={{ opacity: 0, x: -20 }}
                   className="space-y-8"
                 >
                    <PrescriptionBuilder />
                    <div className="bg-white rounded-[2.5rem] border border-slate-200 p-10 shadow-sm">
                       <div className="flex items-center justify-between mb-10">
                          <h3 className="text-xl font-bold flex items-center gap-3">
                             <HistoryIcon className="text-emerald-600" />
                             Clinical Audit Trail
                          </h3>
                       </div>
                       <table className="w-full text-right">
                          <thead className="bg-slate-50 text-[10px] font-black uppercase tracking-widest text-slate-400">
                             <tr>
                                <th className="px-8 py-4">Medication</th>
                                <th className="px-8 py-4">Dosage</th>
                                <th className="px-8 py-4">Frequency</th>
                                <th className="px-8 py-4">Status</th>
                             </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                             {[
                               { name: 'Metformin', dose: '500mg', freq: 'BID (with meals)', status: 'Active' },
                               { name: 'Lisinopril', dose: '10mg', freq: 'QD (morning)', status: 'Active' }
                             ].map((med, i) => (
                                <tr key={i} className="hover:bg-slate-50 transition-colors">
                                   <td className="px-8 py-6 font-bold text-slate-900">{med.name}</td>
                                   <td className="px-8 py-6 text-sm text-slate-600">{med.dose}</td>
                                   <td className="px-8 py-6 text-xs text-slate-400 font-medium">{med.freq}</td>
                                   <td className="px-8 py-6 text-left">
                                      <span className="px-3 py-1 bg-emerald-100 text-emerald-700 text-[10px] font-black uppercase rounded">Active</span>
                                   </td>
                                </tr>
                             ))}
                          </tbody>
                       </table>
                    </div>
                 </motion.div>
               )}

               {activeTab === 'notes' && (
                 <motion.div 
                   key="notes"
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   exit={{ opacity: 0, x: -20 }}
                   className="space-y-8"
                 >
                    <ClinicalNotes />
                    <div className="bg-white rounded-[2.5rem] border border-slate-200 p-10 shadow-sm">
                       <h3 className="text-xl font-bold mb-10 flex items-center gap-3">
                          <HistoryIcon className="text-blue-600" />
                          Previous Progress Notes
                       </h3>
                       <div className="space-y-6">
                          <div className="p-8 bg-slate-50 rounded-[2rem] border border-slate-100 italic">
                             <div className="flex items-center gap-2 mb-4">
                                <Stethoscope size={16} className="text-slate-400" />
                                <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest underline decoration-indigo-200">2024-04-12 • Initial Intake Note</span>
                             </div>
                             <p className="text-sm text-slate-700 leading-relaxed">
                                Patient presents with episodic epigastric pain, non-radiating. Correlated with dietary intake. 
                                Rule out peptic ulcer disease vs gallbladder pathology. Initiated Metformin for metabolic stabilization.
                             </p>
                          </div>
                       </div>
                    </div>
                 </motion.div>
               )}

               {activeTab === 'triage' && (
                <motion.div
                  key="triage"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <AITriageAssistant 
                    patientId={patient.id} 
                    patientData={JSON.stringify(patient) + " " + JSON.stringify(medicalHistory)} 
                  />
                </motion.div>
              )}
               {activeTab === 'ai' && (
                 <motion.div 
                   key="ai"
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   exit={{ opacity: 0, x: -20 }}
                   className="space-y-8"
                 >
                    <div className="bg-indigo-900 rounded-[2.5rem] p-10 text-white relative overflow-hidden shadow-2xl shadow-indigo-200">
                       <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/20 blur-[100px] rounded-full -mr-20 -mt-20" />
                       <h3 className="text-xl font-bold mb-8 flex items-center gap-3">
                          <BrainCircuit className="text-indigo-400" />
                          GULA AI Diagnostic Assistant
                       </h3>
                                           <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
                          <div className="space-y-6 text-right">
                             <div className="bg-white/5 border border-white/10 rounded-3xl p-6 hover:bg-white/10 transition-all group">
                                <div className="flex items-center justify-between mb-6 flex-row-reverse">
                                   <h4 className="text-xs font-black uppercase tracking-widest text-indigo-400">Biological Risk Map</h4>
                                   <div className="p-2 bg-indigo-500/20 rounded-lg text-indigo-400 group-hover:scale-110 transition-transform">
                                      <Zap size={16} />
                                   </div>
                                </div>
                                <div className="space-y-5">
                                   {[
                                      { label: "Cardiovascular Event", value: 8, color: "bg-emerald-400", alert: false },
                                      { label: "Metabolic Complexity", value: 64, color: "bg-red-400", alert: true },
                                      { label: "Renal Filtration Decay", value: 12, color: "bg-emerald-400", alert: false },
                                      { label: "Chronic Inflammation", value: 45, color: "bg-amber-400", alert: false }
                                   ].map(risk => (
                                      <div key={risk.label} className="space-y-2">
                                         <div className="flex justify-between items-center flex-row-reverse text-xs font-bold text-slate-300">
                                            <span>{risk.label}</span>
                                            <span className={cn(risk.alert ? "text-red-400 animate-pulse" : "text-indigo-100")}>{risk.value}%</span>
                                         </div>
                                         <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                                            <motion.div 
                                              initial={{ width: 0 }}
                                              animate={{ width: `${risk.value}%` }}
                                              className={cn("h-full", risk.color)} 
                                            />
                                         </div>
                                      </div>
                                   ))}
                                </div>
                             </div>
                          </div>

                          <div className="space-y-6">
                             <div className="bg-white/5 border border-white/10 rounded-3xl p-6 text-right">
                                <h4 className="text-xs font-black uppercase tracking-widest text-indigo-400 mb-4">Neural Suggestion Engine</h4>
                                <div className="space-y-4">
                                   {[
                                     { type: 'diagnostic', text: 'Upper GI Endoscopy (EGD) due to localized pain pattern.' },
                                     { type: 'imaging', text: 'Liver Ultrasound to assess echogenicity.' },
                                     { type: 'lab', text: 'H. Pylori Stool Antigen test.' }
                                   ].map((step, i) => (
                                     <div key={i} className="flex gap-4 p-3 bg-white/5 rounded-2xl border border-white/5 hover:border-indigo-500/30 transition-all justify-end group">
                                        <div className="flex-1">
                                           <div className="flex items-center gap-2 justify-end mb-1">
                                              <span className="text-[8px] font-black uppercase text-indigo-400 opacity-60 tracking-widest">{step.type}</span>
                                           </div>
                                           <p className="text-xs text-indigo-50 leading-relaxed">{step.text}</p>
                                        </div>
                                        <div className="w-8 h-8 bg-indigo-500/20 text-indigo-400 rounded-xl flex items-center justify-center font-black group-hover:bg-indigo-600 group-hover:text-white transition-all">{i+1}</div>
                                     </div>
                                   ))}
                                </div>
                             </div>
                             <button className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl shadow-indigo-900/40 transition-all flex items-center justify-center gap-3">
                                <ActivityIcon size={16} /> Run Full Neural Scan
                             </button>
                          </div>
                       </div>
                    </div>
                 </motion.div>
               )}
            </AnimatePresence>
         </div>
      </div>

      {/* Modals Region */}
      <AnimatePresence>
        {showAppointmentModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowAppointmentModal(false)}
              className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative bg-white w-full max-w-xl rounded-[2.5rem] shadow-2xl p-10 overflow-hidden"
            >
               <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
                  <Calendar size={180} />
               </div>
               <h3 className="text-2xl font-black text-slate-900 mb-6 flex items-center gap-3">
                  <Calendar className="text-indigo-600" />
                  {t.scheduleAppointment}
               </h3>
               
               <div className="space-y-6 relative z-10">
                  <div className="grid grid-cols-2 gap-4">
                     {['Standard Follow-up', 'Urgent Consult', 'Lab Review', 'Specialist Referral'].map((type) => (
                        <button key={type} className="p-4 border border-slate-200 rounded-2xl text-sm font-bold text-slate-600 hover:border-indigo-600 hover:text-indigo-600 hover:bg-indigo-50 transition-all text-left">
                           {type}
                        </button>
                     ))}
                  </div>
                  
                  <div className="space-y-2">
                     <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Available Slots (Today)</p>
                     <div className="grid grid-cols-3 gap-3">
                        {['14:00', '14:30', '15:45', '16:15', '17:00'].map(slot => (
                           <button key={slot} className="py-3 bg-slate-50 hover:bg-indigo-600 hover:text-white rounded-xl text-sm font-bold transition-all">
                              {slot}
                           </button>
                        ))}
                     </div>
                  </div>

                  <button 
                    onClick={() => setShowAppointmentModal(false)}
                    className="w-full py-5 bg-indigo-600 text-white rounded-2xl font-bold flex items-center justify-center gap-3 shadow-xl shadow-indigo-100 hover:scale-[1.02] active:scale-95 transition-all"
                  >
                     Confirm Appointment <CheckCircle2 size={20} />
                  </button>
               </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showTrendModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowTrendModal(false)}
              className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative bg-white w-full max-w-4xl rounded-[2.5rem] shadow-2xl p-10 overflow-hidden"
            >
               <div className="flex items-center justify-between mb-10">
                  <h3 className="text-2xl font-black text-slate-900 flex items-center gap-3">
                     <TrendingUp className="text-indigo-600" />
                     {t.historicalTrends} Analysis
                  </h3>
                  <button onClick={() => setShowTrendModal(false)} className="p-3 bg-slate-100 hover:bg-slate-200 rounded-2xl transition-all">
                      <ChevronRight className="rotate-90 md:rotate-0" size={20} />
                  </button>
               </div>

               <div className="grid grid-cols-1 md:grid-cols-12 gap-10 text-right">
                  <div className="md:col-span-8 space-y-8">
                     <div className="h-64 bg-slate-50 rounded-3xl border border-slate-100 p-8 flex items-end gap-3 flex-row-reverse">
                        {[20, 35, 25, 45, 40, 60, 55, 75, 70, 90].map((h, i) => (
                           <motion.div 
                              key={i} 
                              initial={{ height: 0 }}
                              animate={{ height: `${h}%` }}
                              className="flex-1 bg-indigo-500 rounded-t-lg relative group"
                           >
                              <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                                 Value: {h}
                              </div>
                           </motion.div>
                        ))}
                     </div>
                     <div className="flex justify-between text-[10px] font-black text-slate-400 uppercase tracking-widest px-2 flex-row-reverse">
                        <span>Current</span>
                        <span>Mar 2024</span>
                        <span>Feb 2024</span>
                        <span>Jan 2024</span>
                     </div>
                  </div>
                  <div className="md:col-span-4 space-y-6">
                     <div className="p-6 bg-indigo-50 rounded-3xl border border-indigo-100">
                        <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-2">Statistical Delta</p>
                        <p className="text-2xl font-black text-indigo-900">+12.4% Increase</p>
                        <p className="text-xs text-indigo-600 mt-2 font-medium">Trending above historical baseline by 4.2 units.</p>
                     </div>
                     <button className="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold flex items-center justify-center gap-3 shadow-lg shadow-slate-200">
                        <Download size={18} /> Export CSV Loop
                     </button>
                  </div>
               </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
