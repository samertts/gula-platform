import React from 'react';
import { cn } from '../../lib/utils';
import { ShieldCheck, ShieldAlert, Shield } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface PasswordStrengthProps {
  password: string;
}

export function PasswordStrength({ password }: PasswordStrengthProps) {
  const { t } = useLanguage();
  const getStrength = (pass: string) => {
    let score = 0;
    if (pass.length > 8) score++;
    if (/[A-Z]/.test(pass)) score++;
    if (/[0-9]/.test(pass)) score++;
    if (/[^a-zA-Z0-9]/.test(pass)) score++;
    return score;
  };

  const strength = getStrength(password);
  
  const labels = [t.weak, t.fair, t.good, t.strong];
  const colors = ['bg-red-500', 'bg-amber-500', 'bg-blue-500', 'bg-emerald-500'];
  const icons = [ShieldAlert, Shield, Shield, ShieldCheck];
  
  const ActiveIcon = icons[strength - 1] || Shield;

  if (!password) return null;

  return (
    <div className="mt-2 space-y-2">
      <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-slate-400">
        <div className="flex items-center gap-1.5">
          <ActiveIcon size={12} className={cn(strength > 0 ? colors[strength-1].replace('bg-', 'text-') : 'text-slate-300')} />
          <span>{t.securityLevel}: {labels[strength - 1] || t.none}</span>
        </div>
        <span>{Math.min(strength * 25, 100)}%</span>
      </div>
      <div className="flex gap-1 h-1">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={cn(
              "flex-1 rounded-full transition-all duration-500",
              i <= strength ? colors[strength - 1] : "bg-slate-100"
            )}
          />
        ))}
      </div>
    </div>
  );
}
