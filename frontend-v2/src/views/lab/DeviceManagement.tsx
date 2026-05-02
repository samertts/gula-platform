import React from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Microscope, Settings, Power, 
  Activity as ActivityIcon, Zap, ShieldAlert,
  Server, Cpu, Database, Wifi
} from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../../lib/utils';

export function DeviceManagement() {
  const { t } = useLanguage();

  const devices = [
    { id: 'AN-01', name: 'Cobas e801 Immunoassay', status: 'online', load: 82, model: 'Roche' },
    { id: 'AN-02', name: 'Atellica Solution IM', status: 'online', load: 45, model: 'Siemens' },
    { id: 'AN-03', name: 'Sysmex XN-3100', status: 'maintenance', load: 0, model: 'Sysmex' },
    { id: 'AN-04', name: 'AU5800 Analyzer', status: 'online', load: 12, model: 'Beckman Coulter' },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-600 text-white rounded-2xl shadow-lg shadow-indigo-100">
            <Microscope size={32} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Connectivity & Devices</h1>
            <p className="text-slate-500 font-medium italic opacity-80">ASTM/HL7 Interface Management</p>
          </div>
        </div>

        <button className="flex items-center gap-2 px-6 py-3 bg-white border border-slate-200 rounded-2xl text-sm font-bold shadow-sm hover:bg-slate-50 transition-all">
          <Zap size={18} className="text-amber-500" /> System Diagnostics
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
         {[
           { label: 'Total Analyzers', value: '18', icon: Microscope, color: 'text-indigo-600' },
           { label: 'Cloud Buffer', value: 'Active', icon: Server, color: 'text-emerald-600' },
           { label: 'LIS Middleware', value: 'v2.4.1', icon: Database, color: 'text-amber-600' },
           { label: 'Network Health', value: '99.9%', icon: Wifi, color: 'text-blue-600' }
         ].map(item => (
           <div key={item.label} className="bg-white p-6 rounded-[32px] border border-slate-100 shadow-sm flex items-center gap-4">
              <div className={cn("p-3 rounded-2xl bg-slate-50", item.color)}>
                 <item.icon size={20} />
              </div>
              <div>
                 <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest leading-none mb-1">{item.label}</p>
                 <p className="text-lg font-bold text-slate-900">{item.value}</p>
              </div>
           </div>
         ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
           <div className="flex items-center justify-between px-2">
              <h3 className="text-2xl font-bold text-slate-900">Lab Instrumentation</h3>
              <button className="text-sm font-bold text-indigo-600">Reboot Stack</button>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {devices.map((device, i) => (
                <motion.div 
                  key={device.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-white p-8 rounded-[40px] border border-slate-100 shadow-sm hover:border-indigo-600 transition-all group overflow-hidden relative"
                >
                  <div className="relative z-10">
                    <div className="flex items-start justify-between mb-8">
                       <div className="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                          <Cpu size={24} />
                       </div>
                       <div className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5 ${
                         device.status === 'online' ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'
                       }`}>
                          <div className={cn("w-1.5 h-1.5 rounded-full", device.status === 'online' ? 'bg-emerald-600 animate-pulse' : 'bg-red-600')} />
                          {device.status}
                       </div>
                    </div>

                    <h4 className="text-lg font-bold text-slate-900 mb-1">{device.name}</h4>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">{device.model} • {device.id}</p>

                    <div className="mt-8">
                       <div className="flex justify-between items-center mb-2">
                          <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Active Cycle Load</span>
                          <span className="text-xs font-bold text-slate-900">{device.load}%</span>
                       </div>
                       <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${device.load}%` }}
                            className={cn("h-full", device.load > 80 ? 'bg-amber-500' : 'bg-indigo-600')} 
                          />
                       </div>
                    </div>

                    <div className="mt-6 flex gap-2">
                       <button className="flex-1 py-3 bg-slate-50 text-slate-400 rounded-xl hover:bg-red-50 hover:text-red-600 transition-all font-bold text-[10px] uppercase tracking-widest flex items-center justify-center gap-2">
                          <Power size={14} /> Power
                       </button>
                       <button className="flex-1 py-3 bg-slate-50 text-slate-400 rounded-xl hover:bg-slate-900 hover:text-white transition-all font-bold text-[10px] uppercase tracking-widest flex items-center justify-center gap-2">
                          <Settings size={14} /> Config
                       </button>
                    </div>
                  </div>
                </motion.div>
              ))}
           </div>
        </div>

        <div className="space-y-6">
           <div className="bg-red-50 rounded-[40px] p-10 border border-red-100">
              <div className="flex items-center gap-3 mb-8 text-red-600">
                 <ShieldAlert size={24} />
                 <h3 className="text-xl font-bold">Alert Hub</h3>
              </div>
              <div className="space-y-4">
                 <div className="p-5 bg-white rounded-3xl border border-red-100 shadow-sm">
                    <p className="text-[10px] font-black text-red-300 uppercase tracking-widest mb-1">Device Calibration</p>
                    <p className="text-sm font-bold text-slate-900 mb-2">Cobas e801 requires re-calibration for Lipase assay.</p>
                    <button className="text-xs font-black text-red-600 border-b border-red-200">Start Sequence</button>
                 </div>
                 <div className="p-5 bg-white rounded-3xl border border-slate-100 opacity-60">
                    <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest mb-1">Archive Overflow</p>
                    <p className="text-sm font-bold text-slate-900">Storage node B3 is at 92% capacity.</p>
                 </div>
              </div>
           </div>

           <div className="bg-slate-900 rounded-[40px] p-10 text-white shadow-xl">
              <div className="flex items-center gap-3 mb-6">
                 <ActivityIcon size={24} className="text-indigo-400" />
                 <h3 className="text-xl font-bold">Interface Logs</h3>
              </div>
              <div className="space-y-3">
                 {[
                   'ASTM Interface [AN-01] Handshake OK',
                   'HL7 Message [ACK] Received from HIS',
                   'Query Patient Info: PID=9421',
                   'Device [AN-02] Result Upload Started'
                 ].map((log, i) => (
                   <div key={i} className="text-[10px] font-mono text-slate-400 flex gap-3">
                      <span className="text-indigo-500/50">[{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}]</span>
                      {log}
                   </div>
                 ))}
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
