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
  { id: "admissions", label: "القبول", icon: FileText },
  { id: "availability", label: "availability", icon: Activity },
  { id: "vitals", label: "العلامات الحيوية", icon: List },
  { id: "ventilator", label: "ventilator", icon: ClipboardList },
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

export default function CriticalCareApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("admissions");
  const col = createColumnHelper<Record<string, unknown>>();

  const admissions = useQuery({
    queryKey: ["criticalCareApi", "admissions"],
    queryFn: () => api.get("/critical-care/admissions").then((r) => r.data),
  });
  const availability = useQuery({
    queryKey: ["criticalCareApi", "availability"],
    queryFn: () => api.get("/critical-care/beds/availability").then((r) => r.data),
  });
  const vitals = useQuery({
    queryKey: ["criticalCareApi", "vitals"],
    enabled: false,
    queryFn: () => api.get("/critical-care/vitals").then((r) => r.data),
  });
  const ventilator = useQuery({
    queryKey: ["criticalCareApi", "ventilator"],
    enabled: false,
    queryFn: () => api.get("/critical-care/ventilator").then((r) => r.data),
  });
  const dashboard = useQuery({
    queryKey: ["criticalCareApi", "dashboard"],
    queryFn: () => api.get("/critical-care/dashboard").then((r) => r.data),
  });
  const health = useQuery({
    queryKey: ["criticalCareApi", "health"],
    queryFn: () => api.get("/critical-care/health").then((r) => r.data),
  });

  const admissionsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const availabilityCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const vitalsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const ventilatorCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    admissions: { columns: admissionsCols, data: asTableData(admissions.data), loading: admissions.isLoading, error: admissions.error, onRetry: () => admissions.refetch() },
    availability: { columns: availabilityCols, data: asTableData(availability.data), loading: availability.isLoading, error: availability.error, onRetry: () => availability.refetch() },
    vitals: { columns: vitalsCols, data: asTableData(vitals.data), loading: vitals.isLoading, error: vitals.error, onRetry: () => vitals.refetch() },
    ventilator: { columns: ventilatorCols, data: asTableData(ventilator.data), loading: ventilator.isLoading, error: ventilator.error, onRetry: () => ventilator.refetch() },
    dashboard: { columns: dashboardCols, data: asTableData(dashboard.data), loading: dashboard.isLoading, error: dashboard.error, onRetry: () => dashboard.refetch() },
    health: { columns: healthCols, data: asTableData(health.data), loading: health.isLoading, error: health.error, onRetry: () => health.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="العناية المركزة" description="إدارة العناية المركزة" />
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
