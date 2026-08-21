import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/contexts/AuthContext";
import type { WorkspaceSummary } from "@/api/client";
import { classifyApiError } from "@/api/errorHandling";

interface WorkspaceSelectorProps {
  onActiveWorkspace?: (workspace: WorkspaceSummary) => void;
}

export function WorkspaceSelector({ onActiveWorkspace }: WorkspaceSelectorProps) {
  const { t } = useTranslation();
  const {
    demoMode,
    availableWorkspaces,
    workspace,
    memberships,
    state,
    switchWorkspace,
    refreshWorkspaces,
    error: authError,
  } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState(workspace?.id ?? "");
  const activeMemberships = workspace?.organization_id
    ? memberships.filter((membership) => membership.organization_id === workspace.organization_id && membership.status === "active")
    : [];
  const accessStatus = state === "AUTHORIZED" ? "مصرح" : state === "WORKSPACE_REQUIRED" ? "يتطلب اختياراً" : state === "ERROR" ? "الخدمة غير متاحة" : state;

  useEffect(() => {
    setSelectedWorkspaceId(workspace?.id ?? "");
  }, [workspace?.id]);

  async function handleSwitch(workspaceId: string) {
    setError(null);
    setSelectedWorkspaceId(workspaceId);
    setLoading(true);
    try {
      const selected = await switchWorkspace(workspaceId);
      setSelectedWorkspaceId(selected.id);
      onActiveWorkspace?.(selected);
    } catch (caught) {
      const info = classifyApiError(caught, "تعذر تبديل مساحة العمل.");
      setSelectedWorkspaceId(workspace?.id ?? "");
      setError(info.message);
      if (info.kind === "CONFLICT") await refreshWorkspaces().catch(() => undefined);
    } finally {
      setLoading(false);
    }
  }

  if (demoMode) {
    return (
      <span className="hidden max-w-40 truncate text-xs text-muted-foreground sm:inline" role="status">
        مساحات العمل غير متاحة في وضع المعاينة الاصطناعي.
      </span>
    );
  }
  if (state === "SESSION_EXPIRED" || state === "UNAUTHENTICATED") return null;
  if (state === "LOADING" || state === "UNKNOWN") {
    return <span className="text-xs text-muted-foreground" role="status" aria-live="polite">جارٍ تحميل المساحات…</span>;
  }
  if (availableWorkspaces.length === 0) {
    if (error || authError) return <div className="flex items-center gap-2" role="alert"><span className="max-w-56 text-xs text-destructive">{error || authError?.message}</span><button type="button" className="text-xs font-semibold underline" onClick={() => void refreshWorkspaces()}>إعادة المحاولة</button></div>;
    return <span className="text-xs text-muted-foreground" role="status">لا توجد مساحة عمل مصرح بها.</span>;
  }
  return (
    <div className="flex items-center gap-2">
      {workspace && (
        <div className="hidden max-w-72 flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground lg:flex" role="status" aria-label="السياق الحالي">
          <span>المنظمة: {workspace.organization_id || "شخصية"}</span>
          <span>المنشأة: {workspace.facility_id || "غير محددة"}</span>
          <span>المساحة: {workspace.name_ar || workspace.name}</span>
          <span>الوصول: {accessStatus}</span>
          <span>نطاق العضوية: {activeMemberships[0]?.scope_type || "غير معروض"}</span>
        </div>
      )}
      {loading && <span className="text-xs text-muted-foreground" role="status" aria-live="polite">جارٍ اعتماد السياق…</span>}
      {(error || authError) && <div className="flex items-center gap-2" role="alert"><span className="max-w-56 text-xs text-destructive">{error || authError?.message}</span><button type="button" className="text-xs font-semibold underline" onClick={() => void refreshWorkspaces()}>إعادة المحاولة</button></div>}
    <label className="flex items-center gap-2 rounded-xl border border-teal-100 bg-teal-50/60 px-2.5 py-1.5 text-xs shadow-sm dark:border-teal-900/50 dark:bg-teal-950/20">
      <span className="sr-only">{t("workspace.selector", "مساحات العمل")}</span>
      <span className="font-semibold text-[#0D9488] dark:text-teal-200" aria-hidden="true">مساحتي</span>
      <select
        className="max-w-44 bg-transparent font-bold outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2"
        value={selectedWorkspaceId}
        onChange={(event) => void handleSwitch(event.target.value)}
        aria-label="اختيار مساحة العمل"
        disabled={loading}
      >
        <option value="" disabled>اختر مساحة العمل</option>
        {availableWorkspaces.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name_ar || item.name}
          </option>
        ))}
      </select>
    </label>
    </div>
  );
}
