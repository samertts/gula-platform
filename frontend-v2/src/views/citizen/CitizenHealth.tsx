import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  ShieldCheck, Heart, FileText, QrCode, 
  Activity as ActivityIcon, History as HistoryIcon, FlaskConical,
  BrainCircuit, TrendingUp, AlertCircle, ChevronRight,
  Stethoscope, Beaker, Pill, Calendar, ArrowUpRight,
  Download, Share2, Bell, CheckCircle2,
  Clock, MapPin, Zap, Info, Filter,
  Fingerprint, ScanFace, ShieldEllipsis, X, Smartphone,
  Sparkles, Loader2, Users
} from 'lucide-react';
import { NationalIDCard } from '../../components/citizen/NationalIDCard';
import { DigitalTwin } from '../../components/citizen/DigitalTwin';
import { DigitalTwinSimulation } from '../../components/DigitalTwinSimulation';
import { QuantumHealthGrid } from '../../components/QuantumHealthGrid';
import { FamilySwitcher } from '../../components/citizen/FamilySwitcher';
import { MedicineCabinet } from '../../components/citizen/MedicineCabinet';
import { SymptomChecker } from '../../components/citizen/SymptomChecker';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';
import { HealthInsight, LabTestResult, MedicalHistoryItem } from '../../types/domain';
import { HealthTrendChart } from '../../components/HealthTrendChart';
import { analyzeLabTrends } from '../../services/aiService';
import Markdown from 'react-markdown';
import { toast } from 'sonner';

