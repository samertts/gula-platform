import { Calendar as CalendarIcon, Clock, User, Phone, MoreVertical, Plus, Shield, BarChart3, PieChart } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';
import { motion } from 'motion/react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

const chartData = [
  { name: 'Cardio', value: 42, color: '#4f46e5' },
  { name: 'Pedia', value: 38, color: '#0ea5e9' },
  { name: 'Neuro', value: 25, color: '#8b5cf6' },
  { name: 'General', value: 54, color: '#10b981' },
];

export function AppointmentsView() {
  const { t } = useLanguage();

  const appointments = [
    { patient: "Naser Mohammad", id: "P-102", time: "09:30 AM", doctor: "Dr. Julian Vance", specialty: "Cardiology", status: "Confirmed" },
    { patient: "Sara Ahmed", id: "P-205", time: "10:15 AM", doctor: "Dr. Layla Demir", specialty: "Pediatrics", status: "Pending" },
    { patient: "Karwan H.", id: "P-301", time: "11:00 AM", doctor: "Dr. Ahmed M.", specialty: "Neurology", status: "Confirmed" },
    { patient: "Elias J.", id: "P-115", time: "01:30 PM", doctor: "Dr. Julian Vance", specialty: "General Practice", status: "Cancelled" }
  ];

  return (
    <div className="space-y-10 animate-in fade-in duration-700 max-w-7xl mx-auto w-full p-4 md:p-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6 w-full">
        <div className="editorial-stack">
          <span className="text-xs font-black uppercase tracking-[0.3em] text-indigo-600 block mb-2">{t.upcomingAppointments}</span>
          <h2 className="font-headline text-3xl lg:text-5xl font-black text-slate-900 tracking-tight leading-none">Intelligence Schedule</h2>
        </div>
        <div className="flex gap-3 w-full sm:w-auto">
          <button className="flex-1 sm:flex-none px-6 py-3 bg-white border border-slate-100 text-slate-700 font-bold text-sm rounded-2xl shadow-xl shadow-slate-200/40 hover:bg-slate-50 transition-all flex items-center justify-center gap-3 active:scale-95 group">
             <CalendarIcon size={18} className="text-indigo-600" />
             Month View
          </button>
          <button className="flex-1 sm:flex-none px-8 py-3 bg-indigo-600 text-white font-bold text-sm rounded-2xl shadow-2xl shadow-indigo-200 hover:bg-slate-900 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3">
            <Plus size={22} className="stroke-[3]" />
            {t.scheduleAppointment}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Load Insight Card */}
        <div className="lg:col-span-1 bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm flex flex-col gap-8">
           <div className="flex items-center justify-between">
              <div>
                 <h3 className="text-sm font-black uppercase tracking-widest text-slate-900">Capacity Distribution</h3>
                 <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">Live Clinical Load</p>
              </div>
              <BarChart3 size={20} className="text-indigo-600" />
           </div>
           
           <div className="h-48 -mx-4">
              <ResponsiveContainer width="100%" height="100%">
                 <BarChart data={chartData}>
                    <XAxis dataKey="name" hide />
                    <YAxis hide />
                    <Tooltip 
                       content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                             return (
                                <div className="bg-slate-900 px-3 py-2 rounded-xl text-[10px] font-black text-white shadow-xl">
                                   {payload[0].name}: {payload[0].value}%
                                </div>
                             );
                          }
                          return null;
                       }}
                    />
                    <Bar dataKey="value" radius={[10, 10, 10, 10]} barSize={24}>
                       {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                       ))}
                    </Bar>
                 </BarChart>
              </ResponsiveContainer>
           </div>

           <div className="space-y-4">
              <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-2xl">
                 <p className="text-[10px] font-black uppercase tracking-widest text-indigo-600 mb-1">AI Suggestion</p>
                 <p className="text-xs text-indigo-900 font-bold leading-relaxed">Consider re-routing Cardio overflows to wing 3 for peak efficiency.</p>
              </div>
           </div>
        </div>

        {/* Appointment Grid */}
        <div className="lg:col-span-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {appointments.map((apt, i) => (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm hover:shadow-2xl hover:shadow-slate-200/50 hover:-translate-y-1 transition-all group relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-8 opacity-[0.02] group-hover:scale-125 transition-transform">
                   <User size={120} />
                </div>

                <div className="flex justify-between items-start mb-8 relative z-10">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-2xl bg-slate-50 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-all shadow-inner">
                      <User size={32} />
                    </div>
                    <div>
                      <h4 className="text-lg font-black font-headline text-slate-900 tracking-tight">{apt.patient}</h4>
                      <p className="text-[10px] text-indigo-600 font-black uppercase tracking-[0.2em]">{apt.id}</p>
                    </div>
                  </div>
                  <span className={cn(
                    "px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border shadow-sm",
                    apt.status === 'Confirmed' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
                    apt.status === 'Pending' ? 'bg-amber-50 text-amber-700 border-amber-100' :
                    'bg-rose-50 text-rose-700 border-rose-100'
                  )}>
                    {apt.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-6 relative z-10">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-slate-400 group-hover:text-slate-900 transition-colors">
                      <Clock size={16} className="text-indigo-600" />
                      <span className="text-xs font-black uppercase tracking-widest">{apt.time}</span>
                    </div>
                    <div className="flex items-center gap-3 text-slate-400 group-hover:text-slate-900 transition-colors">
                      <CalendarIcon size={16} className="text-indigo-600" />
                      <span className="text-xs font-black uppercase tracking-widest leading-none">April 20, 2026</span>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-slate-400 group-hover:text-slate-900 transition-colors">
                      <Shield size={16} className="text-indigo-600" />
                      <div>
                         <p className="text-[10px] font-black uppercase tracking-tighter leading-none">{apt.doctor}</p>
                         <p className="text-[9px] text-slate-400 font-bold uppercase mt-1">{apt.specialty}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-8 pt-8 border-t border-slate-50 flex gap-4 relative z-10">
                  <button className="flex-1 py-4 bg-slate-900 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-2xl hover:bg-indigo-600 transition-all shadow-xl shadow-slate-200">
                    {t.details}
                  </button>
                  <button className="px-6 bg-slate-50 hover:bg-slate-100 text-slate-400 rounded-2xl transition-all border border-slate-100 flex items-center justify-center">
                    <Phone size={18} />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
