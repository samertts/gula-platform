import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "tasks", label: "tasks", icon: FileText },
  { id: "dashboard", label: "لوحة القيادة", icon: Activity },
  { id: "comments", label: "comments", icon: List },
  { id: "history", label: "history", icon: ClipboardList },
  { id: "queues", label: "queues", icon: BookOpen },
  { id: "sla-definitions", label: "sla-definitions", icon:  FolderOpen },
] as const;

type TabId = (typeof tabs)[number]["id"];

const badgeVariant = (s: string) => {
  const m: Record<string, "success" | "warning" | "destructive" | "default"> = {
    active: "success", completed: "success", approved: "success",
    pending: "warning", draft: "default", rejected: "destructive",
    inactive: "default", expired: "warning", revoked: "destructive",
  };
  return m[s?.toLowerCase()] ?? "default";
};

export default function NationalTaskEngineApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("tasks");
  const col = createColumnHelper<Record<string, unknown>>();

  const tasks = useQuery({
    queryKey: ["nationalTaskEngineApi", "tasks"],
    queryFn: () => api.get("/national/tasks").then((r) => r.data),
  });
  const dashboard = useQuery({
    queryKey: ["nationalTaskEngineApi", "dashboard"],
    queryFn: () => api.get("/national/tasks/dashboard").then((r) => r.data),
  });
  const comments = useQuery({
    queryKey: ["nationalTaskEngineApi", "comments"],
    enabled: false,
    queryFn: () => api.get("/national/tasks//comments").then((r) => r.data),
  });
  const history = useQuery({
    queryKey: ["nationalTaskEngineApi", "history"],
    enabled: false,
    queryFn: () => api.get("/national/tasks//history").then((r) => r.data),
  });
  const queues = useQuery({
    queryKey: ["nationalTaskEngineApi", "queues"],
    queryFn: () => api.get("/national/tasks/queues").then((r) => r.data),
  });
  const slaDefinitions = useQuery({
    queryKey: ["nationalTaskEngineApi", "sla-definitions"],
    queryFn: () => api.get("/national/tasks/sla-definitions").then((r) => r.data),
  });

  const tasksCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const dashboardCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const commentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const historyCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const queuesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const slaDefinitionsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    tasks: { columns: tasksCols, data: asTableData(tasks.data), loading: tasks.isLoading, error: tasks.error, onRetry: () => tasks.refetch() },
    dashboard: { columns: dashboardCols, data: asTableData(dashboard.data), loading: dashboard.isLoading, error: dashboard.error, onRetry: () => dashboard.refetch() },
    comments: { columns: commentsCols, data: asTableData(comments.data), loading: comments.isLoading, error: comments.error, onRetry: () => comments.refetch() },
    history: { columns: historyCols, data: asTableData(history.data), loading: history.isLoading, error: history.error, onRetry: () => history.refetch() },
    queues: { columns: queuesCols, data: asTableData(queues.data), loading: queues.isLoading, error: queues.error, onRetry: () => queues.refetch() },
    "sla-definitions": { columns: slaDefinitionsCols, data: asTableData(slaDefinitions.data), loading: slaDefinitions.isLoading, error: slaDefinitions.error, onRetry: () => slaDefinitions.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="محرك المهام" description="إدارة محرك المهام" />
      <Card>
        <CardContent className="p-0">
          <div className="flex border-b flex-wrap">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} role="tab" aria-selected={activeTab === tab.id} onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-indigo-600 text-indigo-600" : "text-gray-500 hover:text-gray-700"}`}>
                  <Icon className="h-4 w-4" />{tab.label}
                </button>
              );
            })}
          </div>
          <div className="p-4">
            <DataTable columns={tables[activeTab].columns} data={tables[activeTab].data} loading={tables[activeTab].loading} error={tables[activeTab].error} onRetry={tables[activeTab].onRetry} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
