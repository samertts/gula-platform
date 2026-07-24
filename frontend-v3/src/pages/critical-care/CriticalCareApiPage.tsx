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
    queryFn: () => api.get("/critical-care/vitals").then((r) => r.data),
  });
  const ventilator = useQuery({
    queryKey: ["criticalCareApi", "ventilator"],
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

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    admissions: { columns: admissionsCols, data: (admissions.data ?? []) as Record<string, unknown>[], loading: admissions.isLoading },
    availability: { columns: availabilityCols, data: (availability.data ?? []) as Record<string, unknown>[], loading: availability.isLoading },
    vitals: { columns: vitalsCols, data: (vitals.data ?? []) as Record<string, unknown>[], loading: vitals.isLoading },
    ventilator: { columns: ventilatorCols, data: (ventilator.data ?? []) as Record<string, unknown>[], loading: ventilator.isLoading },
    dashboard: { columns: dashboardCols, data: (dashboard.data ?? []) as Record<string, unknown>[], loading: dashboard.isLoading },
    health: { columns: healthCols, data: (health.data ?? []) as Record<string, unknown>[], loading: health.isLoading },
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
