import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "gateways", label: "البوابات", icon: FileText },
  { id: "gateway", label: "gateway", icon: Activity },
  { id: "catalog", label: "الفهرس", icon: List },
  { id: "connectors", label: "الموصلات", icon: ClipboardList },
  { id: "standards", label: "المعايير", icon: BookOpen },
  { id: "dashboard", label: "لوحة القيادة", icon:  FolderOpen },
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

export default function IntegrationPage() {
  const [activeTab, setActiveTab] = useState<TabId>("gateways");
  const col = createColumnHelper<Record<string, unknown>>();

  const gateways = useQuery({
    queryKey: ["integration", "gateways"],
    queryFn: () => api.get("/integration/gateways").then((r) => r.data),
  });
  const gateway = useQuery({
    queryKey: ["integration", "gateway"],
    queryFn: () => api.get("/integration/gateways").then((r) => r.data),
  });
  const catalog = useQuery({
    queryKey: ["integration", "catalog"],
    queryFn: () => api.get("/integration/catalog").then((r) => r.data),
  });
  const connectors = useQuery({
    queryKey: ["integration", "connectors"],
    queryFn: () => api.get("/integration/connectors").then((r) => r.data),
  });
  const standards = useQuery({
    queryKey: ["integration", "standards"],
    queryFn: () => api.get("/integration/standards").then((r) => r.data),
  });
  const dashboard = useQuery({
    queryKey: ["integration", "dashboard"],
    queryFn: () => api.get("/integration/monitoring/dashboard").then((r) => r.data),
  });

  const gatewaysCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const gatewayCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const catalogCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const connectorsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const standardsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    gateways: { columns: gatewaysCols, data: (gateways.data ?? []) as Record<string, unknown>[], loading: gateways.isLoading, error: gateways.error, onRetry: () => gateways.refetch() },
    gateway: { columns: gatewayCols, data: (gateway.data ?? []) as Record<string, unknown>[], loading: gateway.isLoading, error: gateway.error, onRetry: () => gateway.refetch() },
    catalog: { columns: catalogCols, data: (catalog.data ?? []) as Record<string, unknown>[], loading: catalog.isLoading, error: catalog.error, onRetry: () => catalog.refetch() },
    connectors: { columns: connectorsCols, data: (connectors.data ?? []) as Record<string, unknown>[], loading: connectors.isLoading, error: connectors.error, onRetry: () => connectors.refetch() },
    standards: { columns: standardsCols, data: (standards.data ?? []) as Record<string, unknown>[], loading: standards.isLoading, error: standards.error, onRetry: () => standards.refetch() },
    dashboard: { columns: dashboardCols, data: (dashboard.data ?? []) as Record<string, unknown>[], loading: dashboard.isLoading, error: dashboard.error, onRetry: () => dashboard.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="التكامل" description="إدارة التكامل" />
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
