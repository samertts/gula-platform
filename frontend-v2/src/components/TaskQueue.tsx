import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  ClipboardList, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  UserPlus, 
  ArrowRight,
  Filter,
  Check,
  Activity as ActivityIcon,
  Square,
  CheckSquare,
  X,
  ChevronDown,
  MoreVertical,
  RotateCcw,
  ExternalLink,
  FileText,
  Link,
  Info,
  Calendar
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Task } from '../types/domain';
import { cn } from '../lib/utils';
import { useState, useRef, useEffect } from 'react';

interface TaskQueueProps {
  tasks: Task[];
  onAssign?: (taskId: string) => void;
  onUpdateStatus?: (taskId: string, status: Task['status']) => void;
  onBulkAction?: (action: 'assign' | 'complete' | 'hold' | 'process', taskIds: string[]) => void;
}

export const TaskQueue: React.FC<TaskQueueProps> = ({ tasks, onAssign, onUpdateStatus, onBulkAction }) => {
  const { t } = useLanguage();
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);
  const [showBulkDropdown, setShowBulkDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowBulkDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleSelect = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleExpand = (id: string) => {
    setExpandedTaskId(expandedTaskId === id ? null : id);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === tasks.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(tasks.map(t => t.id)));
    }
  };

  const handleBulkAction = (action: 'assign' | 'complete' | 'hold' | 'process') => {
    onBulkAction?.(action, Array.from(selectedIds));
    setSelectedIds(new Set());
  };

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'critical': return 'bg-red-50 text-red-600 border-red-100';
      case 'high': return 'bg-orange-50 text-orange-600 border-orange-100';
      case 'medium': return 'bg-blue-50 text-blue-600 border-blue-100';
      default: return 'bg-slate-50 text-slate-600 border-slate-100';
    }
  };

  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="text-green-500" size={18} />;
      case 'in_progress': return <Clock className="text-blue-500 animate-pulse" size={18} />;
      case 'on_hold': return <Clock className="text-amber-500" size={18} />;
      default: return <ClipboardList className="text-slate-400" size={18} />;
    }
  };

  return (
    <div className="space-y-4 relative">
      {/* Bulk Action Bar */}
      <AnimatePresence>
        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="sticky top-2 z-30 mb-4 p-4 bg-slate-900 text-white rounded-[2rem] shadow-2xl flex items-center justify-between gap-6 overflow-hidden border border-white/10"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-indigo-600 rounded-2xl flex items-center justify-center text-white font-black shadow-lg shadow-indigo-900/40">
                {selectedIds.size}
              </div>
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Tasks Selected</p>
                <div className="flex items-center gap-2">
                   <button 
                    onClick={() => setSelectedIds(new Set())}
                    className="text-[9px] font-black uppercase tracking-widest text-white/40 hover:text-rose-400 transition-colors"
                  >
                    Clear Selection
                  </button>
                  <span className="w-1 h-1 bg-white/10 rounded-full" />
                  <button 
                    onClick={toggleSelectAll}
                    className="text-[9px] font-black uppercase tracking-widest text-white/40 hover:text-indigo-400 transition-colors"
                  >
                    {selectedIds.size === tasks.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 relative" ref={dropdownRef}>
              <button 
                onClick={() => setShowBulkDropdown(!showBulkDropdown)}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-2 shadow-lg shadow-indigo-900/40 min-w-[160px] justify-between"
              >
                <span>Batch Actions</span>
                <ChevronDown size={14} className={cn("transition-transform", showBulkDropdown && "rotate-180")} />
              </button>

              <AnimatePresence>
                {showBulkDropdown && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -10 }}
                    className="absolute bottom-full right-0 mb-3 w-56 bg-slate-800 border border-white/10 rounded-2xl shadow-2xl overflow-hidden z-40 backdrop-blur-xl"
                  >
                    {[
                      { id: 'assign', label: 'Assign to Me', icon: UserPlus, color: 'text-indigo-400', hover: 'hover:bg-indigo-500/10' },
                      { id: 'complete', label: 'Mark as Reviewed', icon: CheckCircle2, color: 'text-emerald-400', hover: 'hover:bg-emerald-500/10' },
                      { id: 'hold', label: 'Put on Hold', icon: Clock, color: 'text-amber-400', hover: 'hover:bg-amber-500/10' },
                      { id: 'process', label: 'Push to Analysis', icon: ActivityIcon, color: 'text-rose-400', hover: 'hover:bg-rose-500/10' },
                    ].map((action) => (
                      <button
                        key={action.id}
                        onClick={() => {
                          handleBulkAction(action.id as any);
                          setShowBulkDropdown(false);
                        }}
                        className={cn(
                          "w-full px-5 py-3.5 flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-slate-300 transition-all border-b border-white/5 last:border-0",
                          action.hover
                        )}
                      >
                        <action.icon size={16} className={action.color} />
                        {action.label}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button 
            onClick={toggleSelectAll}
            className={cn(
              "w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all",
              selectedIds.size === tasks.length && tasks.length > 0
                ? "bg-indigo-600 border-indigo-600 text-white"
                : "border-slate-200 text-slate-300 hover:border-indigo-400"
            )}
          >
            {selectedIds.size === tasks.length && tasks.length > 0 ? <Check size={14} /> : <div className="w-2 h-2 bg-slate-100 rounded-sm" />}
          </button>
          <h2 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-3 uppercase">
            <ClipboardList className="text-indigo-600" />
            Operational Execution Queue
          </h2>
        </div>
        <div className="flex gap-2">
          <button className="p-2 border border-slate-100 rounded-xl hover:bg-slate-50 transition-all text-slate-400">
             <Filter size={18} />
          </button>
        </div>
      </div>

      <div className="grid gap-3">
        <AnimatePresence mode="popLayout">
          {tasks.map((task) => (
            <motion.div
              layout
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -20 }}
              key={task.id}
              onClick={() => toggleExpand(task.id)}
              className={cn(
                "bg-white border rounded-[2rem] hover:shadow-xl transition-all group relative overflow-hidden cursor-pointer",
                selectedIds.has(task.id) ? "border-indigo-600 shadow-indigo-100/50 bg-indigo-50/20" : "border-slate-100 hover:border-indigo-100",
                expandedTaskId === task.id && "shadow-2xl shadow-indigo-100 ring-2 ring-indigo-600 ring-offset-4"
              )}
            >
              <div className="p-5">
                <div className="flex items-center justify-between gap-6">
                  <div className="flex items-center gap-4 flex-1">
                    <button 
                      onClick={(e) => toggleSelect(e, task.id)}
                      className={cn(
                        "w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all shrink-0",
                        selectedIds.has(task.id)
                          ? "bg-indigo-600 border-indigo-600 text-white"
                          : "border-slate-200 text-slate-300 hover:border-indigo-400"
                      )}
                    >
                      {selectedIds.has(task.id) ? <Check size={14} /> : <div className="w-2 h-2 bg-slate-100 rounded-sm" />}
                    </button>

                    <div className={cn(
                      "p-3 rounded-2xl shrink-0 transition-colors", 
                      task.status === 'on_hold' ? "bg-amber-100 text-amber-600 shadow-inner" : getPriorityColor(task.priority)
                    )}>
                      {getStatusIcon(task.status)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={cn("text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-md border", getPriorityColor(task.priority))}>
                            {task.priority}
                        </span>
                        {task.status === 'on_hold' && (
                          <span className="text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded-md bg-amber-600 text-white animate-pulse">
                            On Hold
                          </span>
                        )}
                        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">#{task.id.slice(-6)}</span>
                      </div>
                      <h3 className={cn(
                        "text-sm font-bold transition-colors",
                        task.status === 'on_hold' ? "text-slate-400" : "text-slate-900"
                      )}>{task.title}</h3>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-[10px] text-slate-400 font-medium">{t.device}: {task.relatedResourceId}</span>
                        <span className="w-1 h-1 bg-slate-200 rounded-full" />
                        <span className="text-[10px] text-slate-400 font-medium tracking-tight">
                          <Clock size={10} className="inline mr-1 mb-0.5" />
                          SLA: {new Date(task.slaDeadline).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {!task.assignedTo ? (
                      <div className="flex gap-2">
                        <button 
                          onClick={(e) => { e.stopPropagation(); onAssign?.(task.id); }}
                          className="px-4 py-2 bg-indigo-600 text-white text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-indigo-700 transition-all flex items-center gap-2"
                        >
                          <UserPlus size={14} /> {t.assignTechnician}
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); onUpdateStatus?.(task.id, 'on_hold'); }}
                          className="p-2 border border-slate-100 text-slate-400 rounded-xl hover:bg-slate-50 transition-all"
                          title="Put on Hold"
                        >
                          <Clock size={16} />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-4">
                        <div className="flex -space-x-2">
                            <div className="w-8 h-8 rounded-full bg-slate-100 border-2 border-white flex items-center justify-center text-[10px] font-bold text-slate-600 uppercase">
                              {task.assignedTo.slice(0, 2)}
                            </div>
                        </div>
                        
                        {task.status !== 'completed' && (
                          <div className="flex gap-2">
                              {task.status === 'on_hold' ? (
                                <button 
                                  onClick={(e) => { e.stopPropagation(); onUpdateStatus?.(task.id, 'in_progress'); }}
                                  className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-emerald-500 shadow-lg shadow-emerald-100 transition-all flex items-center gap-2"
                                >
                                  <ActivityIcon size={14} /> Resume Process
                                </button>
                              ) : (
                                <>
                                  <button 
                                    onClick={(e) => { e.stopPropagation(); onUpdateStatus?.(task.id, 'on_hold'); }}
                                    className="px-3 py-1.5 bg-amber-50 text-amber-600 border border-amber-100 rounded-lg text-[8px] font-black uppercase tracking-widest hover:bg-amber-100 transition-all flex items-center gap-1.5"
                                  >
                                    <Clock size={12} /> Hold
                                  </button>
                                  {task.status === 'in_progress' ? (
                                    <button 
                                      onClick={(e) => { e.stopPropagation(); onUpdateStatus?.(task.id, 'completed'); }}
                                      className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-[8px] font-black uppercase tracking-widest hover:bg-indigo-500 shadow-lg shadow-indigo-100 transition-all"
                                    >
                                      Finalize
                                    </button>
                                  ) : (
                                    <button 
                                      onClick={(e) => { e.stopPropagation(); onUpdateStatus?.(task.id, 'in_progress'); }}
                                      className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-[8px] font-black uppercase tracking-widest hover:bg-emerald-500 shadow-lg shadow-emerald-100 transition-all flex items-center gap-2"
                                    >
                                      <ActivityIcon size={10} /> Start
                                    </button>
                                  )}
                                </>
                              )}
                          </div>
                        )}
                      </div>
                    )}
                    <button className={cn(
                      "p-2 text-slate-300 transition-transform",
                      expandedTaskId === task.id && "rotate-180 text-indigo-600"
                    )}>
                      <ChevronDown size={20} />
                    </button>
                  </div>
                </div>

                <AnimatePresence>
                  {expandedTaskId === task.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="pt-8 mt-6 border-t border-slate-50 grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-6">
                           <div>
                              <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
                                <Info size={12} /> Administrative Tracking
                              </h4>
                              <div className="grid grid-cols-2 gap-3">
                                 <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100">
                                    <p className="text-[8px] font-black uppercase text-slate-400 mb-1">Entity Origin</p>
                                    <p className="text-xs font-bold text-slate-900">{task.entityId}</p>
                                 </div>
                                 <div className="p-3 bg-slate-50 rounded-2xl border border-slate-100">
                                    <p className="text-[8px] font-black uppercase text-slate-400 mb-1">Related Resource</p>
                                    <p className="text-xs font-bold text-slate-900">{task.relatedResourceId}</p>
                                 </div>
                              </div>
                           </div>

                           <div>
                              <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
                                <FileText size={12} /> Clinical Context & Notes
                              </h4>
                              <div className="p-4 bg-indigo-50/30 rounded-[1.5rem] border border-indigo-100/50">
                                 <p className="text-xs text-slate-600 leading-relaxed">
                                    System generated task for {task.type.replace('_', ' ')}. 
                                    Patient verification required prior to finalizing state. 
                                    Ensure cold chain integrity for sample {task.relatedResourceId}.
                                 </p>
                              </div>
                           </div>
                        </div>

                        <div className="space-y-6">
                           <div>
                              <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
                                <Calendar size={12} /> Lifecycle History
                              </h4>
                              <div className="space-y-3">
                                 {[
                                   { label: 'Task Generated', time: task.createdAt, icon: ActivityIcon },
                                   { label: 'Last Status Update', time: task.updatedAt, icon: Clock },
                                 ].map((event, idx) => (
                                   <div key={idx} className="flex items-center gap-3">
                                      <div className="w-6 h-6 bg-white border border-slate-100 rounded-full flex items-center justify-center text-slate-400">
                                         <event.icon size={10} />
                                      </div>
                                      <div>
                                         <p className="text-[10px] font-bold text-slate-800">{event.label}</p>
                                         <p className="text-[9px] text-slate-400">{new Date(event.time).toLocaleString()}</p>
                                      </div>
                                   </div>
                                 ))}
                              </div>
                           </div>

                           <div>
                              <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
                                <Link size={12} /> Digital Artifacts
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                 {['VerificationDoc.pdf', 'LabProtocol_v2.docx'].map((file, idx) => (
                                   <div key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-xl text-[9px] font-bold text-slate-600 hover:bg-indigo-600 hover:text-white transition-all cursor-pointer border border-slate-200">
                                      <FileText size={10} /> {file}
                                   </div>
                                 ))}
                              </div>
                           </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {tasks.length === 0 && (
          <div className="py-20 text-center space-y-4 bg-slate-50/50 rounded-[40px] border border-dashed border-slate-200">
             <ClipboardList className="mx-auto text-slate-300" size={48} />
             <p className="text-slate-400 font-black text-xs uppercase tracking-widest">Queue Clear. All systems optimal.</p>
          </div>
        )}
      </div>
    </div>
  );
};