export function CitizenHealth() {
  const { t } = useLanguage();
  const [activeSegment, setActiveSegment] = useState<'overview' | 'results' | 'timeline' | 'family' | 'security' | 'triage'>('overview');
  const [explainingResult, setExplainingResult] = useState<LabTestResult | null>(null);
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [isExplaining, setIsExplaining] = useState(false);
  const [showScoreBreakdown, setShowScoreBreakdown] = useState(false);
  const [isBiometricActive, setIsBiometricActive] = useState(false);
  const [showBiometricModal, setShowBiometricModal] = useState(false);
  const [biometricType, setBiometricType] = useState<'fingerprint' | 'face' | null>(null);

  const healthScore = 82; // Composite Score

  useEffect(() => {
    async function getExplanation() {
      if (!explainingResult) {
        setAiExplanation(null);
        return;
      }
      
      setIsExplaining(true);
      try {
        const result = await analyzeLabTrends([explainingResult]);
        setAiExplanation(result);
      } catch (error) {
        setAiExplanation("AI analysis temporarily unavailable. Direct consultation with your pathology lead is recommended.");
      } finally {
        setIsExplaining(false);
      }
    }
    getExplanation();
  }, [explainingResult]);

  const glucoseData = [
    { time: '08:00', value: 92 },
    { time: '10:00', value: 95 },
    { time: '12:00', value: 110 },
    { time: '14:00', value: 105 },
    { time: '16:00', value: 98 },
    { time: '18:00', value: 92 },
  ];

  const hrData = [
    { time: '08:00', value: 65 },
    { time: '10:00', value: 72 },
    { time: '12:00', value: 85 },
    { time: '14:00', value: 78 },
    { time: '16:00', value: 70 },
    { time: '18:00', value: 68 },
  ];

  const criticalAlerts = [
    { 
      id: 'a1', 
      title: 'Action Required: Fasting Blood Sugar', 
      description: 'Your last result (126 mg/dL) is in the pre-diabetic range.', 
      type: 'critical',
      actions: [
        { label: t.bookNow, primary: true },
        { label: t.retest, primary: false }
      ]
    }
  ];

  const nextActions = [
    { title: 'Red Blood Cell Count', provider: 'National Lab', date: 'In 3 Days', type: 'test', status: 'Pending Prep' },
    { title: 'Metformin 500mg', provider: 'Pharmacy', date: 'Every 12h', type: 'medication', status: 'Take Now' },
    { title: 'Follow-up with Dr. Sarah', provider: 'General Clinic', date: 'Next Tuesday', type: 'appointment', status: 'Confirmed' },
  ];

  const scoreBreakdown = [
    { label: t.metabolicRank, status: 'optimal', score: 91, icon: 'Zap' },
    { label: t.cellularStability, status: 'warning', score: 68, icon: 'Activity' },
    { label: t.cognitiveFidelity, status: 'optimal', score: 94, icon: 'BrainCircuit' },
    { label: t.inflammatoryIndex, status: 'optimal', score: 85, icon: 'Shield' },
  ];

  const recentResults: LabTestResult[] = [
    {
      id: 'r1',
      testName: 'Hemoglobin A1c',
      value: '5.4',
      unit: '%',
      range: '4.0 - 5.6',
      flag: 'N',
      status: 'completed',
      labId: 'l1',
      labName: 'Central Diagnostic',
      trend: [{ date: 'Jan', value: 5.6 }, { date: 'Feb', value: 5.5 }, { date: 'Mar', value: 5.4 }]
    },
    {
      id: 'r2',
      testName: 'Vitamin D (25-OH)',
      value: '22',
      unit: 'ng/mL',
      range: '30 - 100',
      flag: 'L',
      status: 'completed',
      labId: 'l1',
      labName: 'Central Diagnostic'
    }
  ];

  const history: MedicalHistoryItem[] = [
    { id: 'h1', patientId: 'p1', date: '2024-03-10', type: 'diagnosis', title: 'Seasonal Allergy', description: 'Mild rhinitis observed. Prescribed antihistamines.', provider: 'Dr. Sarah Smith' },
    { id: 'h2', patientId: 'p1', date: '2023-11-22', type: 'imaging', title: 'Routine Chest X-Ray', description: 'Clear lung fields. No abnormalities.', provider: 'Radiology Dept' }
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 min-h-screen bg-slate-50/30">
      {/* Top Layer: Priority Notification Bar (Action Engine) */}
      <AnimatePresence>
        {criticalAlerts.length > 0 && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            className="overflow-hidden"
          >
            {criticalAlerts.map(alert => (
              <div key={alert.id} className="bg-red-600 text-white p-6 rounded-[2rem] flex flex-col md:flex-row items-center justify-between shadow-2xl shadow-red-200 mb-6 border-b-4 border-red-700">
                <div className="flex items-center gap-4 mb-4 md:mb-0">
                  <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center animate-pulse shrink-0">
                    <AlertCircle size={28} />
                  </div>
                  <div>
                    <h3 className="font-black text-lg tracking-tight flex items-center gap-2">
                       {t.actionRequired}: {alert.title}
                       <span className="px-2 py-0.5 bg-white/20 rounded text-[9px] font-black uppercase">Stat</span>
                    </h3>
                    <p className="text-sm text-red-100 opacity-90">{alert.description}</p>
                  </div>
                </div>
                <div className="flex gap-3 w-full md:w-auto">
                   {alert.actions?.map((action, idx) => (
                     <button 
                        key={idx}
                        className={cn(
                          "flex-1 md:flex-none px-6 py-3 rounded-xl font-black text-xs uppercase tracking-widest transition-all",
                          action.primary 
                            ? "bg-white text-red-600 shadow-lg shadow-red-900/20 hover:scale-[1.02]" 
                            : "bg-red-700 text-white border border-red-500/50 hover:bg-red-800"
                        )}
                      >
                        {action.label}
                      </button>
                   ))}
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header & Health Score Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Security Posture Widget */}
            <div className="bg-slate-900 text-white p-8 rounded-[2.5rem] relative overflow-hidden group">
               <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:rotate-12 transition-transform">
                  <ShieldCheck size={120} />
               </div>
               <div className="relative z-10 space-y-6">
                  <div className="flex items-center gap-3">
                     <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-xl">
                        <ShieldCheck size={24} />
                     </div>
                     <div>
                        <h3 className="font-bold text-lg leading-tight uppercase tracking-widest">Security Posture</h3>
                        <p className="text-[10px] text-emerald-400 font-black tracking-widest">Encrypted & Verified</p>
                     </div>
                  </div>
                  <div className="space-y-3">
                     <div className="flex justify-between text-xs font-bold text-slate-400">
                        <span>Identity Assurance</span>
                        <span className="text-emerald-400">100%</span>
                     </div>
                     <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                        <div className="w-full h-full bg-emerald-500" />
                     </div>
                  </div>
                  <button 
                    onClick={() => setActiveSegment('security')}
                    className="w-full py-3 bg-white/5 text-xs font-black uppercase tracking-widest rounded-xl hover:bg-white/10 transition-all border border-white/10"
                  >
                     Manage Biometrics
                  </button>
               </div>
            </div>

           {/* Health Summary Widget */}
           <div className="bg-indigo-600 text-white p-8 rounded-[2.5rem] relative overflow-hidden group">
              <div className="absolute bottom-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform">
                 <BrainCircuit size={120} />
              </div>
              <div className="relative z-10 space-y-6">
                 <div className="flex items-center gap-3">
                    <div className="p-2 bg-white/20 rounded-xl">
                       <BrainCircuit size={24} />
                    </div>
                    <h3 className="font-bold text-lg leading-tight uppercase tracking-widest">AI Insights</h3>
                 </div>
                 <p className="text-sm font-medium text-indigo-100 leading-relaxed italic">
                    "Your metabolic markers show a 12% positive trend since last panel."
                 </p>
                 <div className="flex gap-2">
                    <div className="px-3 py-1 bg-white/10 rounded-lg text-[9px] font-black uppercase">Wellness: Optimal</div>
                    <div className="px-3 py-1 bg-white/10 rounded-lg text-[9px] font-black uppercase">Next: CBC March</div>
                 </div>
              </div>
           </div>

           {/* Quick Actions Widget */}
           <div className="bg-white border border-slate-200 p-8 rounded-[2.5rem] relative group">
              <div className="flex flex-col h-full justify-between gap-6">
                 <div>
                    <h3 className="font-bold text-lg text-slate-900 leading-tight uppercase tracking-widest mb-2">Quick Actions</h3>
                    <p className="text-xs text-slate-400 font-medium tracking-tight">Rapid access to decentralized tools.</p>
                 </div>
                 <div className="grid grid-cols-2 gap-3">
                    <button 
                      onClick={() => setActiveSegment('triage')}
                      className="col-span-2 flex items-center gap-4 p-4 bg-indigo-600 text-white rounded-2xl hover:bg-slate-900 transition-all shadow-lg group"
                    >
                       <Stethoscope size={20} />
                       <div className="text-left">
                          <span className="text-[10px] font-black uppercase block tracking-widest opacity-60">AI Triage</span>
                          <span className="text-xs font-bold">{t.checkSymptoms}</span>
                       </div>
                       <ChevronRight size={16} className="ml-auto group-hover:translate-x-1 transition-transform" />
                    </button>
                    <button className="flex flex-col items-center gap-2 p-4 bg-slate-50 rounded-2xl hover:bg-indigo-50 hover:text-indigo-600 transition-all">
                       <Download size={20} />
                       <span className="text-[10px] font-black uppercase">Export</span>
                    </button>
                    <button className="flex flex-col items-center gap-2 p-4 bg-slate-50 rounded-2xl hover:bg-indigo-50 hover:text-indigo-600 transition-all">
                       <Share2 size={20} />
                       <span className="text-[10px] font-black uppercase">Share</span>
                    </button>
                 </div>
              </div>
           </div>
        </div>

        <div className="lg:col-span-8 flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white p-8 rounded-[2.5rem] border border-slate-200/60 shadow-sm relative overflow-hidden group">
           <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none transition-transform group-hover:scale-110">
              <Heart size={160} fill="currentColor" className="text-red-500" />
           </div>
           
           <div className="relative z-10 flex items-center gap-6">
              <div 
                className="relative group cursor-pointer"
                onMouseEnter={() => setShowScoreBreakdown(true)}
                onMouseLeave={() => setShowScoreBreakdown(false)}
                onClick={() => setShowScoreBreakdown(!showScoreBreakdown)}
              >
                <div className="absolute inset-0 bg-indigo-500/5 rounded-full animate-pulse group-hover:bg-indigo-500/10 transition-all blur-xl" />
                
                <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 128 128">
                   <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-slate-100" />
                   <motion.circle 
                     cx="64" cy="64" r="58" 
                     stroke="url(#health-gradient)" 
                     strokeWidth="8" fill="transparent" 
                     initial={{ strokeDashoffset: 364 }}
                     animate={{ strokeDashoffset: 364 - (364 * healthScore) / 100 }} 
                     strokeDasharray={364}
                     className="transition-all duration-1000 ease-out" 
                     strokeLinecap="round" 
                   />
                   
                   {/* Triple Ring System */}
                   <circle cx="64" cy="64" r="46" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-slate-50" />
                   <motion.circle 
                     cx="64" cy="64" r="46" 
                     stroke="#10b981" 
                     strokeWidth="4" fill="transparent" 
                     initial={{ strokeDashoffset: 289 }}
                     animate={{ strokeDashoffset: 289 - (289 * (scoreBreakdown[0]?.score || 0)) / 100 }}
                     strokeDasharray={289}
                     strokeLinecap="round" 
                   />
                   
                   <circle cx="64" cy="64" r="36" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-slate-50" />
                   <motion.circle 
                     cx="64" cy="64" r="36" 
                     stroke="#8b5cf6" 
                     strokeWidth="4" fill="transparent" 
                     initial={{ strokeDashoffset: 226 }}
                     animate={{ strokeDashoffset: 226 - (226 * (scoreBreakdown[2]?.score || 0)) / 100 }}
                     strokeDasharray={226}
                     strokeLinecap="round" 
                   />

                   <defs>
                      <linearGradient id="health-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                         <stop offset="0%" stopColor="#4f46e5" />
                         <stop offset="100%" stopColor="#818cf8" />
                      </linearGradient>
                   </defs>
                 </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-black text-slate-900 leading-none">{healthScore}</span>
                  <span className="text-[8px] font-bold text-slate-400 uppercase">Score</span>
                </div>

                {/* Score Breakdown Tooltip */}
                <AnimatePresence>
                  {showScoreBreakdown && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      className="absolute top-full mt-4 left-0 w-72 bg-slate-900 text-white rounded-[2rem] p-6 shadow-2xl z-50 pointer-events-none border border-white/5 backdrop-blur-xl"
                    >
                       <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-3">
                          <h4 className="text-[10px] font-black uppercase tracking-widest text-indigo-400">{t.scoreMetrics}</h4>
                          <Info size={12} className="text-slate-500" />
                       </div>
                       <div className="space-y-5">
                          {scoreBreakdown.map((item, idx) => (
                            <div key={idx} className="space-y-2">
                               <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-wider">
                                  <div className="flex items-center gap-2">
                                     <div className={cn(
                                       "p-1 rounded-md",
                                       item.status === 'optimal' ? "bg-emerald-500/20 text-emerald-400" : "bg-amber-500/20 text-amber-400"
                                     )}>
                                        {item.icon === 'Zap' && <Zap size={10} />}
                                        {item.icon === 'Activity' && <ActivityIcon size={10} />}
                                        {item.icon === 'BrainCircuit' && <BrainCircuit size={10} />}
                                        {item.icon === 'Shield' && <ShieldCheck size={10} />}
                                     </div>
                                     <span className="text-slate-300">{item.label}</span>
                                  </div>
                                  <span className={item.status === 'optimal' ? 'text-emerald-400 font-mono text-xs' : 'text-amber-400 font-mono text-xs'}>{item.score}%</span>
                               </div>
                               <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                                  <motion.div 
                                    initial={{ width: 0 }}
                                    animate={{ width: `${item.score}%` }}
                                    transition={{ duration: 1, delay: idx * 0.1 }}
                                    className={cn("h-full", item.status === 'optimal' ? 'bg-emerald-500' : 'bg-amber-500')} 
                                  />
                               </div>
                               <div className="flex justify-between text-[8px] font-bold text-slate-500 tracking-tighter">
                                  <span>{item.status === 'optimal' ? t.optimized : t.attention}</span>
                                  <span>{t.level}: {item.score > 90 ? t.elite : t.normalLevel}</span>
                                </div>
                            </div>
                          ))}
                       </div>
                       <div className="mt-6 pt-4 border-t border-white/5">
                          <div className="flex items-center gap-2 group/btn">
                             <p className="text-[9px] font-bold text-slate-400 italic">{t.aiDiagnosticClick}</p>
                             <div className="ml-auto w-5 h-5 bg-indigo-500 rounded-lg flex items-center justify-center">
                                <ArrowUpRight size={10} />
                             </div>
                          </div>
                       </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900 tracking-tight">{t.welcomeBack}, Samer</h1>
                <div className="flex items-center gap-2 mt-1">
                   <ShieldCheck className="w-4 h-4 text-emerald-500" />
                   <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">{t.identVerification} – Level 3 Authorized</span>
                </div>
              </div>
           </div>

           <div className="relative z-10 flex gap-3">
              <FamilySwitcher />
              <button className="flex items-center gap-2 px-6 py-4 bg-slate-900 text-white border-b-4 border-slate-950 rounded-2xl font-bold text-sm shadow-xl shadow-slate-200 hover:scale-[1.02] transition-all active:translate-y-1 active:border-b-0">
                <QrCode size={20} /> MY HEALTH ID
              </button>
              <button className="p-4 bg-white border border-slate-200 rounded-2xl hover:border-indigo-600 transition-all group">
                <Bell size={24} className="text-slate-400 group-hover:text-indigo-600" />
              </button>
           </div>
        </div>

        <div className="lg:col-span-4 self-stretch flex flex-col">
           <div className="bg-indigo-600 p-8 rounded-[2.5rem] text-white shadow-2xl shadow-indigo-100 flex-1 relative overflow-hidden group border-b-4 border-indigo-800">
              <div className="absolute bottom-0 right-0 translate-x-1/4 translate-y-1/4 opacity-10 group-hover:scale-110 transition-transform">
                 <Zap size={140} />
              </div>
              <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                 <Zap size={18} className="text-amber-400 fill-amber-400" /> {t.nextActions}
              </h3>
              <div className="space-y-4">
                 {nextActions.map((action, i) => (
                   <div key={i} className="bg-white/10 border border-white/10 rounded-2xl p-4 flex items-center justify-between backdrop-blur-md hover:bg-white/20 transition-all cursor-pointer group/action">
                      <div>
                         <p className="font-bold text-sm flex items-center gap-2">
                            {action.title}
                            {action.type === 'medication' && <Pill size={12} className="text-emerald-400" />}
                         </p>
                         <p className="text-[10px] text-indigo-200">{action.provider}</p>
                      </div>
                      <div className="text-right">
                         <span className={cn(
                           "px-2 py-0.5 rounded text-[8px] font-black uppercase mb-1 block w-fit ml-auto",
                           action.status === 'Take Now' ? "bg-red-500 text-white" : "bg-white/20 text-indigo-100"
                         )}>
                            {action.status}
                         </span>
                         <div className="flex items-center gap-2 text-xs font-black">
                            {action.date}
                            <ChevronRight size={14} className="group-hover/action:translate-x-1 transition-transform" />
                         </div>
                      </div>
                   </div>
                 ))}
              </div>
           </div>
        </div>
      </div>

      {/* Decision Layers Navigation */}
      <div className="flex bg-white/60 backdrop-blur-lg p-1.5 rounded-3xl w-fit border border-slate-200/60 shadow-sm mx-auto sticky top-24 z-30">
        {(['overview', 'triage', 'results', 'timeline', 'family', 'security'] as const).map((seg) => (
          <button
            key={seg}
            onClick={() => setActiveSegment(seg)}
            className={cn(
              "px-10 py-3 rounded-2xl text-xs font-bold uppercase tracking-widest transition-all relative",
              activeSegment === seg ? "bg-white text-indigo-600 shadow-xl border border-slate-100" : "text-slate-400 hover:text-slate-700"
            )}
          >
            {seg === 'triage' ? t.symptomChecker : seg}
            {activeSegment === seg && (
              <motion.div layoutId="activeSeg" className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-1 h-1 bg-indigo-600 rounded-full" />
            )}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {activeSegment === 'overview' && (
          <motion.div 
            key="overview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 lg:grid-cols-12 gap-8"
          >
             <div className="lg:col-span-12">
                <MedicineCabinet />
             </div>
             <div className="lg:col-span-12">
                <DigitalTwinSimulation />
             </div>
             <div className="lg:col-span-12">
                <QuantumHealthGrid />
             </div>
             {/* Vital Trends Hub */}
             <div className="lg:col-span-8 space-y-6">
                <div className="bg-white rounded-[2.5rem] border border-slate-200 p-8 shadow-sm">
                   <div className="flex items-center justify-between mb-8">
                      <h3 className="text-xl font-bold text-slate-900 tracking-tight">{t.vitalSigns}</h3>
                      <div className="flex gap-2">
                         <button className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-500 hover:border-indigo-600 transition-all"><Filter size={14} /> Filter</button>
                         <button className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-xl text-xs font-bold hover:bg-indigo-100 transition-all"><Zap size={14} /> Sync Device</button>
                      </div>
                   </div>

                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-6 bg-slate-50 rounded-3xl border border-transparent hover:border-indigo-100 hover:bg-indigo-50/30 transition-all group overflow-hidden">
                         <div className="flex justify-between items-start mb-4">
                            <div>
                               <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest group-hover:text-indigo-600">Glucose (Fasting)</p>
                               <div className="flex items-baseline gap-1 mt-1">
                                  <span className="text-3xl font-black text-slate-900">92</span>
                                  <span className="text-xs font-bold text-slate-400">mg/dL</span>
                               </div>
                            </div>
                            <div className="px-2 py-0.5 bg-emerald-500/10 text-emerald-600 rounded text-[9px] font-black uppercase">Optimal</div>
                         </div>
                         <HealthTrendChart data={glucoseData} color="#10b981" type="area" />
                      </div>

                      <div className="p-6 bg-slate-50 rounded-3xl border border-transparent hover:border-indigo-100 hover:bg-indigo-50/30 transition-all group overflow-hidden text-right">
                         <div className="flex justify-between items-start mb-4 flex-row-reverse text-right">
                            <div className="text-right">
                               <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest group-hover:text-indigo-600">Heart Rate</p>
                               <div className="flex items-baseline gap-1 mt-1 flex-row-reverse">
                                  <span className="text-3xl font-black text-slate-900">68</span>
                                  <span className="text-xs font-bold text-slate-400 pr-1">BPM</span>
                               </div>
                            </div>
                            <div className="px-2 py-0.5 bg-indigo-500/10 text-indigo-600 rounded text-[9px] font-black uppercase">Resting</div>
                         </div>
                         <HealthTrendChart data={hrData} color="#6366f1" />
                      </div>
                   </div>
                </div>

                {/* AI-Driven Historical Analysis Summary */}
                <div className="bg-slate-900 rounded-[2.5rem] p-10 text-white relative overflow-hidden group">
                   <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none group-hover:scale-110 transition-transform">
                      <BrainCircuit size={180} />
                   </div>
                   <div className="relative z-10 grid grid-cols-1 md:grid-cols-12 gap-10">
                      <div className="md:col-span-7 space-y-6">
                         <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-indigo-500/20 border border-indigo-500/30 rounded-full">
                            <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse" />
                            <span className="text-[10px] font-bold uppercase tracking-[0.2em]">{t.medicalIntelligence} Engine 2.0</span>
                         </div>
                         <h3 className="text-3xl font-bold tracking-tight">Your Health Outlook is Stable</h3>
                         <p className="text-slate-400 text-sm leading-relaxed">
                            Cross-referencing your last 3 lab panels and wearable data, we detect a 12% improvement in metabolic efficiency. Your Vitamin D levels are normalizing, but continue supplementation as prescribed.
                         </p>
                         <div className="flex gap-4">
                            <button className="flex-1 py-4 bg-white text-slate-900 rounded-2xl font-bold flex items-center justify-center gap-3 hover:bg-slate-50 active:scale-95 transition-all">
                               Full Intelligence Report <ArrowUpRight size={18} />
                            </button>
                         </div>
                      </div>
                      <div className="md:col-span-5 flex flex-col justify-center border-l border-white/10 pl-10">
                         <div className="space-y-6">
                            {[
                              { label: 'Metabolic Rank', value: 'Top 15%', color: 'text-indigo-400' },
                              { label: 'Predicted Improvement', value: '+4.2%', color: 'text-emerald-400' },
                              { label: 'SLA Data Integrity', value: '100% Valid', color: 'text-slate-400' }
                            ].map((met, idx) => (
                              <div key={idx} className="flex flex-col">
                                 <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">{met.label}</span>
                                 <span className={cn("text-xl font-bold", met.color)}>{met.value}</span>
                              </div>
                            ))}
                         </div>
                      </div>
                   </div>
                </div>
             </div>

             {/* Sidebar Info Hub */}
             <div className="lg:col-span-4 space-y-6">
                {/* Health Timeline Preview */}
                <div className="bg-white rounded-[2.5rem] border border-slate-200 p-8 shadow-sm">
                   <h3 className="text-lg font-bold mb-6 flex items-center justify-between">
                     {t.timeline}
                     <button onClick={() => setActiveSegment('timeline')} className="text-xs text-indigo-600 hover:underline">View All</button>
                   </h3>
                   <div className="space-y-8 relative">
                      <div className="absolute left-4 top-2 bottom-2 w-px bg-slate-100" />
                      {[
                        { date: 'Today', event: 'Lab Appointment', type: 'appointment', icon: Calendar, color: 'bg-indigo-500' },
                        { date: 'Mar 12', event: 'CBC Results Shared', type: 'lab', icon: Beaker, color: 'bg-emerald-500' },
                        { date: 'Feb 28', event: 'Prescription Expiry', type: 'alert', icon: AlertCircle, color: 'bg-amber-500' }
                      ].map((evt, idx) => (
                        <div key={idx} className="relative pl-10 group">
                           <div className={cn("absolute left-1.5 top-1 w-5 h-5 rounded-lg flex items-center justify-center text-white z-10 shadow-sm", evt.color)}>
                              <evt.icon size={12} />
                           </div>
                           <div>
                              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{evt.date}</p>
                              <p className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">{evt.event}</p>
                           </div>
                        </div>
                      ))}
                   </div>
                </div>

                {/* Consent Status Quick Access */}
                <div className="bg-emerald-50 border border-emerald-100 rounded-[2.5rem] p-8">
                   <div className="flex items-center gap-3 mb-6">
                      <ShieldCheck className="w-8 h-8 text-emerald-600" />
                      <div>
                         <h3 className="font-bold text-emerald-900 tracking-tight">{t.consentManagement}</h3>
                         <p className="text-[10px] text-emerald-600 font-bold uppercase tracking-widest">Active Sovereignty</p>
                      </div>
                   </div>
                   <div className="space-y-3 mb-6">
                      <div className="flex items-center justify-between p-3 bg-white/50 rounded-xl">
                        <span className="text-xs font-medium text-emerald-800">Primary GP</span>
                        <span className="text-[10px] px-2 py-0.5 bg-emerald-600 text-white rounded font-black">ACTIVE</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-white/50 rounded-xl">
                        <span className="text-xs font-medium text-emerald-800">Regional Lab</span>
                        <span className="text-[10px] px-2 py-0.5 bg-amber-500 text-white rounded font-black">EXPIRING</span>
                      </div>
                   </div>
                   <button className="w-full py-4 bg-emerald-600 text-white rounded-2xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-emerald-100 hover:scale-[1.02] transition-all">
                     Privacy Hub <ArrowUpRight size={18} />
                   </button>
                </div>
             </div>
          </motion.div>
        )}

        {activeSegment === 'triage' && (
          <motion.div
            key="triage"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <SymptomChecker />
          </motion.div>
        )}

        {activeSegment === 'family' && (
          <motion.div
            key="family"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-[3rem] p-12 border border-slate-200 shadow-sm text-center"
          >
            <div className="max-w-2xl mx-auto space-y-8">
              <div className="w-24 h-24 bg-indigo-50 text-indigo-600 rounded-[2rem] flex items-center justify-center mx-auto mb-8">
                <Users size={48} />
              </div>
              <h2 className="text-3xl font-black text-slate-900 tracking-tighter italic">Family Health Management Coming Soon</h2>
              <p className="text-slate-500 font-medium text-lg leading-relaxed">
                Connect and manage the health records of your dependents securely. Shared biometric verification for children and elderly care is in the final phase of regulatory approval.
              </p>
              <button className="px-10 py-4 bg-slate-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl">
                Get Notified on Launch
              </button>
            </div>
          </motion.div>
        )}

        {activeSegment === 'security' && (
          <motion.div 
            key="security"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-8"
          >
             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {/* Biometric Status Card */}
                <div className="bg-white p-10 rounded-[3rem] border border-slate-200 shadow-sm space-y-8 relative overflow-hidden group">
                   <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 transition-transform">
                      <Fingerprint size={120} />
                   </div>
                   <div className="flex items-center gap-4">
                      <div className="flex flex-col xl:flex-row gap-8 items-start mb-12">
                       <div className="w-full xl:w-auto">
                          <h3 className="text-xl font-bold mb-6 flex items-center gap-3">
                             <ShieldCheck className="text-emerald-500" />
                             Iraqi National Cloud ID
                          </h3>
                          <NationalIDCard 
                            name="Samer Mohammed" 
                            id="GID-292-1029-X8" 
                            dob="12/05/2024" 
                            bloodType="O+" 
                            expiry="12/05/2034"
                          />
                       </div>
                    </div>

                    <div className="p-4 bg-indigo-600 text-white rounded-2xl shadow-xl shadow-indigo-100">
                         <Fingerprint size={32} />
                      </div>
                      <div>
                         <h3 className="text-xl font-bold tracking-tight">Biometric Log</h3>
                         <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">Enrollment Status</p>
                      </div>
                   </div>

                   <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100">
                         <div className="flex items-center gap-3">
                            <Fingerprint size={20} className={isBiometricActive ? "text-indigo-600" : "text-slate-300"} />
                            <span className="text-sm font-bold text-slate-700">Touch ID / Fingerprint</span>
                         </div>
                         <button 
                           onClick={() => {
                             setBiometricType('fingerprint');
                             setShowBiometricModal(true);
                           }}
                           className={cn(
                             "px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all",
                             isBiometricActive ? "bg-emerald-500 text-white" : "bg-indigo-600 text-white shadow-lg active:scale-95"
                           )}
                         >
                            {isBiometricActive ? "Verified" : "Enroll"}
                         </button>
                      </div>

                      <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100">
                         <div className="flex items-center gap-3">
                            <ScanFace size={20} className="text-slate-300" />
                            <span className="text-sm font-bold text-slate-700">Face ID Recognition</span>
                         </div>
                         <button 
                           onClick={() => {
                             setBiometricType('face');
                             setShowBiometricModal(true);
                           }}
                           className="px-4 py-1.5 bg-slate-200 text-slate-500 rounded-lg text-[10px] font-black uppercase tracking-widest cursor-not-allowed"
                         >
                            Inactive
                         </button>
                      </div>
                   </div>

                   <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                      <div className="flex gap-3">
                         <ShieldEllipsis size={18} className="text-indigo-600 shrink-0" />
                         <p className="text-[10px] text-slate-500 leading-relaxed font-medium">
                            Biometric keys are stored locally in Iraq National Cloud (INC) hardware enclaves. Your data never leaves the secure hardware.
                         </p>
                      </div>
                   </div>
                </div>

                {/* Audit Log Card */}
                <div className="bg-slate-900 text-white p-10 rounded-[3rem] space-y-8 relative overflow-hidden group">
                   <div className="absolute top-0 right-0 p-8 opacity-10">
                      <ShieldCheck size={120} />
                   </div>
                   <div className="flex items-center gap-4">
                      <div className="p-4 bg-emerald-500/20 text-emerald-400 rounded-2xl">
                         <ShieldCheck size={32} />
                      </div>
                      <div>
                         <h3 className="text-xl font-bold tracking-tight">Access Logs</h3>
                         <p className="text-xs text-emerald-400/60 font-bold uppercase tracking-widest">Sovereign Data Guardian</p>
                      </div>
                   </div>

                   <div className="space-y-4">
                      {[
                        { time: '2m ago', action: 'Auth: Fingerprint Success', device: 'iPhone 15' },
                        { time: '1h ago', action: 'Data Export: PDF Generation', device: 'Web Console' },
                        { time: 'Yesterday', action: 'Consent Revoked: Dr. Omar', device: 'System Proxy' }
                      ].map((log, i) => (
                        <div key={i} className="flex items-center justify-between text-xs border-b border-white/5 pb-4">
                           <div>
                              <p className="font-bold">{log.action}</p>
                              <p className="text-[10px] text-slate-500 font-medium">{log.device}</p>
                           </div>
                           <span className="text-slate-500">{log.time}</span>
                        </div>
                      ))}
                   </div>

                   <button className="w-full py-4 bg-white/5 text-xs font-black uppercase tracking-widest rounded-2xl hover:bg-white/10 transition-all border border-white/10">
                      View Full Audit Chain
                   </button>
                </div>

                {/* Cyber Security Tips */}
                <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 text-white p-10 rounded-[3rem] flex flex-col justify-between shadow-2xl shadow-indigo-200">
                   <div className="space-y-6">
                      <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
                         <BrainCircuit size={32} />
                      </div>
                      <h3 className="text-2xl font-black leading-tight">Patient Data Privacy is a Right, Not a Luxury.</h3>
                      <p className="text-indigo-100 text-sm leading-relaxed opacity-80 italic">
                         "GULA uses 256-bit AES encryption for all personal records. We recommend rotating your digital keys every 90 days."
                      </p>
                   </div>
                   <div className="space-y-4">
                      <div className="flex items-center gap-2">
                         <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                         <span className="text-[10px] font-black uppercase tracking-widest">Security Health: EXCELLENT</span>
                      </div>
                   </div>
                </div>
             </div>
          </motion.div>
        )}

        {activeSegment === 'results' && (
          <motion.div 
            key="results"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-6"
          >
            {/* Quick Summary Strip */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
               <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">Total Panels</p>
                  <p className="text-3xl font-black text-slate-900">42</p>
               </div>
               <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">Alert Level</p>
                  <div className="flex items-center gap-2">
                     <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                     <p className="text-xl font-bold text-red-600 uppercase">Attention Needed</p>
                  </div>
               </div>
               <button className="bg-indigo-600 p-6 rounded-3xl text-white shadow-xl shadow-indigo-100 flex items-center justify-center gap-3 font-bold hover:scale-[1.02] transition-all">
                  <Download size={22} /> Export Secure Health Bundle
               </button>
            </div>

            <div className="bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden">
               <div className="p-8 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                     <FlaskConical className="text-indigo-600" />
                     <h3 className="text-xl font-bold">Latest Laboratory Reports</h3>
                  </div>
                  <div className="flex bg-slate-100 p-1 rounded-xl">
                     <button className="px-4 py-1.5 bg-white text-indigo-600 rounded-lg text-xs font-bold shadow-sm">Card View</button>
                     <button className="px-4 py-1.5 text-slate-500 text-xs font-bold">List View</button>
                  </div>
               </div>
               <div className="p-8 space-y-6">
                  {recentResults.map(res => (
                    <div key={res.id} className="p-8 bg-slate-50 rounded-[2rem] border border-transparent hover:border-indigo-100 hover:bg-white transition-all">
                       <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                          <div className="lg:col-span-4 flex items-center gap-6">
                             <div className={cn(
                               "w-16 h-16 rounded-[1.25rem] flex items-center justify-center text-white shadow-lg",
                               res.flag === 'L' || res.flag === 'H' ? "bg-red-600 shadow-red-100" : "bg-indigo-600 shadow-indigo-100"
                             )}>
                                <ActivityIcon size={28} />
                             </div>
                             <div>
                                <h4 className="text-xl font-black text-slate-900 uppercase tracking-tight">{res.testName}</h4>
                                <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">{res.labName} • Feb 24, 2024</p>
                             </div>
                          </div>
                          
                          <div className="lg:col-span-4 grid grid-cols-2 gap-8 border-l border-r border-slate-200 px-8">
                             <div>
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Result</span>
                                <div className="flex items-baseline gap-1">
                                   <span className={cn("text-3xl font-black", res.flag === 'L' || res.flag === 'H' ? "text-red-600" : "text-emerald-600")}>{res.value}</span>
                                   <span className="text-xs font-bold text-slate-400">{res.unit}</span>
                                </div>
                             </div>
                             <div>
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Normal Range</span>
                                <span className="text-lg font-bold text-slate-900 tracking-tight">{res.range}</span>
                             </div>
                          </div>
                          <div className="lg:col-span-4 flex items-center justify-between pl-8">
                             <div>
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2">Trend</span>
                                <div className="flex items-end gap-1 h-10">
                                   {[30, 45, 25, 40, 35, 50].map((h, i) => (
                                      <div key={i} className="w-1.5 bg-indigo-100 rounded-full group-hover:bg-indigo-300 transition-colors" style={{ height: `${h}%` }} />
                                   ))}
                                </div>
                             </div>
                             <div className="flex gap-2">
                                <button 
                                  onClick={() => setExplainingResult(res)}
                                  className="p-3 bg-indigo-50 border border-indigo-100 rounded-2xl text-indigo-600 hover:bg-indigo-600 hover:text-white transition-all group/ai"
                                  title="AI Interpretation"
                                >
                                   <BrainCircuit size={20} className="group-hover/ai:rotate-12 transition-transform" />
                                </button>
                                <button className="p-3 bg-white border border-slate-200 rounded-2xl hover:border-indigo-600 hover:text-indigo-600 transition-all">
                                   <Download size={20} />
                                </button>
                                <button className="p-3 bg-white border border-slate-200 rounded-2xl hover:border-indigo-600 hover:text-indigo-600 transition-all">
                                   <ArrowUpRight size={20} />
                                </button>
                             </div>
                          </div>
                        </div>
                     </div>
                  ))}
               </div>
            </div>
          </motion.div>
        )}

      <AnimatePresence>
        {explainingResult && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setExplainingResult(null)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-xl"
            />
            <motion.div 
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative bg-white w-full max-w-2xl rounded-[3rem] shadow-2xl border border-slate-100 overflow-hidden"
            >
              <div className="p-10 bg-indigo-600 text-white relative overflow-hidden">
                <div className="absolute top-0 right-0 p-12 opacity-10 rotate-12">
                   <Sparkles size={120} />
                </div>
                <div className="relative z-10 flex items-center justify-between">
                   <div className="flex items-center gap-4">
                      <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-md">
                         <BrainCircuit size={32} />
                      </div>
                      <div>
                        <h3 className="text-2xl font-black italic tracking-tight">AI Clinical Insight.</h3>
                        <p className="text-[10px] uppercase font-bold tracking-widest opacity-80">{explainingResult.testName} Analysis</p>
                      </div>
                   </div>
                   <button 
                     onClick={() => setExplainingResult(null)}
                     className="p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
                   >
                     <X size={24} />
                   </button>
                </div>
              </div>

              <div className="p-12 overflow-y-auto max-h-[60vh]">
                {isExplaining ? (
                  <div className="flex flex-col items-center justify-center py-20 gap-8">
                    <div className="relative">
                       <Loader2 size={64} className="text-indigo-600 animate-spin" />
                       <Sparkles size={24} className="absolute -top-2 -right-2 text-indigo-400 animate-pulse" />
                    </div>
                    <div className="text-center space-y-2">
                       <p className="text-lg font-black text-slate-900 uppercase tracking-widest italic">Analyzing Biological Data...</p>
                       <p className="text-sm text-slate-400 font-medium max-w-xs mx-auto">Gemini Clinical Engine is cross-referencing your results with current medical standards.</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-100 rounded-2xl">
                       <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                       <span className="text-[10px] font-black text-emerald-700 uppercase tracking-widest">GULA Health Layer • Verified Clinical Model</span>
                    </div>
                    
                    <div className="markdown-body prose prose-slate max-w-none prose-p:leading-8 prose-p:text-slate-600 prose-strong:text-indigo-600 font-medium">
                      <Markdown>{aiExplanation || ''}</Markdown>
                    </div>

                    <div className="p-6 bg-slate-50 rounded-[2rem] border border-slate-100 italic text-xs text-slate-400 leading-relaxed">
                      <strong>Medical Disclaimer:</strong> This interpretation is generated by GULA AI for educational purposes only. It is not a diagnosis. Please review all results with your healthcare provider.
                    </div>

                    <div className="flex items-center gap-4 pt-10 border-t border-slate-100">
                       <button 
                         onClick={() => setExplainingResult(null)}
                         className="flex-1 py-5 bg-slate-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-slate-800 transition-colors shadow-2xl active:scale-95"
                       >
                         Acknowledge Insight
                       </button>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

        {activeSegment === 'timeline' && (
          <motion.div 
            key="timeline"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl mx-auto space-y-12"
          >
             <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold text-slate-900 tracking-tight">Clinical Health Journey</h2>
                <p className="text-slate-500">A comprehensive immutable log of your medical milestones.</p>
             </div>

             <div className="relative space-y-12">
               {/* Vertical Line */}
               <div className="absolute left-1/2 top-4 bottom-4 w-1 bg-slate-100 -translate-x-1/2" />
               
               {history.map((item, i) => (
                 <motion.div 
                   key={item.id}
                   initial={{ opacity: 0, x: i % 2 === 0 ? -40 : 40 }}
                   whileInView={{ opacity: 1, x: 0 }}
                   viewport={{ once: true }}
                   className={cn(
                     "flex items-center gap-12 relative w-full",
                     i % 2 === 0 ? "flex-row" : "flex-row-reverse text-right"
                   )}
                 >
                   {/* Timeline Element */}
                   <div className="flex-1 w-full">
                      <div className={cn(
                        "p-8 bg-white border border-slate-200 rounded-[2.5rem] shadow-sm hover:shadow-xl hover:border-indigo-600 transition-all group",
                        i % 2 === 0 ? "text-right" : "text-left"
                      )}>
                         <span className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em] mb-4 block">
                            {item.type} • {item.date}
                         </span>
                         <h4 className="text-2xl font-black text-slate-900 mb-2 leading-none">{item.title}</h4>
                         <p className="text-slate-500 text-sm leading-relaxed mb-6 italic">"{item.description}"</p>
                         <div className={cn("flex items-center gap-3", i % 2 === 0 ? "justify-end" : "justify-start")}>
                            <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                               <MapPin size={18} />
                            </div>
                            <span className="text-xs font-bold text-slate-700">{item.provider}</span>
                         </div>
                      </div>
                   </div>

                   {/* Center Dot */}
                   <div className="relative z-10">
                      <div className="w-12 h-12 bg-white border-8 border-indigo-600 rounded-full shadow-2xl flex items-center justify-center">
                         <div className="w-1.5 h-1.5 bg-indigo-600 rounded-full animate-ping" />
                      </div>
                   </div>

                   {/* Spacer for Reverse Row */}
                   <div className="flex-1" />
                 </motion.div>
               ))}
             </div>
          </motion.div>
        )}

        {/* ... similar enhanced family view if needed ... */}
      </AnimatePresence>

      {/* Biometric Auth Modal/Simulation */}
      <AnimatePresence>
        {showBiometricModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowBiometricModal(false)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-xl"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative bg-white w-full max-w-md rounded-[3rem] p-10 shadow-2xl border border-slate-200 overflow-hidden"
            >
               <div className="absolute top-0 right-0 p-8 opacity-5">
                  {biometricType === 'fingerprint' ? <Fingerprint size={160} /> : <ScanFace size={160} />}
               </div>
               
               <div className="text-center space-y-8 relative z-10">
                  <div className="w-24 h-24 bg-indigo-600 text-white rounded-3xl flex items-center justify-center mx-auto shadow-2xl shadow-indigo-100 animate-pulse">
                     {biometricType === 'fingerprint' ? <Fingerprint size={48} /> : <ScanFace size={48} />}
                  </div>
                  
                  <div>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">
                       {biometricType === 'fingerprint' ? 'Touch ID Enrollment' : 'Face ID Recognition'}
                    </h2>
                    <p className="text-slate-500 font-medium text-sm">
                       Please scan your {biometricType === 'fingerprint' ? 'finger' : 'face'} using your device's biometric sensor.
                    </p>
                  </div>

                  <div className="flex flex-col gap-4">
                     <button 
                       onClick={() => {
                         setIsBiometricActive(true);
                         setShowBiometricModal(false);
                         toast.success("Biometric verification enabled successfully!");
                       }}
                       className="w-full py-5 bg-slate-900 text-white rounded-2xl font-black uppercase tracking-widest text-xs shadow-xl active:scale-95 transition-all"
                     >
                        Simulate Success Scan
                     </button>
                     <button 
                       onClick={() => setShowBiometricModal(false)}
                       className="w-full py-4 text-slate-400 font-black uppercase tracking-widest text-xs hover:text-slate-600 transition-all"
                     >
                        Cancel
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
