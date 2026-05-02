import React, { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Zap, AlertCircle, Calendar, Pill, BrainCircuit, 
  ArrowUpRight, Heart, TrendingUp, ShieldCheck, 
  Stethoscope, Box, Clock, ChevronRight, Activity,
  Download, Share2, Info, Bell, Users
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';
import { MedicineCabinet } from '../../components/citizen/MedicineCabinet';
import { HealthTrendChart } from '../../components/HealthTrendChart';
import { FamilySwitcher } from '../../components/citizen/FamilySwitcher';
import { Link } from 'react-router-dom';

export function CitizenDashboard() {
  const { t } = useLanguage();
  const [showScoreBreakdown, setShowScoreBreakdown] = useState(false);

  const healthScore = 85;

  const todayTasks = [
    { id: 't1', title: 'Fasting Glucose Test', time: '08:00 AM', type: 'test', location: 'Central Lab', status: 'upcoming' },
    { id: 't2', title: 'Metformin 500mg', time: '08:00 AM', type: 'medication', dosage: '1 Pill', status: 'due' },
    { id: 't3', title: 'Cardiologist Follow-up', time: '11:45 AM', type: 'appointment', doctor: 'Dr. Sarah', status: 'upcoming' },
    { id: 't4', title: 'Vitamin D3', time: '01:00 PM', type: 'medication', dosage: '2000 IU', status: 'future' },
  ];

  const criticalAlerts = [
    { 
      id: 'a1', 
      title: 'Action Recommended', 
      description: 'Your Vitamin D levels (22 ng/mL) remain below optimal range despite supplementation.', 
      severity: 'warning' 
    }
  ];

  return (
    <div className="space-y-8 max-w-[1600px] mx-auto p-4 md:p-8 animate-in fade-in duration-500 pb-20">
      {/* 🟢 TOP LAYER: PRIORITY ENGINE */}
      <AnimatePresence>
        {criticalAlerts.map(alert => (
          <motion.div 
            key={alert.id}
            initial={{ height: 0, opacity: 0, y: -20 }}
            animate={{ height: 'auto', opacity: 1, y: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-amber-500 text-white p-6 rounded-[2.5rem] flex flex-col md:flex-row items-center justify-between shadow-2xl shadow-amber-200/50 mb-6 border-b-4 border-amber-600">
              <div className="flex items-center gap-6 mb-4 md:mb-0">
                <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center animate-pulse shrink-0">
                  <AlertCircle size={32} />
                </div>
                <div>
                  <h3 className="font-black text-xl tracking-tight uppercase flex items-center gap-3">
                    {t.proactiveEngagement}: {alert.title}
                    <span className="px-2 py-0.5 bg-white/20 rounded text-[9px] font-black uppercase">Next Steps</span>
                  </h3>
                  <p className="text-sm text-amber-100 font-medium opacity-90">{alert.description}</p>
                </div>
              </div>
              <div className="flex gap-3 w-full md:w-auto">
                <Link to="/citizen/results" className="flex-1 md:flex-none px-8 py-4 bg-white text-amber-600 rounded-2xl font-black text-xs uppercase tracking-widest shadow-lg hover:scale-[1.02] transition-all text-center">
                  Analyze Result
                </Link>
                <Link to="/citizen/appointments" className="flex-1 md:flex-none px-8 py-4 bg-amber-700 text-white border border-amber-500/50 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-amber-800 transition-all text-center">
                  Book Specialist
                </Link>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* 🔵 HERO SECTION: THE HEALTH OS CORE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Central Core: Score + Profile */}
        <div className="lg:col-span-8 flex flex-col md:flex-row items-center justify-between gap-8 bg-white p-10 rounded-[3.5rem] border border-slate-200/60 shadow-sm relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none transition-transform group-hover:scale-110">
            <Heart size={200} fill="currentColor" className="text-rose-500" />
          </div>
          
          <div className="relative z-10 flex items-center gap-10">
            <div 
              className="relative group cursor-pointer"
              onClick={() => setShowScoreBreakdown(!showScoreBreakdown)}
            >
              <div className="absolute inset-0 bg-indigo-500/5 rounded-full animate-pulse group-hover:bg-indigo-500/10 transition-all blur-xl" />
              
              <svg className="w-40 h-40 transform -rotate-90" viewBox="0 0 128 128">
                <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="6" fill="transparent" className="text-slate-100" />
                <motion.circle 
                  cx="64" cy="64" r="58" 
                  stroke="url(#hp-grad)" 
                  strokeWidth="8" fill="transparent" 
                  initial={{ strokeDashoffset: 364 }}
                  animate={{ strokeDashoffset: 364 - (364 * healthScore) / 100 }} 
                  strokeDasharray={364}
                  className="transition-all duration-1000 ease-out" 
                  strokeLinecap="round" 
                />
                <defs>
                  <linearGradient id="hp-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-4xl font-black text-slate-900 leading-none">{healthScore}</span>
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">Health Score</span>
              </div>
            </div>

            <div>
              <p className="text-[11px] font-black text-indigo-600 uppercase tracking-[0.3em] mb-2">{t.welcomeBack}, Samer</p>
              <h2 className="text-4xl font-black text-slate-900 tracking-tighter italic leading-none">{t.personalHealthVault}</h2>
              <div className="flex items-center gap-3 mt-4">
                <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-600 rounded-lg text-[9px] font-black uppercase border border-emerald-100">
                  <ShieldCheck size={12} /> {t.biometricVerified}
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1 bg-slate-900 text-white rounded-lg text-[9px] font-black uppercase">
                   LOA-3 Authorized
                </div>
              </div>
            </div>
          </div>

          <div className="relative z-10 flex gap-4">
            <FamilySwitcher />
            <button className="flex flex-col items-center justify-center p-5 bg-slate-900 text-white rounded-[2rem] hover:bg-indigo-600 transition-all group w-32 shadow-xl shadow-slate-200">
               <Zap size={24} className="mb-2 group-hover:scale-125 transition-transform" />
               <span className="text-[10px] font-black uppercase tracking-widest">Medical ID</span>
            </button>
          </div>
        </div>

        {/* AI Insight Box */}
        <div className="lg:col-span-4 bg-indigo-600 rounded-[3.5rem] p-10 text-white relative overflow-hidden group shadow-2xl shadow-indigo-100">
          <div className="absolute top-0 right-0 p-12 opacity-10 pointer-events-none group-hover:rotate-12 transition-transform duration-700">
            <BrainCircuit size={160} />
          </div>
          <div className="relative z-10 space-y-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-md">
                <BrainCircuit size={24} />
              </div>
              <h3 className="font-black text-lg uppercase tracking-widest">{t.medicalIntelligence}</h3>
            </div>
            <p className="text-lg font-medium leading-relaxed italic text-indigo-50">
              "You are on a 5-day streak of taking your medications on time. Keep it up! Your next Vitamin D check is due in 12 days."
            </p>
            <div className="pt-4 flex items-center justify-between">
               <span className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-200">System Outlook: Stable</span>
               <button className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center hover:bg-white/20 transition-all">
                  <ArrowUpRight size={20} />
               </button>
            </div>
          </div>
        </div>
      </div>

      {/* 🕒 MIDDLE LAYER: TODAY'S OPERATIONAL QUEUE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-4">
        {/* Today's Tasks */}
        <div className="lg:col-span-7 bg-white rounded-[3.5rem] p-10 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-10">
            <div>
              <h3 className="text-2xl font-black text-slate-900 tracking-tighter italic leading-none mb-2">Today's Focus</h3>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">Operational Health Schedule</p>
            </div>
            <Link to="/citizen/appointments" className="px-6 py-2 bg-slate-50 text-slate-600 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-100 transition-all">
              View Calendar
            </Link>
          </div>

          <div className="space-y-4">
            {todayTasks.map((task, i) => (
              <motion.div 
                key={task.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className={cn(
                  "p-6 rounded-[2.5rem] border flex items-center justify-between group transition-all cursor-pointer",
                  task.status === 'due' ? "bg-amber-50 border-amber-100" : "bg-slate-50 border-transparent hover:bg-white hover:border-slate-100 hover:shadow-xl hover:shadow-slate-100"
                )}
              >
                <div className="flex items-center gap-6">
                  <div className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg transition-transform group-hover:scale-110",
                    task.type === 'medication' ? 'bg-white text-emerald-500' : 
                    task.type === 'test' ? 'bg-white text-indigo-500' : 
                    'bg-white text-rose-500'
                  )}>
                    {task.type === 'medication' && <Pill size={24} />}
                    {task.type === 'test' && <TestTube size={24} />}
                    {task.type === 'appointment' && <Calendar size={24} />}
                  </div>
                  <div>
                    <h4 className="text-lg font-black text-slate-900 tracking-tight leading-none mb-1">{task.title}</h4>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                        <Clock size={12} /> {task.time}
                      </span>
                      <span className="w-1 h-1 bg-slate-200 rounded-full" />
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                        {task.dosage || task.location || task.doctor}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-4">
                  {task.status === 'due' && (
                    <button className="px-6 py-2 bg-amber-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-amber-200 animate-pulse">
                      Mark Complete
                    </button>
                  )}
                  <div className="p-3 bg-white rounded-xl border border-slate-100 text-slate-300 group-hover:text-indigo-600 group-hover:border-indigo-100 transition-all">
                    <ChevronRight size={20} />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Quick Access Menu */}
        <div className="lg:col-span-5 grid grid-cols-2 gap-6">
          <Link to="/citizen/assistant" className="col-span-2 group relative overflow-hidden bg-slate-900 rounded-[3rem] p-10 text-white hover:bg-slate-800 transition-all">
             <div className="absolute top-0 right-0 p-10 opacity-5 group-hover:scale-125 transition-transform duration-1000">
               <BrainCircuit size={160} />
             </div>
             <div className="relative z-10 mb-12">
                <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center mb-6">
                   <BrainCircuit size={32} className="text-indigo-400" />
                </div>
                <h3 className="text-3xl font-black italic tracking-tighter leading-tight">AI Health Assistant</h3>
                <p className="text-slate-400 mt-2 text-sm font-medium">Interpret records or check symptoms instantly.</p>
             </div>
             <div className="flex items-center justify-between text-xs font-black uppercase tracking-[0.2em] border-t border-white/5 pt-6">
                <span>Start Conversation</span>
                <ChevronRight size={20} className="text-indigo-500 group-hover:translate-x-2 transition-transform" />
             </div>
          </Link>

          <Link to="/citizen/results" className="bg-white border border-slate-200 p-8 rounded-[3rem] hover:border-indigo-600 transition-all group shadow-sm">
             <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl w-fit mb-6 group-hover:bg-indigo-600 group-hover:text-white transition-all">
                <Box size={24} />
             </div>
             <h4 className="text-xl font-black text-slate-900 tracking-tight leading-none mb-2">{t.labResults}</h4>
             <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{t.resultsInterpretation}</p>
          </Link>

          <Link to="/citizen/medications" className="bg-white border border-slate-200 p-8 rounded-[3rem] hover:border-indigo-600 transition-all group shadow-sm">
             <div className="p-4 bg-emerald-50 text-emerald-600 rounded-2xl w-fit mb-6 group-hover:bg-emerald-600 group-hover:text-white transition-all">
                <Pill size={24} />
             </div>
             <h4 className="text-xl font-black text-slate-900 tracking-tight leading-none mb-2">{t.medicineCabinet}</h4>
             <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active Adherence</p>
          </Link>
        </div>
      </div>

      {/* 🔴 VITAL TRENDS OVERLAY */}
      <div className="bg-white rounded-[3.5rem] p-12 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h3 className="text-3xl font-black text-slate-900 tracking-tighter italic leading-none mb-2">Trends & Bio-Signals</h3>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">Continuously Monitored Bio-Data</p>
            </div>
            <div className="flex gap-3">
              <button className="px-6 py-3 bg-slate-50 text-slate-600 rounded-2xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-slate-100">
                <Info size={14} /> Historical Context
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
             <TrendCard label="Glucose (Daily)" value="92" unit="mg/dL" status="Optimal" color="#6366f1" />
             <TrendCard label="Heart Rate" value="68" unit="BPM" status="Resting" color="#ec4899" />
             <TrendCard label="Blood Pressure" value="114/76" unit="mmHg" status="Stable" color="#10b981" />
          </div>
      </div>
    </div>
  );
}

function TrendCard({ label, value, unit, status, color }: { label: string, value: string, unit: string, status: string, color: string }) {
  const mockData = [
     { time: '08:00', value: 80 },
     { time: '10:00', value: 85 },
     { time: '12:00', value: 95 },
     { time: '14:00', value: 90 },
     { time: '16:00', value: 82 },
     { time: '18:00', value: 88 },
  ];

  return (
    <div className="space-y-6 group">
       <div className="flex justify-between items-start">
          <div>
            <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest group-hover:text-indigo-600 transition-colors mb-2">{label}</p>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-black text-slate-900">{value}</span>
              <span className="text-xs font-bold text-slate-400">{unit}</span>
            </div>
          </div>
          <div className="px-3 py-1 bg-slate-50 rounded-lg text-[9px] font-black uppercase border border-slate-100 text-slate-500 whitespace-nowrap">
            {status}
          </div>
       </div>
       <div className="h-24 overflow-hidden rounded-2xl">
          <HealthTrendChart data={mockData} color={color} type="area" />
       </div>
    </div>
  );
}

const TestTube = ({ size, className }: { size: number, className?: string }) => (
  <svg 
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
    <path d="M14 2v17.8c0 .1.1.2.2.2h3.6c.1 0 .2-.1.2-.2V2"/>
    <path d="M10 2v17.8c0 .1-.1.2-.2.2H6.2c-.1 0-.2-.1-.2-.2V2"/>
    <path d="M3 2h18"/>
    <path d="M3 7h18"/>
  </svg>
);
