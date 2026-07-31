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
  { id: "catalog", label: "الفهرس", icon: FileText },
  { id: "lineage", label: "النسب", icon: Activity },
  { id: "policies", label: "السياسات", icon: List },
  { id: "metrics", label: "metrics", icon: ClipboardList },
  { id: "events", label: "الأحداث", icon: BookOpen },
  { id: "query", label: "query", icon:  FolderOpen },
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

export default function HealthDataPage() {
  const [activeTab, setActiveTab] = useState<TabId>("catalog");
  const col = createColumnHelper<Record<string, unknown>>();

  const catalog = useQuery({
    queryKey: ["healthData", "catalog"],
    queryFn: () => api.get("/health-data/catalog").then((r) => r.data),
  });
  const lineage = useQuery({
    queryKey: ["healthData", "lineage"],
    enabled: false,
    queryFn: () => api.get("/health-data/lineage").then((r) => r.data),
  });
  const policies = useQuery({
    queryKey: ["healthData", "policies"],
    queryFn: () => api.get("/health-data/governance/policies").then((r) => r.data),
  });
  const metrics = useQuery({
    queryKey: ["healthData", "metrics"],
    queryFn: () => api.get("/health-data/quality/metrics").then((r) => r.data),
  });
  const events = useQuery({
    queryKey: ["healthData", "events"],
    queryFn: () => api.get("/health-data/event-store/events").then((r) => r.data),
  });
  const query = useQuery({
    queryKey: ["healthData", "query"],
    queryFn: () => api.get("/health-data/warehouse/query").then((r) => r.data),
  });

  const catalogCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const lineageCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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
  const metricsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const eventsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const queryCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    catalog: { columns: catalogCols, data: asTableData(catalog.data), loading: catalog.isLoading, error: catalog.error, onRetry: () => catalog.refetch() },
    lineage: { columns: lineageCols, data: asTableData(lineage.data), loading: lineage.isLoading, error: lineage.error, onRetry: () => lineage.refetch() },
    policies: { columns: policiesCols, data: asTableData(policies.data), loading: policies.isLoading, error: policies.error, onRetry: () => policies.refetch() },
    metrics: { columns: metricsCols, data: asTableData(metrics.data), loading: metrics.isLoading, error: metrics.error, onRetry: () => metrics.refetch() },
    events: { columns: eventsCols, data: asTableData(events.data), loading: events.isLoading, error: events.error, onRetry: () => events.refetch() },
    query: { columns: queryCols, data: asTableData(query.data), loading: query.isLoading, error: query.error, onRetry: () => query.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="البيانات الصحية" description="إدارة البيانات الصحية" />
      <Card>
        <CardContent className="p-0">
          <div className="flex border-b flex-wrap">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
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
