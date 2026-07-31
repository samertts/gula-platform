import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "emergencies", label: "emergencies", icon: FileText },
  { id: "resource-requests", label: "resource-requests", icon: Activity },
  { id: "situation-reports", label: "situation-reports", icon: List },
  { id: "after-action-reports", label: "after-action-reports", icon: ClipboardList },
  { id: "dashboard", label: "لوحة القيادة", icon: BookOpen },
  { id: "health", label: "الحالة", icon:  FolderOpen },
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

export default function CommandCenterApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("emergencies");
  const col = createColumnHelper<Record<string, unknown>>();

  const emergencies = useQuery({
    queryKey: ["commandCenterApi", "emergencies"],
    queryFn: () => api.get("/command-center/emergencies").then((r) => r.data),
  });
  const resourceRequests = useQuery({
    queryKey: ["commandCenterApi", "resource-requests"],
    queryFn: () => api.get("/command-center/resource-requests").then((r) => r.data),
  });
  const situationReports = useQuery({
    queryKey: ["commandCenterApi", "situation-reports"],
    queryFn: () => api.get("/command-center/situation-reports").then((r) => r.data),
  });
  const afterActionReports = useQuery({
    queryKey: ["commandCenterApi", "after-action-reports"],
    queryFn: () => api.get("/command-center/after-action-reports").then((r) => r.data),
  });
  const dashboard = useQuery({
    queryKey: ["commandCenterApi", "dashboard"],
    queryFn: () => api.get("/command-center/dashboard").then((r) => r.data),
  });
  const health = useQuery({
    queryKey: ["commandCenterApi", "health"],
    queryFn: () => api.get("/command-center/health").then((r) => r.data),
  });

  const emergenciesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const resourceRequestsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const situationReportsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const afterActionReportsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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
  const healthCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    emergencies: { columns: emergenciesCols, data: (emergencies.data ?? []) as Record<string, unknown>[], loading: emergencies.isLoading },
    "resource-requests": { columns: resourceRequestsCols, data: (resourceRequests.data ?? []) as Record<string, unknown>[], loading: resourceRequests.isLoading },
    "situation-reports": { columns: situationReportsCols, data: (situationReports.data ?? []) as Record<string, unknown>[], loading: situationReports.isLoading },
    "after-action-reports": { columns: afterActionReportsCols, data: (afterActionReports.data ?? []) as Record<string, unknown>[], loading: afterActionReports.isLoading },
    dashboard: { columns: dashboardCols, data: (dashboard.data ?? []) as Record<string, unknown>[], loading: dashboard.isLoading },
    health: { columns: healthCols, data: (health.data ?? []) as Record<string, unknown>[], loading: health.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="مركز القيادة" description="إدارة مركز القيادة" />
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
            <DataTable columns={tables[activeTab].columns} data={tables[activeTab].data} loading={tables[activeTab].loading} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
