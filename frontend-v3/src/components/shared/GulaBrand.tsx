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
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-teal-400 to-blue-600 text-white shadow-sm">
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
    <span className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-700 dark:text-amber-300">
      <span className="h-2 w-2 rounded-full bg-amber-500" />
      بيئة عرض تجريبية
    </span>
  );
}
