import React, { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Users, Clock, AlertCircle, CheckCircle2, 
  ChevronRight, BrainCircuit, UserCheck, 
  Activity, MapPin, PhoneForwarded
} from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../../lib/utils';

interface QueuedPatient {
  id: string;
  name: string;
  age: number;
  reason: string;
  waitingTime: string;
  slaRemaining: number; // in minutes
  priority: 'low' | 'medium' | 'high' | 'critical';
  triageScore: number;
  riskIndex: number;
  tags: string[];
  vitals: { hr: number; bp: string; temp: string };
  status: 'waiting' | 'in_consultation' | 'completed';
}

export function DoctorPriorityQueue() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<'all' | 'critical' | 'assigned' | 'completed'>('all');
  
  const queue: QueuedPatient[] = [
    { 
      id: 'P-102', 
      name: 'Ahmed K.', 
      age: 45, 
      reason: 'Persistent Chest Pain', 
      waitingTime: '8m', 
      slaRemaining: 12,
      priority: 'critical', 
      triageScore: 98,
      riskIndex: 94,
      tags: ['HTN', 'Chest Pain'],
      vitals: { hr: 110, bp: '160/95', temp: '37.1°C' },
      status: 'waiting'
    },
    { 
      id: 'P-105', 
      name: 'Layla S.', 
      age: 32, 
      reason: 'Post-Op Fever', 
      waitingTime: '15m', 
      slaRemaining: 45,
      priority: 'high', 
      triageScore: 82,
      riskIndex: 65,
      tags: ['Surgical', 'Fever'],
      vitals: { hr: 92, bp: '120/80', temp: '38.9°C' },
      status: 'waiting'
    },
    { 
      id: 'P-108', 
      name: 'Omar R.', 
      age: 67, 
      reason: 'Routine Follow-up', 
      waitingTime: '22m', 
      slaRemaining: 120,
      priority: 'low', 
      triageScore: 45,
      riskIndex: 22,
      tags: ['Diabetes', 'Refill'],
      vitals: { hr: 72, bp: '135/85', temp: '36.6°C' },
      status: 'waiting'
    }
  ];

  const filteredQueue = queue.filter(p => {
    if (activeTab === 'all') return true;
    if (activeTab === 'critical') return p.priority === 'critical';
    return true;
  });

  return (
    <div className="bg-white rounded-[2.5rem] border border-slate-200 p-8 shadow-sm">
      <div className="flex flex-col md:flex-row items-center justify-between mb-10 gap-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-indigo-600 rounded-[1.5rem] flex items-center justify-center text-white shadow-xl shadow-indigo-100">
            <Users size={28} />
          </div>
          <div>
            <h3 className="text-2xl font-black text-slate-900 tracking-tighter">Clinical Work Queue</h3>
            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">
              <BrainCircuit size={12} className="text-indigo-500" /> Cognitive Load Balancing Active
            </div>
          </div>
        </div>
        
        <div className="flex bg-slate-100 p-1.5 rounded-[2rem] border border-slate-200/50">
          {[
            { id: 'all', label: 'All Tasks', count: 12 },
            { id: 'critical', label: 'Critical', count: 2 },
            { id: 'assigned', label: 'My Cases', count: 4 },
            { id: 'completed', label: 'Done', count: 32 }
          ].map(tab => (
            <button 
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "px-6 py-3 rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-3",
                activeTab === tab.id 
                  ? "bg-white text-indigo-600 shadow-xl shadow-indigo-100/20" 
                  : "text-slate-400 hover:text-slate-600"
              )}
            >
              {tab.label}
              <span className={cn(
                "px-2 py-0.5 rounded-full text-[9px]",
                activeTab === tab.id ? "bg-indigo-600 text-white" : "bg-slate-200 text-slate-500"
              )}>{tab.count}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {filteredQueue.map((patient, idx) => (
          <motion.div
            key={patient.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="group flex flex-col lg:flex-row lg:items-center gap-6 p-6 bg-slate-50 rounded-[2.5rem] border border-transparent hover:border-indigo-100 hover:bg-white hover:shadow-2xl hover:shadow-indigo-100/40 transition-all cursor-pointer relative overflow-hidden"
          >
            {/* SLA Progress Bar */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-slate-200">
               <div 
                 className={cn(
                   "h-full transition-all duration-1000",
                   patient.slaRemaining < 15 ? "bg-red-500" : "bg-indigo-500"
                 )} 
                 style={{ width: `${Math.max(0, 100 - (patient.slaRemaining / 120) * 100)}%` }}
               />
            </div>

            <div className="flex-1 flex items-center gap-6">
              <div className="relative">
                <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center text-slate-900 border border-slate-100 shadow-sm font-black text-xl group-hover:scale-110 transition-transform">
                  {patient.name[0]}
                </div>
                <div className={cn(
                  "absolute -top-2 -right-2 w-6 h-6 rounded-full border-4 border-white flex items-center justify-center text-[8px] font-black",
                  patient.priority === 'critical' ? "bg-red-500 text-white" : "bg-indigo-500 text-white"
                )}>
                  !
                </div>
              </div>
              <div>
                <div className="flex items-center gap-3 mb-1">
                   <h4 className="text-lg font-black text-slate-900 tracking-tight">
                     {patient.name}
                   </h4>
                   <span className="px-2 py-0.5 bg-slate-200 rounded text-[9px] font-black uppercase text-slate-500">#{patient.id}</span>
                </div>
                <p className="text-sm font-medium text-slate-500 mb-2 underline decoration-indigo-200 underline-offset-4">{patient.reason}</p>
                <div className="flex gap-2">
                  {patient.tags.map(tag => (
                    <span key={tag} className="px-2 py-0.5 bg-indigo-50 text-indigo-600 text-[8px] font-black uppercase rounded tracking-tighter">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-8 px-8 border-l border-r border-slate-200">
               <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Vitals Radar</span>
                  <div className="flex flex-col text-xs font-bold text-slate-900">
                    <span className="flex items-center gap-1"><Activity size={12} className="text-red-500" /> {patient.vitals.hr}</span>
                    <span className="flex items-center gap-1"><MapPin size={12} className="text-indigo-500" /> {patient.vitals.bp}</span>
                  </div>
               </div>
               <div className="text-center">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Risk Index</span>
                  <div className={cn(
                    "text-2xl font-black",
                    patient.riskIndex > 80 ? "text-red-600 animate-pulse" : "text-slate-900"
                  )}>
                    {patient.riskIndex}%
                  </div>
               </div>
               <div className="text-center">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">SLA Limit</span>
                  <div className={cn(
                    "text-lg font-black",
                    patient.slaRemaining < 15 ? "text-red-600" : "text-indigo-600"
                  )}>
                    {patient.slaRemaining}m
                  </div>
               </div>
               <div className="text-right">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Wait Time</span>
                  <div className="flex items-center justify-end gap-1 text-slate-900 font-black">
                    <Clock size={14} className="text-amber-500" />
                    {patient.waitingTime}
                  </div>
               </div>
            </div>

            <div className="flex items-center gap-3 pl-4">
              <button 
                onClick={(e) => { e.stopPropagation(); }}
                className="px-6 py-4 bg-indigo-600 text-white rounded-2xl shadow-xl shadow-indigo-100 hover:scale-105 active:scale-95 transition-all text-[10px] font-black uppercase tracking-widest flex items-center gap-2"
              >
                <UserCheck size={16} /> Open Dashboard
              </button>
              <button className="p-4 bg-white border border-slate-200 text-slate-400 rounded-2xl hover:bg-slate-50 transition-all">
                <PhoneForwarded size={20} />
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-8 flex items-center justify-center">
        <button className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 hover:text-indigo-600 transition-colors">
          Show All Queued (24 Patients)
        </button>
      </div>
    </div>
  );
}
