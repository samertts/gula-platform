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
  { id: "situation-room", label: "situation-room", icon: FileText },
  { id: "kpis", label: "kpis", icon: Activity },
  { id: "trend", label: "trend", icon: List },
  { id: "incidents", label: "الحوادث", icon: ClipboardList },
  { id: "capacity", label: "capacity", icon: BookOpen },
  { id: "executive-dashboard", label: "executive-dashboard", icon:  FolderOpen },
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

export default function CommandIntelligencePage() {
  const [activeTab, setActiveTab] = useState<TabId>("situation-room");
  const col = createColumnHelper<Record<string, unknown>>();

  const situationRoom = useQuery({
    queryKey: ["commandIntelligence", "situation-room"],
    queryFn: () => api.get("/intelligence/situation-room").then((r) => r.data),
  });
  const kpis = useQuery({
    queryKey: ["commandIntelligence", "kpis"],
    queryFn: () => api.get("/intelligence/kpis").then((r) => r.data),
  });
  const trend = useQuery({
    queryKey: ["commandIntelligence", "trend"],
    enabled: false,
    queryFn: () => api.get("/intelligence/kpis//trend").then((r) => r.data),
  });
  const incidents = useQuery({
    queryKey: ["commandIntelligence", "incidents"],
    queryFn: () => api.get("/intelligence/incidents").then((r) => r.data),
  });
  const capacity = useQuery({
    queryKey: ["commandIntelligence", "capacity"],
    queryFn: () => api.get("/intelligence/capacity").then((r) => r.data),
  });
  const executiveDashboard = useQuery({
    queryKey: ["commandIntelligence", "executive-dashboard"],
    queryFn: () => api.get("/intelligence/executive-dashboard").then((r) => r.data),
  });

  const situationRoomCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const kpisCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const trendCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const incidentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const capacityCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const executiveDashboardCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    "situation-room": { columns: situationRoomCols, data: asTableData(situationRoom.data), loading: situationRoom.isLoading, error: situationRoom.error, onRetry: () => situationRoom.refetch() },
    kpis: { columns: kpisCols, data: asTableData(kpis.data), loading: kpis.isLoading, error: kpis.error, onRetry: () => kpis.refetch() },
    trend: { columns: trendCols, data: asTableData(trend.data), loading: trend.isLoading, error: trend.error, onRetry: () => trend.refetch() },
    incidents: { columns: incidentsCols, data: asTableData(incidents.data), loading: incidents.isLoading, error: incidents.error, onRetry: () => incidents.refetch() },
    capacity: { columns: capacityCols, data: asTableData(capacity.data), loading: capacity.isLoading, error: capacity.error, onRetry: () => capacity.refetch() },
    "executive-dashboard": { columns: executiveDashboardCols, data: asTableData(executiveDashboard.data), loading: executiveDashboard.isLoading, error: executiveDashboard.error, onRetry: () => executiveDashboard.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الاستخبارات" description="إدارة الاستخبارات" />
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
