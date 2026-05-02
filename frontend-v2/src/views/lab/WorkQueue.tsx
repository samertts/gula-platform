import React, { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Microscope, PlayCircle, CheckCircle2, AlertCircle, 
  Clock, User, Shield, Zap, Filter, Search,
  ArrowRight, PauseCircle, Timer, MoreVertical,
  Activity as ActivityIcon, Users, Settings,
  Wifi, WifiOff, AlertTriangle, ClipboardList,
  Image as ImageIcon, Terminal, Keyboard, Scan,
  Dna, Cpu, Box
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../../lib/utils';
import { toast } from 'sonner';
import { ResultEntryUI } from '../../components/lab/ResultEntryUI';

type TaskStatus = 'unassigned' | 'claimed' | 'in-progress' | 'review' | 'completed';
type TaskPriority = 'routine' | 'urgent'| 'stat';

interface LabTask {
  id: string;
  sampleId: string;
  patientId: string;
  patientName: string;
  testName: string;
  priority: TaskPriority;
  status: TaskStatus;
  slaMinutes: number;
  timeRemaining: number;
  owner?: string;
  section: string;
  dueAt: Date;
  notes?: string;
  attachments?: string[];
}

export function WorkQueue() {
  const { t } = useLanguage();
  const { profile } = useAuth();
  const [viewMode, setViewMode] = useState<'technician' | 'pathologist' | 'manager'>('technician');
  const [filterSection, setFilterSection] = useState('All');
  const [sortBy, setSortBy] = useState<'priority' | 'due'>('priority');
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);
  const [isResultEntryOpen, setIsResultEntryOpen] = useState<LabTask | null>(null);

  const [tasks, setTasks] = useState<LabTask[]>([
    { 
      id: 'T1', 
      sampleId: 'SMP-8832', 
      patientId: 'PAT-0044',
      patientName: 'Ahmed Mohammed Ali',
      testName: 'Cardiac Markers (Troponin I)', 
      priority: 'stat', 
      status: 'unassigned', 
      slaMinutes: 30, 
      timeRemaining: 5, 
      section: 'Biochemistry', 
      dueAt: new Date(Date.now() + 5 * 60000),
      notes: 'Patient showing symptoms of acute myocardial infarction. Expedite results.',
      attachments: ['ECG_Report.pdf', 'Clinical_History.docx']
    },
    { 
      id: 'T2', 
      sampleId: 'SMP-1029', 
      patientId: 'PAT-8812',
      patientName: 'Sarah Jenkins',
      testName: 'CBC + Differential', 
      priority: 'urgent', 
      status: 'claimed', 
      slaMinutes: 60, 
      timeRemaining: 25, 
      owner: 'Technician Ali', 
      section: 'Hematology', 
      dueAt: new Date(Date.now() + 25 * 60000),
      notes: 'Post-operative monitoring. Check for leukocyte count elevation.',
      attachments: ['Lab_Order_Request.pdf']
    },
    { 
      id: 'T3', 
      sampleId: 'SMP-9921', 
      patientId: 'PAT-3321',
      patientName: 'Michael Chen',
      testName: 'HbA1c', 
      priority: 'routine', 
      status: 'in-progress', 
      slaMinutes: 120, 
      timeRemaining: 95, 
      owner: 'Technician Leyla', 
      section: 'Biochemistry', 
      dueAt: new Date(Date.now() + 95 * 60000),
      notes: 'Routine diabetic follow-up. Reviewing historical glucose trend.',
      attachments: []
    },
  ]);

  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [isProcessing, setIsProcessing] = useState<string | null>(null);
  const [confirmingTask, setConfirmingTask] = useState<{ id: string; action: TaskStatus } | null>(null);
  
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [syncQueue, setSyncQueue] = useState<{ taskId: string; action: TaskStatus; timestamp: number }[]>([]);
  const [activeWorkId, setActiveWorkId] = useState<string | null>(null);
  const [criticalAlert, setCriticalAlert] = useState<{ message: string; severity: 'high' | 'critical' } | null>(null);

  // Keyboard Shortcuts (UX Requirement)
  const handleKeyPress = useCallback((e: KeyboardEvent) => {
    if (isResultEntryOpen) return;
    
    // Alt + C: Claim first unassigned urgent task
    if (e.altKey && e.key === 'c') {
      const firstUnassigned = tasks.find(t => t.status === 'unassigned');
      if (firstUnassigned) handleClaim(firstUnassigned.id);
    }
    // Alt + S: Scan (Simulated)
    if (e.altKey && e.key === 's') {
      toast.info('Barcode Scanner Ready...', { icon: '🔍' });
    }
  }, [tasks, isResultEntryOpen]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);

  useEffect(() => {
    const handleOnline = () => {
      setIsOffline(false);
      toast.success('System back online. Syncing changes...');
    };
    const handleOffline = () => {
      setIsOffline(true);
      toast.error('Connection lost. Entering offline mode.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    const savedWork = localStorage.getItem('active_lab_work');
    if (savedWork) {
      const { taskId } = JSON.parse(savedWork);
      setActiveWorkId(taskId);
      toast('Resuming interrupted work session', { icon: '🔄' });
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    if (!isOffline && syncQueue.length > 0) {
      const processQueue = async () => {
        for (const item of syncQueue) {
          await new Promise(resolve => setTimeout(resolve, 500));
          setTasks(prev => prev.map(t => t.id === item.taskId ? { ...t, status: item.action } : t));
        }
        setSyncQueue([]);
        toast.success('Offline changes synchronized successfully');
      };
      processQueue();
    }
  }, [isOffline, syncQueue]);

  const handleClaim = (taskId: string) => {
    setIsProcessing(taskId);
    setTimeout(() => {
      setTasks(prev => prev.map(task => 
        task.id === taskId ? { ...task, status: 'claimed', owner: profile?.name || 'You' } : task
      ));
      setIsProcessing(null);
      toast.success('Task Claimed', {
        description: `Sample ${tasks.find(t => t.id === taskId)?.sampleId} assigned to your queue`
      });
    }, 600);
  };

  const updateTaskStatus = (taskId: string, newStatus: TaskStatus) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    if (newStatus === 'completed') {
      setConfirmingTask({ id: taskId, action: newStatus });
      return;
    }

    executeStatusUpdate(taskId, newStatus);
  };

  const executeStatusUpdate = (taskId: string, newStatus: TaskStatus) => {
    if (isOffline) {
      setSyncQueue(prev => [...prev, { taskId, action: newStatus, timestamp: Date.now() }]);
      toast('Change queued for synchronization', { icon: '📥' });
      setConfirmingTask(null);
      return;
    }

    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, status: newStatus } : task
    ));
    setConfirmingTask(null);
    toast.success(`Task status updated to ${newStatus}`);
    
    if (activeWorkId === taskId) {
      localStorage.removeItem('active_lab_work');
      setActiveWorkId(null);
    }
  };

  const startWork = (task: LabTask) => {
    setIsResultEntryOpen(task);
    setActiveWorkId(task.id);
    localStorage.setItem('active_lab_work', JSON.stringify({ taskId: task.id, startTime: Date.now() }));
    toast.info('Starting intensive sample evaluation...');
  };

  const handleResultsSave = (results: any) => {
    if (isResultEntryOpen) {
      updateTaskStatus(isResultEntryOpen.id, 'review');
      setIsResultEntryOpen(null);
    }
  };

  const toggleSelect = (taskId: string) => {
    const newSelected = new Set(selectedTasks);
    if (newSelected.has(taskId)) newSelected.delete(taskId);
    else newSelected.add(taskId);
    setSelectedTasks(newSelected);
  };

  const handleBulkClaim = () => {
    const taskIds = Array.from(selectedTasks);
    setTasks(prev => prev.map(task => 
      taskIds.includes(task.id) && task.status === 'unassigned'
        ? { ...task, status: 'claimed', owner: profile?.name || 'You' } 
        : task
    ));
    setSelectedTasks(new Set());
    toast.success(`Claimed ${taskIds.length} tasks`);
  };

  const sections = ['All', 'Hematology', 'Biochemistry', 'Serology', 'Microbiology'];

  if (isResultEntryOpen) {
    return (
      <div className="p-8">
        <ResultEntryUI 
          taskId={isResultEntryOpen.id}
          sampleId={isResultEntryOpen.sampleId}
          patientName={isResultEntryOpen.patientName}
          testName={isResultEntryOpen.testName}
          onSave={handleResultsSave}
          onCancel={() => setIsResultEntryOpen(null)}
        />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 min-h-screen bg-slate-50/20">
      {/* Connection Status & Critical Alerts */}
      <AnimatePresence>
        {isOffline && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-amber-600 text-white px-6 py-3 rounded-2xl flex items-center justify-between shadow-xl shadow-amber-900/20 mb-4"
          >
            <div className="flex items-center gap-3 text-left">
              <WifiOff size={18} className="shrink-0" />
              <div className="flex flex-col">
                <span className="text-xs font-black uppercase tracking-[0.2em] leading-none">Offline Mode Active</span>
                <span className="text-[9px] font-bold opacity-80 mt-1">{syncQueue.length} changes queued for synchronization</span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex gap-1">
                {[1,2,3].map(i => (
                  <motion.div 
                    key={i}
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ repeat: Infinity, duration: 1.5, delay: i * 0.2 }}
                    className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_8px_white]"
                  />
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {criticalAlert && (
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-red-600 text-white p-6 rounded-[2rem] shadow-2xl shadow-red-900/30 flex items-center justify-between mb-4 ring-4 ring-red-500/20 outline-none"
          >
            <div className="flex items-center gap-4 text-left">
              <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center animate-pulse shrink-0">
                <AlertTriangle size={24} />
              </div>
              <div>
                <h4 className="text-sm font-black uppercase tracking-tight">Critical Interrupt</h4>
                <p className="text-[10px] font-bold text-red-100">{criticalAlert.message}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setCriticalAlert(null)}
                className="px-6 py-3 bg-white text-red-600 rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-slate-100 transition-all shrink-0 shadow-lg"
              >
                Acknowledge
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Production Control Header */}
      <div className="bg-slate-900 rounded-[3rem] p-10 text-white flex flex-col lg:flex-row items-center justify-between gap-8 shadow-2xl relative">
         <div className="absolute top-0 right-0 p-12 opacity-[0.03] pointer-events-none scale-150">
            <Microscope size={240} />
         </div>

         <div className="relative z-10 flex items-center gap-8">
            <div className="w-20 h-20 bg-indigo-600 rounded-[2rem] flex items-center justify-center text-white shadow-2xl shadow-indigo-500/20 rotate-3 group-hover:rotate-0 transition-transform">
              <ActivityIcon size={40} className="animate-pulse" />
            </div>
            <div>
               <h1 className="text-4xl font-black tracking-tight leading-none mb-2">Work Intelligence <span className="text-indigo-400">Queue</span></h1>
               <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                     <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                     <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Active Neural Link</span>
                  </div>
                  <div className="w-1 h-1 rounded-full bg-white/20" />
                  <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">{profile?.name || 'Operator'} Authorized</span>
                  
                  {/* State Control Simulation */}
                  <div className="flex bg-white/10 p-1 rounded-xl border border-white/5 shrink-0 gap-1 ml-2 scale-90 translate-y-[-1px]">
                    <button 
                      onClick={() => setIsOffline(!isOffline)}
                      className={cn("p-1.5 rounded-lg transition-all", isOffline ? "bg-emerald-500 text-white shadow-lg" : "text-white/40 hover:bg-white/10")}
                      title="Simulate Network Drop"
                    >
                      {isOffline ? <Wifi size={12} /> : <WifiOff size={12} />}
                    </button>
                    <button 
                      onClick={() => setCriticalAlert({ message: 'Major analyzer calibration error detected. Manual routing required for critical samples.', severity: 'critical' })}
                      className="p-1.5 text-white/40 hover:bg-white/10 hover:text-white rounded-lg transition-all"
                      title="Simulate Critical Alert"
                    >
                      <AlertTriangle size={12} />
                    </button>
                  </div>
               </div>
            </div>
         </div>

         <div className="relative z-10 flex bg-white/5 p-1.5 rounded-2xl border border-white/10">
            {(['technician', 'pathologist', 'manager'] as const).map(mode => (
              <button 
                key={mode}
                onClick={() => setViewMode(mode)}
                className={cn(
                  "px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
                  viewMode === mode ? "bg-white text-slate-900 shadow-md" : "text-white/40 hover:text-white/80"
                )}
              >
                {mode}
              </button>
            ))}
         </div>

         <div className="relative z-10 flex gap-4">
            <div className="text-right">
               <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Total Throughput</p>
               <p className="text-2xl font-black">42 Samples/hr</p>
            </div>
            <div className="w-px h-10 bg-white/10 hidden lg:block" />
            <div className="text-right">
               <p className="text-[10px] font-black uppercase tracking-widest text-red-500">{t.stat} Alert</p>
               <p className="text-2xl font-black text-red-500">2 Pending</p>
            </div>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
         <div className="lg:col-span-3 space-y-6">
            <div className="bg-white rounded-[2rem] border border-slate-200 p-8 shadow-sm">
               <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-6">Queue Filtering</h3>
               <div className="space-y-2">
                  {sections.map(section => (
                    <button 
                      key={section}
                      onClick={() => setFilterSection(section)}
                      className={cn(
                        "w-full text-right p-4 rounded-2xl text-xs font-bold transition-all border",
                        filterSection === section ? "bg-indigo-50 border-indigo-200 text-indigo-600 shadow-sm" : "bg-slate-50 border-transparent text-slate-500 hover:bg-slate-100"
                      )}
                    >
                      {section}
                    </button>
                  ))}
               </div>
            </div>

            <div className="bg-indigo-600 rounded-[2rem] p-8 text-white shadow-xl shadow-indigo-100">
               <h3 className="text-sm font-black mb-6 flex items-center gap-2">
                 <Zap size={18} className="text-amber-400 fill-amber-400" /> System Automation
               </h3>
               <div className="space-y-4">
                  <div className="flex justify-between items-center text-xs">
                     <span className="opacity-60 font-medium">Instrumentation Link</span>
                     <span className="font-bold text-emerald-400 uppercase">Connected</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                     <span className="opacity-60 font-medium">QC Integration</span>
                     <span className="font-bold text-emerald-400 uppercase">Passed</span>
                  </div>
               </div>
               <button className="w-full mt-8 py-4 bg-white/10 border border-white/20 rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-white/20 transition-all">
                  Device Monitoring
               </button>
            </div>
         </div>

         <div className="lg:col-span-9 space-y-6">
            <div className="flex items-center justify-between px-2 mt-4">
               <div className="flex items-center gap-4">
                  <h2 className="text-2xl font-black text-slate-900 tracking-tight uppercase">Active Execution</h2>
                  <div className="flex items-center gap-2 px-3 py-1 bg-indigo-600 text-white rounded-full shadow-lg shadow-indigo-100">
                     <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                     <span className="text-[10px] font-black tracking-widest">{tasks.length} Samples</span>
                  </div>
               </div>
               
               <AnimatePresence>
                 {selectedTasks.size > 0 && (
                   <motion.div 
                     initial={{ opacity: 0, x: 20, scale: 0.9 }}
                     animate={{ opacity: 1, x: 0, scale: 1 }}
                     exit={{ opacity: 0, x: 20, scale: 0.9 }}
                     className="flex items-center gap-4 bg-white border border-indigo-100 p-2 pl-6 rounded-[2rem] shadow-2xl"
                   >
                      <span className="text-[10px] font-black uppercase text-indigo-600 tracking-widest">{selectedTasks.size} Selected for Batch</span>
                      <button 
                        onClick={handleBulkClaim}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest hover:bg-slate-900 shadow-lg shadow-indigo-100 transition-all active:scale-95"
                      >
                        Claim Batch
                      </button>
                   </motion.div>
                 )}
               </AnimatePresence>
               <div className="flex gap-2">
                  <div className="relative">
                     <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300" size={14} />
                     <input type="text" placeholder="Search task..." className="bg-white border border-slate-200 rounded-xl py-2 pl-4 pr-10 text-xs focus:ring-4 focus:ring-indigo-100 transition-all outline-none" />
                  </div>
                  <div className="flex bg-white border border-slate-200 p-1 rounded-xl">
                     <button 
                       onClick={() => setSortBy('priority')}
                       className={cn(
                         "px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all",
                         sortBy === 'priority' ? "bg-slate-900 text-white shadow-sm" : "text-slate-400 hover:text-slate-600"
                       )}
                     >
                       Priority
                     </button>
                     <button 
                       onClick={() => setSortBy('due')}
                       className={cn(
                         "px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all",
                         sortBy === 'due' ? "bg-slate-900 text-white shadow-sm" : "text-slate-400 hover:text-slate-600"
                       )}
                     >
                       Due
                     </button>
                  </div>
                  <button className="p-2.5 bg-white border border-slate-200 rounded-xl hover:text-indigo-600 transition-all">
                     <Filter size={18} />
                  </button>
               </div>
            </div>

            <div className="space-y-4">
               <AnimatePresence mode="popLayout">
                  {tasks
                    .filter(t => filterSection === 'All' || t.section === filterSection)
                    .sort((a, b) => {
                       if (sortBy === 'priority') {
                         const priorityMap = { stat: 0, urgent: 1, routine: 2 };
                         return priorityMap[a.priority] - priorityMap[b.priority];
                       }
                       return a.dueAt.getTime() - b.dueAt.getTime();
                    })
                    .map((task, i) => (
                    <motion.div 
                      layout
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ delay: i * 0.05 }}
                      key={task.id}
                      onClick={() => setExpandedTaskId(expandedTaskId === task.id ? null : task.id)}
                      className={cn(
                        "bg-white rounded-[3rem] border border-slate-200 p-8 shadow-sm group hover:border-indigo-600 transition-all cursor-pointer relative overflow-hidden",
                        task.priority === 'stat' && "border-l-[12px] border-l-red-500",
                        selectedTasks.has(task.id) && "ring-2 ring-indigo-600 ring-offset-4 bg-indigo-50/10",
                        expandedTaskId === task.id && "shadow-xl shadow-indigo-100 border-indigo-400"
                      )}
                    >
                       <div className="absolute top-4 right-4 z-20">
                          <input 
                            type="checkbox" 
                            checked={selectedTasks.has(task.id)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleSelect(task.id);
                            }}
                            className="w-5 h-5 rounded-lg border-2 border-slate-200 checked:bg-indigo-600 checked:border-transparent transition-all cursor-pointer"
                          />
                       </div>
                       <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
                          <div className="md:col-span-4 flex items-center gap-6">
                             <div className={cn(
                               "w-20 h-20 rounded-[2rem] flex flex-col items-center justify-center text-white shadow-2xl transition-all group-hover:scale-105 group-hover:rotate-2",
                               task.priority === 'stat' ? 'bg-red-600 shadow-red-200' :
                               task.priority === 'urgent' ? 'bg-amber-500 shadow-amber-200' : 'bg-slate-900 shadow-slate-200'
                             )}>
                                <span className="text-[8px] font-black uppercase mb-1 tracking-tighter opacity-80">{task.priority}</span>
                                {task.priority === 'stat' ? <AlertCircle size={32} className="animate-pulse" /> : <PlayCircle size={32} className="group-hover:fill-white/20" />}
                             </div>
                             <div>
                                <div className="flex items-center gap-2 mb-1">
                                   <h4 className="text-2xl font-black text-slate-900 uppercase tracking-tighter">{task.sampleId}</h4>
                                   {task.status === 'in-progress' && (
                                     <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                                   )}
                                </div>
                                <p className="text-[10px] text-indigo-600 font-black uppercase tracking-[0.2em]">{task.testName}</p>
                             </div>
                          </div>

                          <div className="md:col-span-4 flex flex-col gap-4 border-l border-r border-slate-100 px-8">
                                 <div className="space-y-1.5">
                                    <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-widest">
                                       <span className="text-slate-400">SLA {t.progress || 'Progress'}</span>
                                       <span className={cn(
                                          task.timeRemaining < 10 || task.priority === 'stat' ? 'text-red-500 font-black' : 
                                          task.timeRemaining < 30 || task.priority === 'urgent' ? 'text-amber-500' : 
                                          'text-emerald-600'
                                       )}>{task.timeRemaining}m {t.remaining || 'Left'}</span>
                                    </div>
                                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden relative">
                                       <motion.div 
                                          initial={{ width: 0 }}
                                          animate={{ width: `${Math.max(0, Math.min(100, (task.timeRemaining / task.slaMinutes) * 100))}%` }}
                                          className={cn(
                                             "h-full rounded-full transition-all duration-1000",
                                             (task.timeRemaining / task.slaMinutes) < 0.2 || task.priority === 'stat' ? 'bg-red-500' : 
                                             (task.timeRemaining / task.slaMinutes) < 0.5 || task.priority === 'urgent' ? 'bg-amber-500' : 
                                             'bg-emerald-500'
                                          )} 
                                       />
                                    </div>
                                 </div>
                             <div className="flex items-center gap-4">
                                <div className="flex items-center gap-1.5">
                                   <Users size={12} className="text-slate-300" />
                                   <span className="text-[10px] font-bold text-slate-500 uppercase">{task.section}</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                   <User size={12} className="text-slate-300" />
                                   <span className="text-[10px] font-bold text-slate-500 uppercase">{task.owner || 'Unassigned'}</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                   <Clock size={12} className="text-slate-300" />
                                   <span className="text-[10px] font-bold text-slate-500 uppercase">
                                      Due: {task.dueAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                   </span>
                                </div>
                             </div>
                          </div>

                          <div className="md:col-span-4 flex items-center justify-end gap-4 pl-8">
                             {task.status === 'unassigned' ? (
                               <button 
                                 onClick={(e) => {
                                   e.stopPropagation();
                                   handleClaim(task.id);
                                 }}
                                 disabled={isProcessing === task.id}
                                 className="flex-1 py-5 bg-indigo-600 text-white rounded-3xl font-black text-[10px] uppercase tracking-widest shadow-2xl shadow-indigo-100 hover:bg-slate-900 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2 group/btn"
                               >
                                 {isProcessing === task.id ? (
                                   <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                 ) : (
                                   <>
                                     Claim Task
                                     <Zap size={14} className="group-hover/btn:fill-amber-400 group-hover/btn:text-amber-400 transition-all" />
                                   </>
                                 )}
                               </button>
                             ) : task.status === 'claimed' || task.status === 'in-progress' ? (
                               <button 
                                 onClick={(e) => {
                                   e.stopPropagation();
                                   startWork(task);
                                 }}
                                 className="flex-1 py-5 bg-slate-900 text-white rounded-3xl font-black text-[10px] uppercase tracking-widest shadow-2xl shadow-slate-200 hover:bg-black hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
                               >
                                 Result Intelligence
                                 <Terminal size={14} className="text-indigo-400" />
                               </button>
                             ) : task.status === 'review' ? (
                               <button 
                                 onClick={(e) => {
                                   e.stopPropagation();
                                   updateTaskStatus(task.id, 'completed');
                                 }}
                                 className="flex-1 py-5 bg-emerald-600 text-white rounded-3xl font-black text-[10px] uppercase tracking-widest shadow-2xl shadow-emerald-100 hover:bg-emerald-700 hover:scale-[1.02] transition-all flex items-center justify-center gap-2">
                                 Validate [Digital Twin]
                                 <Shield size={14} />
                               </button>
                             ) : (
                               <div className="flex-1 py-5 bg-slate-100 text-slate-400 rounded-3xl font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-2">
                                 Completed
                                 <CheckCircle2 size={14} />
                               </div>
                             )}
                             <button 
                               onClick={(e) => e.stopPropagation()}
                               className="p-5 border border-slate-200 rounded-3xl hover:border-indigo-600 hover:text-indigo-600 transition-all hover:bg-indigo-50"
                             >
                                <MoreVertical size={20} />
                             </button>
                          </div>
                       </div>

                       {/* Expansion Panel */}
                       <AnimatePresence>
                         {expandedTaskId === task.id && (
                           <motion.div
                             initial={{ height: 0, opacity: 0 }}
                             animate={{ height: 'auto', opacity: 1 }}
                             exit={{ height: 0, opacity: 0 }}
                             className="overflow-hidden"
                           >
                             <div className="pt-8 mt-8 border-t border-slate-100 grid grid-cols-1 lg:grid-cols-3 gap-8">
                                <div className="space-y-4">
                                   <div className="p-6 bg-slate-50 rounded-3xl">
                                      <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-3 block">Patient Digital ID</span>
                                      <div className="flex items-center gap-3">
                                         <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-sm">
                                            <User size={18} className="text-indigo-600" />
                                         </div>
                                         <span className="text-lg font-black text-slate-900 tracking-tight">{task.patientId}</span>
                                      </div>
                                   </div>
                                   <div className="p-6 bg-slate-50 rounded-3xl">
                                      <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-3 block">Clinical Logic Group</span>
                                      <span className="text-xs font-bold text-slate-700">{task.section} Analytics Node-42</span>
                                   </div>
                                </div>
                                
                                <div className="lg:col-span-2 space-y-4">
                                   <div className="p-6 bg-white border border-slate-100 rounded-[2rem] shadow-sm">
                                      <div className="flex items-center gap-2 mb-4">
                                         <ClipboardList size={16} className="text-indigo-600" />
                                         <span className="text-[10px] font-black uppercase text-slate-900 tracking-widest">Clinical Handover Notes</span>
                                      </div>
                                      <p className="text-sm font-medium text-slate-600 leading-relaxed italic">
                                         "{task.notes || 'No clinical notes provided for this sample phase.'}"
                                      </p>
                                   </div>

                                   {task.attachments && task.attachments.length > 0 && (
                                     <div className="flex items-center gap-3 overflow-x-auto no-scrollbar pb-2">
                                        {task.attachments.map((file, idx) => (
                                          <div key={idx} className="flex-none flex items-center gap-2 px-4 py-3 bg-indigo-50 text-indigo-700 rounded-2xl border border-indigo-100 group/file cursor-pointer hover:bg-slate-900 hover:text-white transition-all">
                                             <ImageIcon size={14} />
                                             <span className="text-[10px] font-black truncate max-w-[120px]">{file}</span>
                                          </div>
                                        ))}
                                     </div>
                                   )}
                                </div>
                             </div>
                           </motion.div>
                         )}
                       </AnimatePresence>
                    </motion.div>
                  ))}
               </AnimatePresence>
            </div>
         </div>
      </div>

      {/* Action Confirmation Modal */}
      <AnimatePresence>
        {confirmingTask && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               exit={{ opacity: 0 }}
               onClick={() => setConfirmingTask(null)}
               className="absolute inset-0 bg-slate-900/60 backdrop-blur-md"
            />
            <motion.div 
               initial={{ scale: 0.9, opacity: 0, y: 20 }}
               animate={{ scale: 1, opacity: 1, y: 0 }}
               exit={{ scale: 0.9, opacity: 0, y: 20 }}
               className="relative bg-white w-full max-w-lg rounded-[3rem] p-12 shadow-2xl"
            >
               {(() => {
                 const task = tasks.find(t => t.id === confirmingTask.id)!;
                 const isHighRisk = task.priority === 'stat' || task.priority === 'urgent';
                 
                 return (
                   <div className="text-center">
                     <div className={cn(
                       "w-24 h-24 rounded-[2.5rem] flex items-center justify-center mx-auto mb-8 shadow-2xl",
                       isHighRisk ? "bg-red-50 text-red-600 shadow-red-100" : "bg-indigo-50 text-indigo-600 shadow-indigo-100"
                     )}>
                        <Shield size={48} className={cn(isHighRisk && "animate-pulse")} />
                     </div>
                     
                     <h3 className="text-2xl font-black text-slate-900 tracking-tight mb-4 uppercase">
                        Confirm Clinical Action
                     </h3>
                     
                     <p className="text-slate-500 font-medium mb-8 text-sm">
                        You are about to mark sample <span className="font-bold text-slate-900">#{task.sampleId}</span> ({task.testName}) as <span className="font-bold text-indigo-600 uppercase">{confirmingTask.action}</span>. This action is irreversible in the current cycle.
                     </p>

                     {isHighRisk && (
                       <div className="mb-8 p-6 bg-red-50 border border-red-100 rounded-[2rem] flex items-center gap-4 text-left">
                          <AlertCircle className="text-red-600 shrink-0" size={24} />
                          <div>
                             <p className="text-[10px] font-black text-red-600 uppercase tracking-widest mb-1 font-sans">High Priority Directive</p>
                             <p className="text-xs font-bold text-red-900 leading-relaxed">STAT samples require double-verification of all calibrated values before sign-off.</p>
                          </div>
                       </div>
                     )}

                     <div className="flex gap-4">
                        <button 
                           onClick={() => setConfirmingTask(null)}
                           className="flex-1 py-5 bg-slate-100 text-slate-500 rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-slate-200 transition-all"
                        >
                           Cancel
                        </button>
                        <button 
                           onClick={() => executeStatusUpdate(confirmingTask.id, confirmingTask.action)}
                           className={cn(
                             "flex-2 py-5 rounded-2xl font-black text-[10px] uppercase tracking-widest text-white shadow-2xl transition-all hover:scale-[1.02] active:scale-95",
                             isHighRisk ? "bg-red-600 shadow-red-200 hover:bg-red-700" : "bg-indigo-600 shadow-indigo-200 hover:bg-slate-900"
                           )}
                        >
                           Confirm & Sign Result
                        </button>
                     </div>
                   </div>
                 );
               })()}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
