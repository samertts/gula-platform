import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "jobs", label: "الوظائف", icon: FileText },
  { id: "executions", label: "executions", icon: Activity },
  { id: "schedules", label: "schedules", icon: List },
  { id: "stats", label: "stats", icon: ClipboardList },
  { id: "due", label: "due", icon: BookOpen },
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

export default function NationalBackgroundPlatformApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("jobs");
  const col = createColumnHelper<Record<string, unknown>>();

  const jobs = useQuery({
    queryKey: ["nationalBackgroundPlatformApi", "jobs"],
    queryFn: () => api.get("/national/jobs").then((r) => r.data),
  });
  const executions = useQuery({
    queryKey: ["nationalBackgroundPlatformApi", "executions"],
    queryFn: () => api.get("/national/jobs//executions").then((r) => r.data),
  });
  const schedules = useQuery({
    queryKey: ["nationalBackgroundPlatformApi", "schedules"],
    queryFn: () => api.get("/national/jobs//schedules").then((r) => r.data),
  });
  const stats = useQuery({
    queryKey: ["nationalBackgroundPlatformApi", "stats"],
    queryFn: () => api.get("/national/jobs/stats").then((r) => r.data),
  });
  const due = useQuery({
    queryKey: ["nationalBackgroundPlatformApi", "due"],
    queryFn: () => api.get("/national/jobs/due").then((r) => r.data),
  });
  const dashboard = useQuery({
    queryKey: ["nationalBackgroundPlatformApi", "dashboard"],
    queryFn: () => api.get("/national/jobs/dashboard").then((r) => r.data),
  });

  const jobsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const executionsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const schedulesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const statsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const dueCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    jobs: { columns: jobsCols, data: (jobs.data ?? []) as Record<string, unknown>[], loading: jobs.isLoading },
    executions: { columns: executionsCols, data: (executions.data ?? []) as Record<string, unknown>[], loading: executions.isLoading },
    schedules: { columns: schedulesCols, data: (schedules.data ?? []) as Record<string, unknown>[], loading: schedules.isLoading },
    stats: { columns: statsCols, data: (stats.data ?? []) as Record<string, unknown>[], loading: stats.isLoading },
    due: { columns: dueCols, data: (due.data ?? []) as Record<string, unknown>[], loading: due.isLoading },
    dashboard: { columns: dashboardCols, data: (dashboard.data ?? []) as Record<string, unknown>[], loading: dashboard.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الخلفية الوطنية" description="إدارة الخلفية الوطنية" />
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
