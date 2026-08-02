import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "components", label: "المكونات", icon: FileText },
  { id: "topology", label: "topology", icon: Activity },
  { id: "health", label: "الحالة", icon: List },
  { id: "config", label: "الإعدادات", icon: ClipboardList },
  { id: "policies", label: "السياسات", icon: BookOpen },
  { id: "nodes", label: "nodes", icon:  FolderOpen },
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

export default function ControlPlanePage() {
  const [activeTab, setActiveTab] = useState<TabId>("components");
  const col = createColumnHelper<Record<string, unknown>>();

  const components = useQuery({
    queryKey: ["controlPlane", "components"],
    queryFn: () => api.get("/control-plane/registry/components").then((r) => r.data),
  });
  const topology = useQuery({
    queryKey: ["controlPlane", "topology"],
    queryFn: () => api.get("/control-plane/registry/topology").then((r) => r.data),
  });
  const health = useQuery({
    queryKey: ["controlPlane", "health"],
    queryFn: () => api.get("/control-plane/health").then((r) => r.data),
  });
  const config = useQuery({
    queryKey: ["controlPlane", "config"],
    enabled: false,
    queryFn: () => api.get("/control-plane/config").then((r) => r.data),
  });
  const policies = useQuery({
    queryKey: ["controlPlane", "policies"],
    queryFn: () => api.get("/control-plane/policies").then((r) => r.data),
  });
  const nodes = useQuery({
    queryKey: ["controlPlane", "nodes"],
    queryFn: () => api.get("/control-plane/fleet/nodes").then((r) => r.data),
  });

  const componentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const topologyCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const healthCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const configCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const policiesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const nodesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    components: { columns: componentsCols, data: asTableData(components.data), loading: components.isLoading, error: components.error, onRetry: () => components.refetch() },
    topology: { columns: topologyCols, data: asTableData(topology.data), loading: topology.isLoading, error: topology.error, onRetry: () => topology.refetch() },
    health: { columns: healthCols, data: asTableData(health.data), loading: health.isLoading, error: health.error, onRetry: () => health.refetch() },
    config: { columns: configCols, data: asTableData(config.data), loading: config.isLoading, error: config.error, onRetry: () => config.refetch() },
    policies: { columns: policiesCols, data: asTableData(policies.data), loading: policies.isLoading, error: policies.error, onRetry: () => policies.refetch() },
    nodes: { columns: nodesCols, data: asTableData(nodes.data), loading: nodes.isLoading, error: nodes.error, onRetry: () => nodes.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="مستوى التحكم" description="إدارة مستوى التحكم" />
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
