import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "devices", label: "الأجهزة", icon: FileText },
  { id: "pm", label: "pm", icon: Activity },
  { id: "calibration", label: "calibration", icon: List },
  { id: "work-orders", label: "work-orders", icon: ClipboardList },
  { id: "incidents", label: "الحوادث", icon: BookOpen },
  { id: "technicians", label: "الفنيون", icon:  FolderOpen },
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

export default function BiomedicalApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("devices");
  const col = createColumnHelper<Record<string, unknown>>();

  const devices = useQuery({
    queryKey: ["biomedicalApi", "devices"],
    queryFn: () => api.get("/biomedical/devices").then((r) => r.data),
  });
  const pm = useQuery({
    queryKey: ["biomedicalApi", "pm"],
    queryFn: () => api.get("/biomedical/devices/due/pm").then((r) => r.data),
  });
  const calibration = useQuery({
    queryKey: ["biomedicalApi", "calibration"],
    queryFn: () => api.get("/biomedical/devices/due/calibration").then((r) => r.data),
  });
  const workOrders = useQuery({
    queryKey: ["biomedicalApi", "work-orders"],
    queryFn: () => api.get("/biomedical/work-orders").then((r) => r.data),
  });
  const incidents = useQuery({
    queryKey: ["biomedicalApi", "incidents"],
    queryFn: () => api.get("/biomedical/incidents").then((r) => r.data),
  });
  const technicians = useQuery({
    queryKey: ["biomedicalApi", "technicians"],
    queryFn: () => api.get("/biomedical/technicians").then((r) => r.data),
  });

  const devicesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const pmCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const calibrationCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const workOrdersCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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
  const techniciansCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    devices: { columns: devicesCols, data: (devices.data ?? []) as Record<string, unknown>[], loading: devices.isLoading, error: devices.error, onRetry: () => devices.refetch() },
    pm: { columns: pmCols, data: (pm.data ?? []) as Record<string, unknown>[], loading: pm.isLoading, error: pm.error, onRetry: () => pm.refetch() },
    calibration: { columns: calibrationCols, data: (calibration.data ?? []) as Record<string, unknown>[], loading: calibration.isLoading, error: calibration.error, onRetry: () => calibration.refetch() },
    "work-orders": { columns: workOrdersCols, data: (workOrders.data ?? []) as Record<string, unknown>[], loading: workOrders.isLoading, error: workOrders.error, onRetry: () => workOrders.refetch() },
    incidents: { columns: incidentsCols, data: (incidents.data ?? []) as Record<string, unknown>[], loading: incidents.isLoading, error: incidents.error, onRetry: () => incidents.refetch() },
    technicians: { columns: techniciansCols, data: (technicians.data ?? []) as Record<string, unknown>[], loading: technicians.isLoading, error: technicians.error, onRetry: () => technicians.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الأجهزة الطبية" description="إدارة الأجهزة الطبية" />
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
