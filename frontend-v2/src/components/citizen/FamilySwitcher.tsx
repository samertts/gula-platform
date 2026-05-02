import React, { useState } from 'react';
import { Users, UserPlus, Heart, ChevronDown, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';

interface FamilyMember {
  id: string;
  name: string;
  relationship: string;
  avatar: string;
}

export function FamilySwitcher() {
  const { t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [selected, setSelected] = useState<FamilyMember>({ id: 'me', name: 'Samer Mohammed', relationship: 'Self', avatar: 'S' });
  
  const members: FamilyMember[] = [
    { id: 'me', name: 'Samer Mohammed', relationship: 'Self', avatar: 'S' },
    { id: 'm1', name: 'Zaid Samer', relationship: 'Son', avatar: 'Z' },
    { id: 'm2', name: 'Mariam Samer', relationship: 'Daughter', avatar: 'M' },
    { id: 'm3', name: 'Fatima Ali', relationship: 'Spouse', avatar: 'F' }
  ];

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-4 bg-white border border-slate-200 p-2 pl-4 pr-3 rounded-2xl shadow-sm hover:border-indigo-600 transition-all group"
      >
        <div className="flex -space-x-2">
          {members.slice(0, 3).map(m => (
            <div key={m.id} className="w-8 h-8 rounded-lg bg-indigo-50 border-2 border-white flex items-center justify-center text-[10px] font-black text-indigo-600 shadow-sm uppercase">
              {m.avatar}
            </div>
          ))}
          {members.length > 3 && (
            <div className="w-8 h-8 rounded-lg bg-slate-900 border-2 border-white flex items-center justify-center text-[10px] font-black text-white shadow-sm">
              +{members.length - 3}
            </div>
          )}
        </div>
        <div className="text-left py-1 pr-6 border-r border-slate-100 flex-1">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">{t.familyAccess}</p>
          <p className="text-xs font-black text-slate-900 leading-none">{selected.name}</p>
        </div>
        <ChevronDown size={16} className={cn("text-slate-400 transition-transform", isOpen && "rotate-180")} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="absolute top-full right-0 mt-4 w-72 bg-white rounded-[2rem] border border-slate-200 shadow-2xl p-6 z-50 overflow-hidden"
          >
             <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
                <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400">Manage Profiles</h4>
                <Users size={14} className="text-slate-300" />
             </div>
             
             <div className="space-y-1 mb-4">
               {members.map(member => (
                 <button
                   key={member.id}
                   onClick={() => {
                     setSelected(member);
                     setIsOpen(false);
                   }}
                   className={cn(
                     "w-full flex items-center gap-4 p-3 rounded-xl transition-all text-left group",
                     selected.id === member.id ? "bg-indigo-50" : "hover:bg-slate-50"
                   )}
                 >
                   <div className={cn(
                     "w-10 h-10 rounded-xl flex items-center justify-center font-black shadow-sm",
                     selected.id === member.id ? "bg-indigo-600 text-white" : "bg-white border border-slate-200 text-slate-400"
                   )}>
                     {member.avatar}
                   </div>
                   <div className="flex-1">
                     <p className="text-xs font-black text-slate-900">{member.name}</p>
                     <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">{member.relationship}</p>
                   </div>
                   {selected.id === member.id && <Check size={16} className="text-indigo-600" />}
                 </button>
               ))}
             </div>

             <button className="w-full py-4 bg-slate-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-indigo-600 transition-colors shadow-lg active:scale-95">
                <UserPlus size={16} /> {t.addDependent}
             </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
