import React, { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Box, Search, AlertTriangle, Plus, 
  ArrowUpRight, ShoppingCart, BarChart2,
  Trash2, Edit2, Filter, History as HistoryIcon,
  PackageCheck, Archive
} from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../../lib/utils';
import { auth, db } from '../../firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { toast } from 'sonner';

interface InventoryItem {
  id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  minLevel: number;
  expiryDate: string;
  status: 'optimal' | 'low' | 'expired';
  location: string;
}

export function InventoryManagement() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<'all' | 'low' | 'expired'>('all');
  const [isSimulating, setIsSimulating] = useState(false);

  const simulateAlert = async () => {
    setIsSimulating(true);
    try {
      await addDoc(collection(db, 'events'), {
        type: 'expiring_reagent',
        recipientId: 'all',
        title: 'Reagent Expiry Warning',
        message: 'Glucose Reagent Pack (MAT-101) is set to expire in 48 hours. Batch #G-092.',
        priority: 'urgent',
        wing: 'lab',
        read: false,
        createdAt: serverTimestamp()
      });
    } catch (e) {
      toast.error('Simulation failed');
    } finally {
      setIsSimulating(false);
    }
  };

  const inventory: InventoryItem[] = [
    {
      id: 'MAT-101',
      name: 'Glucose Reagent Pack',
      category: 'Chemistry',
      quantity: 12,
      unit: 'packs',
      minLevel: 20,
      expiryDate: '2026-10-15',
      status: 'low',
      location: 'Fridge A-2'
    },
    {
      id: 'MAT-205',
      name: 'EDTA Blood Tubes (5ml)',
      category: 'Consumables',
      quantity: 1400,
      unit: 'pcs',
      minLevel: 500,
      expiryDate: '2027-01-01',
      status: 'optimal',
      location: 'Rack B-1'
    },
    {
      id: 'MAT-044',
      name: 'Control Serum Level 1',
      category: 'Quality Control',
      quantity: 3,
      unit: 'vials',
      minLevel: 5,
      expiryDate: '2026-04-25',
      status: 'expired',
      location: 'Zero Freezer'
    }
  ];

  const filteredItems = inventory.filter(item => {
    if (activeTab === 'low') return item.status === 'low';
    if (activeTab === 'expired') return item.status === 'expired';
    return true;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10 min-h-screen">
      {/* Immersive Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 bg-slate-900 p-10 rounded-[3rem] text-white relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 p-12 opacity-[0.03] pointer-events-none scale-150">
           <Archive size={200} />
        </div>
        <div className="relative z-10 space-y-4">
           <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-900/20">
                 <Box size={24} className="text-white" />
              </div>
              <div>
                 <h1 className="text-3xl font-black uppercase tracking-tight">Supply Strategy</h1>
                 <p className="text-indigo-300/60 text-[10px] font-black uppercase tracking-[0.2em]">Autonomous Reagent Logistics Grid</p>
              </div>
           </div>
           <p className="max-w-xl text-sm text-slate-400 font-medium leading-relaxed">
             Real-time parity with regional reserves. Predictive algorithms are monitoring batch-level telemetry to prevent critical outages.
           </p>
        </div>
        <div className="relative z-10 flex flex-wrap items-center gap-3">
           <button 
             onClick={simulateAlert}
             disabled={isSimulating}
             className="flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 border border-white/10 rounded-2xl transition-all disabled:opacity-50 group"
           >
             <AlertTriangle size={18} className="text-amber-400" />
             <span className="text-[10px] font-black uppercase tracking-widest group-hover:tracking-[0.15em] transition-all">Simulation</span>
           </button>
           <button className="flex items-center gap-2 px-8 py-4 bg-indigo-600 text-white rounded-2xl shadow-xl shadow-indigo-900/20 hover:scale-105 transition-all active:scale-95">
             <Plus size={20} />
             <span className="text-[10px] font-black uppercase tracking-widest">Register Asset</span>
           </button>
        </div>
      </div>

      {/* High-Impact Stat Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: t.totalValue || 'Total Valuation', value: '$42,500', icon: BarChart2, color: 'text-indigo-600', bg: 'bg-indigo-600' },
          { label: t.lowStock || 'Critical Points', value: '8 Nodes', icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-600' },
          { label: t.expiringSoon || 'Expiry Risk', value: '3 Units', icon: HistoryIcon, color: 'text-rose-600', bg: 'bg-rose-600' },
          { label: t.activePos || 'Active Logistics', value: '5 Shipments', icon: ShoppingCart, color: 'text-emerald-600', bg: 'bg-emerald-600' },
        ].map((stat, i) => (
          <motion.div 
            key={i} 
            whileHover={{ y: -5 }}
            className="bg-white p-6 rounded-[2.5rem] border border-slate-100 shadow-sm flex items-center gap-6 group hover:border-indigo-100 transition-all relative overflow-hidden"
          >
            <div className={cn("absolute top-0 right-0 w-24 h-24 opacity-[0.03] -mr-8 -mt-8 rounded-full blur-2xl", stat.bg)} />
            <div className={cn("p-4 rounded-2xl bg-slate-50 transition-colors group-hover:text-white group-hover:shadow-lg", stat.color, `group-hover:${stat.bg}`)}>
              <stat.icon size={24} />
            </div>
            <div className="flex flex-col relative z-10">
               <span className="text-[9px] text-slate-400 font-black uppercase tracking-[0.2em] mb-1">{stat.label}</span>
               <span className="text-2xl font-black text-slate-900 tracking-tight">{stat.value}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Sophisticated Data Grid */}
      <div className="bg-white border border-slate-100 rounded-[3rem] overflow-hidden shadow-xl shadow-slate-200/40">
        <div className="p-8 border-b border-slate-50 flex flex-col lg:flex-row lg:items-center justify-between gap-6 bg-slate-50/30">
          <div className="flex items-center gap-2 p-1.5 bg-slate-100/50 rounded-2xl w-fit">
            {(['all', 'low', 'expired'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "px-8 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all",
                  activeTab === tab 
                    ? "bg-slate-900 text-white shadow-xl shadow-slate-900/20" 
                    : "text-slate-400 hover:text-slate-600 hover:bg-white"
                )}
              >
                {tab}
              </button>
            ))}
          </div>
          <div className="flex gap-4">
             <div className="relative group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-indigo-600 transition-colors" size={18} />
                <input 
                  type="text" 
                  placeholder="Query material registry..."
                  className="pl-12 pr-6 py-4 border border-transparent bg-white rounded-2xl text-xs w-full lg:w-80 shadow-sm focus:ring-4 focus:ring-indigo-50 outline-none transition-all font-bold placeholder:text-slate-300"
                />
             </div>
             <button className="p-4 bg-white border border-slate-100 rounded-2xl text-slate-400 hover:text-indigo-600 transition-all shadow-sm">
                <Filter size={20} />
             </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-50">
                <th className="px-10 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Material Intelligence</th>
                <th className="px-8 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Deployment</th>
                <th className="px-8 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Resource Level</th>
                <th className="px-8 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Expiry Vector</th>
                <th className="px-8 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Status</th>
                <th className="px-10 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Control</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/50 transition-all group">
                  <td className="px-10 py-8">
                    <div className="flex items-center gap-4">
                       <div className="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-all">
                          <PackageCheck size={24} />
                       </div>
                       <div className="flex flex-col">
                         <span className="text-base font-black text-slate-900 leading-none mb-1 group-hover:translate-x-1 transition-transform">{item.name}</span>
                         <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">{item.id} • ZONE {item.location}</span>
                       </div>
                    </div>
                  </td>
                  <td className="px-8 py-8">
                    <span className="px-4 py-1.5 bg-slate-50 text-slate-500 rounded-xl text-[10px] font-black uppercase tracking-widest border border-slate-100">{item.category}</span>
                  </td>
                  <td className="px-8 py-8">
                     <div className="space-y-2 max-w-[120px]">
                        <div className="flex items-end justify-between">
                           <span className={cn(
                             "text-xl font-black",
                             item.quantity < item.minLevel ? "text-amber-600" : "text-slate-900"
                           )}>{item.quantity}</span>
                           <span className="text-[9px] text-slate-400 font-black uppercase tracking-tighter mb-1">{item.unit}</span>
                        </div>
                        <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
                           <motion.div 
                             initial={{ width: 0 }}
                             animate={{ width: `${Math.min((item.quantity / 2000) * 100, 100)}%` }}
                             className={cn("h-full", item.quantity < item.minLevel ? 'bg-amber-500' : 'bg-indigo-500')}
                           />
                        </div>
                     </div>
                  </td>
                  <td className="px-8 py-8">
                    <div className="flex flex-col">
                       <span className={cn(
                         "text-xs font-black",
                         item.status === 'expired' ? "text-red-500" : "text-slate-900"
                       )}>{new Date(item.expiryDate).toLocaleDateString()}</span>
                       <span className="text-[9px] font-bold text-slate-400 uppercase tracking-tight">System Validated</span>
                    </div>
                  </td>
                  <td className="px-8 py-8">
                     <span className={cn(
                       "inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest shadow-sm",
                       item.status === 'optimal' ? "bg-emerald-50 text-emerald-600 border border-emerald-100" :
                       item.status === 'low' ? "bg-amber-50 text-amber-600 border border-amber-100 animate-pulse" :
                       "bg-red-50 text-red-600 border border-red-100"
                     )}>
                        <div className={cn(
                          "w-1.5 h-1.5 rounded-full",
                          item.status === 'optimal' ? "bg-emerald-600" :
                          item.status === 'low' ? "bg-amber-600" :
                          "bg-red-600"
                        )} />
                        {item.status}
                     </span>
                  </td>
                  <td className="px-10 py-8">
                     <div className="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-all translate-x-4 group-hover:translate-x-0">
                        <button className="p-3 text-slate-400 hover:text-indigo-600 hover:bg-white rounded-2xl shadow-sm transition-all border border-transparent hover:border-slate-100">
                           <Edit2 size={16} />
                        </button>
                        <button className="p-3 text-slate-400 hover:text-red-600 hover:bg-white rounded-2xl shadow-sm transition-all border border-transparent hover:border-slate-100">
                           <Trash2 size={16} />
                        </button>
                        <button className="p-3 bg-indigo-600 text-white rounded-2xl shadow-lg shadow-indigo-100 hover:scale-110 active:scale-95 transition-all">
                           <ShoppingCart size={16} />
                        </button>
                     </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
