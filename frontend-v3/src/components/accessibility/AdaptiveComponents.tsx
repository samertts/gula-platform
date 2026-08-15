import { CheckCircle2, CircleAlert, CircleOff, Clock3, Eye, Info, LockKeyhole, WifiOff, XCircle, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export type AdaptiveState =
  | "enabled"
  | "disabled"
  | "preview"
  | "saved"
  | "saving"
  | "failed"
  | "consent_required"
  | "permission_denied"
  | "unavailable"
  | "offline";

const STATE_META: Record<AdaptiveState, { label: string; icon: LucideIcon; className: string }> = {
  enabled: { label: "Enabled", icon: CheckCircle2, className: "border-emerald-200 bg-emerald-50 text-emerald-800" },
  disabled: { label: "Disabled", icon: CircleOff, className: "border-slate-200 bg-slate-50 text-slate-700" },
  preview: { label: "Preview", icon: Eye, className: "border-sky-200 bg-sky-50 text-sky-800" },
  saved: { label: "Saved", icon: CheckCircle2, className: "border-emerald-200 bg-emerald-50 text-emerald-800" },
  saving: { label: "Saving", icon: Clock3, className: "border-amber-200 bg-amber-50 text-amber-900" },
  failed: { label: "Failed", icon: XCircle, className: "border-rose-200 bg-rose-50 text-rose-800" },
  consent_required: { label: "Consent Required", icon: LockKeyhole, className: "border-rose-200 bg-rose-50 text-rose-800" },
  permission_denied: { label: "Permission Denied", icon: CircleAlert, className: "border-rose-200 bg-rose-50 text-rose-800" },
  unavailable: { label: "Unavailable", icon: Info, className: "border-slate-200 bg-slate-50 text-slate-700" },
  offline: { label: "Offline", icon: WifiOff, className: "border-amber-200 bg-amber-50 text-amber-900" },
};

export function AdaptiveStateBadge({ state }: { state: AdaptiveState }) {
  const meta = STATE_META[state];
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold ${meta.className}`} role="status">
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      <span>{meta.label}</span>
    </span>
  );
}

export function AdaptiveStatus({
  state,
  label,
  description,
}: {
  state: AdaptiveState;
  label: string;
  description?: string;
}) {
  const meta = STATE_META[state];
  const Icon = meta.icon;
  return (
    <div className={`flex items-start gap-3 rounded-2xl border p-3 text-sm ${meta.className}`} role="status">
      <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <div>
        <div className="font-bold">{label}</div>
        {description && <div className="mt-1 text-xs leading-5 opacity-80">{description}</div>}
      </div>
    </div>
  );
}

export function AdaptivePreview({ children, active }: { children: ReactNode; active: boolean }) {
  return (
    <div className={active ? "rounded-[1.5rem] border-2 border-dashed border-sky-300 bg-sky-50/40 p-4 ring-4 ring-sky-100/70 dark:border-sky-700 dark:bg-sky-950/20 dark:ring-sky-950/40" : "rounded-[1.5rem] border border-slate-200/80 p-4 dark:border-white/10"}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="text-sm font-bold text-[#0F172A] dark:text-white">Adaptive component preview</div>
        <AdaptiveStateBadge state={active ? "preview" : "disabled"} />
      </div>
      {children}
    </div>
  );
}

export function AccessibleStatusLegend() {
  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4" aria-label="Status legend">
      <AdaptiveStatus state="enabled" label="Result ready" description="Text, icon, and shape reinforce the state." />
      <AdaptiveStatus state="disabled" label="Not enabled" description="The state is visible without relying on color." />
      <AdaptiveStatus state="consent_required" label="Consent required" description="Sensitive preferences stay hidden until consent." />
      <AdaptiveStatus state="offline" label="Offline" description="Local presentation remains safe; sensitive writes stop." />
    </div>
  );
}
