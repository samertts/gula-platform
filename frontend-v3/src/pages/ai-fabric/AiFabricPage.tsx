import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "health", label: "الحالة", icon: FileText },
  { id: "providers", label: "المزودون", icon: Activity },
  { id: "cost", label: "cost", icon: List },
  { id: "status", label: "status", icon: ClipboardList },
  { id: "entity", label: "entity", icon: BookOpen },
  { id: "related", label: "related", icon:  FolderOpen },
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

export default function AiFabricPage() {
  const [activeTab, setActiveTab] = useState<TabId>("health");
  const col = createColumnHelper<Record<string, unknown>>();

  const health = useQuery({
    queryKey: ["aiFabric", "health"],
    queryFn: () => api.get("/ai/fabric/health").then((r) => r.data),
  });
  const providers = useQuery({
    queryKey: ["aiFabric", "providers"],
    queryFn: () => api.get("/ai/fabric/gateway/providers").then((r) => r.data),
  });
  const cost = useQuery({
    queryKey: ["aiFabric", "cost"],
    queryFn: () => api.get("/ai/fabric/gateway/cost").then((r) => r.data),
  });
  const status = useQuery({
    queryKey: ["aiFabric", "status"],
    queryFn: () => api.get("/ai/fabric/local-ai/status").then((r) => r.data),
  });
  const entity = useQuery({
    queryKey: ["aiFabric", "entity"],
    queryFn: () => api.get("/ai/fabric/knowledge-graph/entity").then((r) => r.data),
  });
  const related = useQuery({
    queryKey: ["aiFabric", "related"],
    queryFn: () => api.get("/ai/fabric/knowledge-graph/related").then((r) => r.data),
  });

  const healthCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const providersCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const costCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const statusCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const entityCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const relatedCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    health: { columns: healthCols, data: (health.data ?? []) as Record<string, unknown>[], loading: health.isLoading, error: health.error, onRetry: () => health.refetch() },
    providers: { columns: providersCols, data: (providers.data ?? []) as Record<string, unknown>[], loading: providers.isLoading, error: providers.error, onRetry: () => providers.refetch() },
    cost: { columns: costCols, data: (cost.data ?? []) as Record<string, unknown>[], loading: cost.isLoading, error: cost.error, onRetry: () => cost.refetch() },
    status: { columns: statusCols, data: (status.data ?? []) as Record<string, unknown>[], loading: status.isLoading, error: status.error, onRetry: () => status.refetch() },
    entity: { columns: entityCols, data: (entity.data ?? []) as Record<string, unknown>[], loading: entity.isLoading, error: entity.error, onRetry: () => entity.refetch() },
    related: { columns: relatedCols, data: (related.data ?? []) as Record<string, unknown>[], loading: related.isLoading, error: related.error, onRetry: () => related.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="النسيج الذكي" description="إدارة النسيج الذكي" />
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
