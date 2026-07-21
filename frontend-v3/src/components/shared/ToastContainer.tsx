import { cn } from "@/lib/utils";
import { X, AlertCircle, CheckCircle2, Info } from "lucide-react";
import { useToast } from "@/hooks/useToast";

const iconMap = {
  default: Info,
  success: CheckCircle2,
  destructive: AlertCircle,
};

export function ToastContainer() {
  const { toasts, dismiss } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 end-4 z-[100] flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => {
        const Icon = iconMap[t.variant === "destructive" ? "destructive" : t.variant === "success" ? "success" : "default"];
        return (
          <div
            key={t.id}
            className={cn(
              "flex items-start gap-3 rounded-lg border p-4 shadow-lg bg-background text-foreground animate-in slide-in-from-right-full duration-300",
              t.variant === "destructive" && "border-destructive/50 text-destructive",
              t.variant === "success" && "border-emerald-500/50 text-emerald-700 dark:text-emerald-400",
            )}
          >
            <Icon className="h-5 w-5 shrink-0 mt-0.5" />
            <div className="flex-1">
              {t.title && <p className="text-sm font-semibold">{t.title}</p>}
              {t.description && <p className="text-sm opacity-90">{t.description}</p>}
            </div>
            <button onClick={() => dismiss(t.id)} className="shrink-0 rounded-sm opacity-70 hover:opacity-100">
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
