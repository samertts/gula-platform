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
  { id: "appointments", label: "appointments", icon: FileText },
  { id: "slots", label: "slots", icon: Activity },
  { id: "resources", label: "resources", icon: List },
  { id: "schedules", label: "schedules", icon: ClipboardList },
  { id: "waiting-list", label: "waiting-list", icon: BookOpen },
  { id: "calendars", label: "calendars", icon:  FolderOpen },
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

export default function NationalSchedulingPlatformApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("appointments");
  const col = createColumnHelper<Record<string, unknown>>();

  const appointments = useQuery({
    queryKey: ["nationalSchedulingPlatformApi", "appointments"],
    queryFn: () => api.get("/national/scheduling/appointments").then((r) => r.data),
  });
  const slots = useQuery({
    queryKey: ["nationalSchedulingPlatformApi", "slots"],
    queryFn: () => api.get("/national/scheduling/availability/slots").then((r) => r.data),
  });
  const resources = useQuery({
    queryKey: ["nationalSchedulingPlatformApi", "resources"],
    queryFn: () => api.get("/national/scheduling/resources").then((r) => r.data),
  });
  const schedules = useQuery({
    queryKey: ["nationalSchedulingPlatformApi", "schedules"],
    enabled: false,
    queryFn: () => api.get("/national/scheduling/schedules").then((r) => r.data),
  });
  const waitingList = useQuery({
    queryKey: ["nationalSchedulingPlatformApi", "waiting-list"],
    queryFn: () => api.get("/national/scheduling/waiting-list").then((r) => r.data),
  });
  const calendars = useQuery({
    queryKey: ["nationalSchedulingPlatformApi", "calendars"],
    queryFn: () => api.get("/national/scheduling/calendars").then((r) => r.data),
  });

  const appointmentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const slotsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const resourcesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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
  const waitingListCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const calendarsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    appointments: { columns: appointmentsCols, data: asTableData(appointments.data), loading: appointments.isLoading, error: appointments.error, onRetry: () => appointments.refetch() },
    slots: { columns: slotsCols, data: asTableData(slots.data), loading: slots.isLoading, error: slots.error, onRetry: () => slots.refetch() },
    resources: { columns: resourcesCols, data: asTableData(resources.data), loading: resources.isLoading, error: resources.error, onRetry: () => resources.refetch() },
    schedules: { columns: schedulesCols, data: asTableData(schedules.data), loading: schedules.isLoading, error: schedules.error, onRetry: () => schedules.refetch() },
    "waiting-list": { columns: waitingListCols, data: asTableData(waitingList.data), loading: waitingList.isLoading, error: waitingList.error, onRetry: () => waitingList.refetch() },
    calendars: { columns: calendarsCols, data: asTableData(calendars.data), loading: calendars.isLoading, error: calendars.error, onRetry: () => calendars.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الجدولة الوطنية" description="إدارة الجدولة الوطنية" />
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
