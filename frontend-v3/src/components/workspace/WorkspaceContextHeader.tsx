import { Building2, LockKeyhole, ShieldCheck } from "lucide-react";
import { getRoleLabel } from "@/lib/utils";
import type { WorkspaceSummary } from "@/api/client";

interface WorkspaceContextHeaderProps {
  workspace?: WorkspaceSummary | null;
  demoMode: boolean;
  role?: string;
}

function workspaceLabel(workspace: WorkspaceSummary) {
  return workspace.name_ar || workspace.name || "مساحة العمل الحالية";
}

export function WorkspaceContextHeader({
  workspace,
  demoMode,
  role,
}: WorkspaceContextHeaderProps) {
  if (demoMode) {
    return (
      <section
        aria-label="سياق الوصول الحالي"
        className="flex flex-col gap-4 rounded-2xl border border-amber-200/80 bg-gradient-to-l from-amber-50 to-white p-4 shadow-sm dark:border-amber-900/50 dark:from-amber-950/30 dark:to-slate-900/70 sm:flex-row sm:items-center sm:justify-between"
      >
        <div className="flex min-w-0 items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/15 text-amber-700 dark:text-amber-200">
            <ShieldCheck className="h-5 w-5" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-amber-700 dark:text-amber-200">
              سياق المعاينة
            </p>
            <h2 className="mt-1 truncate text-sm font-bold text-amber-950 dark:text-amber-100">
              مساحة GULA الاصطناعية المعزولة
            </h2>
            <p className="mt-1 text-xs leading-5 text-amber-800/75 dark:text-amber-200/75">
              بيانات تركيبية للقراءة فقط؛ لا توجد عضوية مؤسسية أو عملية سريرية حقيقية.
            </p>
          </div>
        </div>
        <span className="inline-flex shrink-0 items-center gap-1.5 self-start rounded-full border border-amber-300/70 bg-amber-100/70 px-3 py-1.5 text-xs font-bold text-amber-800 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-200 sm:self-center">
          <LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" />
          {getRoleLabel(role || "citizen")} · قراءة فقط
        </span>
      </section>
    );
  }

  if (!workspace) {
    return (
      <section
        aria-label="سياق الوصول الحالي"
        role="status"
        className="flex items-start gap-3 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900/70"
      >
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-500 dark:bg-white/10 dark:text-slate-300">
          <LockKeyhole className="h-5 w-5" aria-hidden="true" />
        </span>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
            سياق مؤسسي محمي
          </p>
          <h2 className="mt-1 text-sm font-bold">لم تُحمّل مساحة عمل مصرح بها</h2>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            لن تُعرض بيانات مؤسسية حتى يعيد الخادم سياقاً صالحاً للجلسة الحالية.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section
      aria-label="سياق الوصول الحالي"
      className="flex flex-col gap-4 rounded-2xl border border-teal-100/80 bg-gradient-to-l from-teal-50/80 to-white p-4 shadow-sm dark:border-teal-900/50 dark:from-teal-950/25 dark:to-slate-900/70 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="flex min-w-0 items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-teal-500/15 text-teal-700 dark:text-teal-200">
          <Building2 className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-teal-700 dark:text-teal-200">
            مساحة العمل الحالية
          </p>
          <h2 className="mt-1 truncate text-sm font-bold">
            {workspaceLabel(workspace)}
          </h2>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            الحالة: {workspace.status || "منعكسة من الخادم"} · النطاق يحدده الخادم
          </p>
        </div>
      </div>
      <div className="flex shrink-0 flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full bg-teal-100/80 px-3 py-1.5 font-bold text-teal-800 dark:bg-teal-950/50 dark:text-teal-200">
          {getRoleLabel(role || "citizen")}
        </span>
        <span className="rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 font-semibold text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300">
          سياق خادمي
        </span>
      </div>
    </section>
  );
}
