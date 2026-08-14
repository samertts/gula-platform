import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface GulaBrandProps {
  compact?: boolean;
  dark?: boolean;
  className?: string;
}

export function GulaBrand({ compact = false, dark = false, className }: GulaBrandProps) {
  return (
    <span className={cn("inline-flex items-center gap-2", dark ? "text-white" : "text-foreground", className)}>
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#0D9488] to-[#0F172A] text-white shadow-[0_10px_24px_-14px_rgba(15,23,42,0.9)]">
        <Activity className="h-5 w-5" strokeWidth={2.5} />
      </span>
      {!compact && (
        <span className="leading-tight">
          <span className="block text-sm font-bold tracking-tight">جولا</span>
          <span className={cn("block font-mono text-[9px] font-bold tracking-[0.22em]", dark ? "text-slate-300" : "text-muted-foreground")}>
            GULA
          </span>
        </span>
      )}
    </span>
  );
}

export function DemoEnvironmentBadge() {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-semibold text-amber-800 dark:text-amber-200">
      <span className="h-2 w-2 rounded-full bg-amber-500 shadow-[0_0_0_4px_rgba(245,158,11,0.12)]" />
      عرض تجريبي · قراءة فقط
    </span>
  );
}
