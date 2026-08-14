import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";

interface WorkspaceSelectorProps {
  onActiveWorkspace?: (workspace: WorkspaceSummary) => void;
}

export function WorkspaceSelector({ onActiveWorkspace }: WorkspaceSelectorProps) {
  const { t } = useTranslation();
  const { demoMode } = useAuth();
  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState("");
  const [loading, setLoading] = useState(!demoMode);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (demoMode) {
      setLoading(false);
      setWorkspaces([]);
      return () => { cancelled = true; };
    }
    setLoading(true);
    apiClient.listWorkspaces()
      .then((payload) => {
        if (cancelled) return;
        setWorkspaces(payload.workspaces);
        const first = payload.workspaces[0];
        if (first) {
          setActiveWorkspaceId(first.id);
          onActiveWorkspace?.(first);
        }
      })
      .catch(() => {
        if (!cancelled) setError("تعذر تحميل مساحات العمل المصرح بها من الخادم.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [demoMode, onActiveWorkspace]);

  async function handleSwitch(workspaceId: string) {
    const selected = workspaces.find((item) => item.id === workspaceId);
    if (!selected) return;
    setError(null);
    try {
      const response = await apiClient.switchWorkspace(workspaceId);
      setActiveWorkspaceId(response.context.workspace_id);
      onActiveWorkspace?.(response.workspace);
    } catch {
      setError("رفض الخادم تبديل مساحة العمل أو انتهت صلاحية الجلسة.");
    }
  }

  if (demoMode) {
    return <span className="text-xs text-muted-foreground" role="status">مساحات العمل غير متاحة في وضع المعاينة الاصطناعي.</span>;
  }
  if (loading) {
    return <span className="text-xs text-muted-foreground" role="status" aria-live="polite">جارٍ تحميل المساحات…</span>;
  }
  if (error) {
    return <span className="max-w-56 text-xs text-destructive" role="alert">{error}</span>;
  }
  if (workspaces.length === 0) {
    return <span className="text-xs text-muted-foreground" role="status">لا توجد مساحة عمل مصرح بها.</span>;
  }

  return (
    <label className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs dark:border-white/10 dark:bg-white/[0.04]">
      <span className="sr-only">{t("workspace.selector", "مساحات العمل")}</span>
      <span className="font-semibold text-muted-foreground" aria-hidden="true">مساحتي</span>
      <select
        className="max-w-44 bg-transparent font-bold outline-none"
        value={activeWorkspaceId}
        onChange={(event) => void handleSwitch(event.target.value)}
        aria-label="اختيار مساحة العمل"
      >
        {workspaces.map((workspace) => (
          <option key={workspace.id} value={workspace.id}>
            {workspace.name_ar || workspace.name}
          </option>
        ))}
      </select>
    </label>
  );
}
