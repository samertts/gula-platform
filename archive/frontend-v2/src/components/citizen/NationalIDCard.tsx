import React from 'react';
import { motion } from 'motion/react';
import { Shield, Fingerprint, QrCode, Cpu, Globe } from 'lucide-react';
import { cn } from '../../lib/utils';

interface NationalIDCardProps {
  name: string;
  id: string;
  dob: string;
  bloodType: string;
  expiry: string;
  photoUrl?: string;
  className?: string;
}

export const NationalIDCard: React.FC<NationalIDCardProps> = ({
  name, id, dob, bloodType, expiry, photoUrl, className
}) => {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      className={cn(
        "relative w-full max-w-md aspect-[1.6/1] bg-slate-900 rounded-[2rem] overflow-hidden shadow-2xl border border-white/10 group",
        className
      )}
    >
      {/* Dynamic Background Elements */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(79,70,229,0.3),transparent)]" />
      <div className="absolute inset-0 bg-[repeating-linear-gradient(45deg,transparent,transparent_20px,rgba(255,255,255,0.02)_20px,rgba(255,255,255,0.02)_21px)]" />
      
      {/* Holographic Overlays */}
      <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
         <Globe size={180} />
      </div>

      <div className="relative z-10 p-8 h-full flex flex-col justify-between text-white">
        {/* Header */}
        <div className="flex justify-between items-start">
           <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur-md border border-white/10 shadow-lg shadow-indigo-900/50">
                 <Shield size={20} className="text-indigo-400" />
              </div>
              <div>
                 <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-400">Republic of Iraq</h2>
                 <h1 className="text-xs font-bold uppercase tracking-widest text-white/80">National Cloud Identity</h1>
              </div>
           </div>
           <div className="flex flex-col items-end">
              <div className="w-8 h-8 bg-emerald-500/20 rounded-lg flex items-center justify-center text-emerald-400 border border-emerald-500/30">
                 <Fingerprint size={16} />
              </div>
              <span className="text-[6px] font-bold uppercase tracking-widest mt-1 text-emerald-400/60">Biometrics Encoded</span>
           </div>
        </div>

        {/* Mid Section */}
        <div className="flex gap-6 items-end">
           <div className="w-24 h-24 bg-white/5 rounded-2xl border border-white/10 overflow-hidden relative group/photo">
              {photoUrl ? (
                <img src={photoUrl} alt="User" className="w-full h-full object-cover grayscale group-hover/photo:grayscale-0 transition-all duration-700" referrerPolicy="no-referrer" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-white/20">
                   <User size={48} />
                </div>
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 to-transparent" />
              <div className="absolute bottom-1 right-1">
                 <div className="w-4 h-4 bg-emerald-500 rounded-full border-2 border-slate-900 animate-pulse" />
              </div>
           </div>

           <div className="flex-1 space-y-4">
              <div>
                 <p className="text-[8px] font-black text-indigo-400/60 uppercase tracking-widest mb-0.5">Subject Identity</p>
                 <p className="text-xl font-black tracking-tight">{name}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                 <div>
                    <p className="text-[8px] font-black text-indigo-400/60 uppercase tracking-widest mb-0.5">National UID</p>
                    <p className="text-xs font-mono font-bold tracking-tighter">{id}</p>
                 </div>
                 <div>
                    <p className="text-[8px] font-black text-indigo-400/60 uppercase tracking-widest mb-0.5">Blood Type</p>
                    <p className="text-xs font-black text-rose-400">{bloodType}</p>
                 </div>
              </div>
           </div>

           <div className="flex flex-col items-center justify-center gap-2">
              <div className="p-3 bg-white rounded-xl shadow-xl shadow-black/20 group-hover:scale-105 transition-transform duration-500">
                 <QrCode size={40} className="text-slate-900" />
              </div>
              <p className="text-[6px] font-black uppercase text-indigo-400/40">Secure Node Sync</p>
           </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center pt-4 border-t border-white/5">
           <div className="flex items-center gap-4">
              <div>
                 <p className="text-[6px] font-black text-white/20 uppercase tracking-widest">Issued On</p>
                 <p className="text-[8px] font-bold">{dob}</p>
              </div>
              <div>
                 <p className="text-[6px] font-black text-white/20 uppercase tracking-widest">Expires</p>
                 <p className="text-[8px] font-bold text-amber-400/80">{expiry}</p>
              </div>
           </div>
           <div className="flex items-center gap-2">
              <Cpu size={12} className="text-indigo-400/40" />
              <span className="text-[7px] font-black uppercase tracking-widest text-indigo-400/40">GULA-CRYPTO-V4</span>
           </div>
        </div>
      </div>
    </motion.div>
  );
};

import { User } from 'lucide-react';
