import { cn } from "@/lib/utils";
import { type LucideIcon, FileText, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui";

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("flex items-center justify-between", className)}>
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        {description && <p className="text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon: Icon = FileText, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      {description && <p className="mt-1 text-sm text-muted-foreground max-w-sm">{description}</p>}
      {action && (
        <Button className="mt-4" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}

export function PageLoadingSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("space-y-5 p-1", className)}
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label="جارٍ تحميل الصفحة"
    >
      <span className="sr-only">جارٍ تحميل الصفحة</span>
      <div className="motion-safe:animate-pulse space-y-3" aria-hidden="true">
        <div className="h-7 w-48 rounded-lg bg-slate-200/80 dark:bg-white/10" />
        <div className="h-4 w-72 max-w-full rounded-md bg-slate-200/70 dark:bg-white/[0.08]" />
      </div>
      <div className="grid gap-4 md:grid-cols-3" aria-hidden="true">
        {Array.from({ length: 3 }, (_, index) => (
          <div key={index} className="h-28 rounded-2xl border border-slate-200/80 bg-white/70 dark:border-white/10 dark:bg-white/[0.04]" />
        ))}
      </div>
      <div className="h-64 rounded-2xl border border-slate-200/80 bg-white/70 dark:border-white/10 dark:bg-white/[0.04]" aria-hidden="true" />
    </div>
  );
}

export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div
      className={cn("flex items-center justify-center py-16", className)}
      role="status"
      aria-live="polite"
      aria-label="جارٍ التحميل"
    >
      <span className="sr-only">جارٍ التحميل</span>
      <svg className="motion-safe:animate-spin h-8 w-8 text-primary" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
  );
}

interface ErrorDisplayProps {
  error?: string;
  onRetry?: () => void;
}

export function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <AlertCircle className="h-12 w-12 text-destructive" />
      <h3 className="mt-4 text-lg font-semibold">حدث خطأ</h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">{error || "حدث خطأ غير متوقع"}</p>
      {onRetry && (
        <Button variant="outline" className="mt-4" onClick={onRetry}>
          إعادة المحاولة
        </Button>
      )}
    </div>
  );
}
