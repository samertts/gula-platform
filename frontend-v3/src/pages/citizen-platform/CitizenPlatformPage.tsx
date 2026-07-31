import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "dashboard", label: "لوحة القيادة", icon: FileText },
  { id: "profile", label: "profile", icon: Activity },
  { id: "health-summary", label: "health-summary", icon: List },
  { id: "appointments", label: "appointments", icon: ClipboardList },
  { id: "medications", label: "medications", icon: BookOpen },
  { id: "lab-results", label: "lab-results", icon:  FolderOpen },
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

export default function CitizenPlatformPage() {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const col = createColumnHelper<Record<string, unknown>>();

  const dashboard = useQuery({
    queryKey: ["citizenPlatform", "dashboard"],
    enabled: false,
    queryFn: () => api.get("/citizen-platform/dashboard").then((r) => r.data),
  });
  const profile = useQuery({
    queryKey: ["citizenPlatform", "profile"],
    enabled: false,
    queryFn: () => api.get("/citizen-platform/profile").then((r) => r.data),
  });
  const healthSummary = useQuery({
    queryKey: ["citizenPlatform", "health-summary"],
    enabled: false,
    queryFn: () => api.get("/citizen-platform/health-summary").then((r) => r.data),
  });
  const appointments = useQuery({
    queryKey: ["citizenPlatform", "appointments"],
    enabled: false,
    queryFn: () => api.get("/citizen-platform/appointments").then((r) => r.data),
  });
  const medications = useQuery({
    queryKey: ["citizenPlatform", "medications"],
    enabled: false,
    queryFn: () => api.get("/citizen-platform/medications").then((r) => r.data),
  });
  const labResults = useQuery({
    queryKey: ["citizenPlatform", "lab-results"],
    enabled: false,
    queryFn: () => api.get("/citizen-platform/lab-results").then((r) => r.data),
  });

  const dashboardCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const profileCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const healthSummaryCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const appointmentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const medicationsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const labResultsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    dashboard: { columns: dashboardCols, data: asTableData(dashboard.data), loading: dashboard.isLoading },
    profile: { columns: profileCols, data: asTableData(profile.data), loading: profile.isLoading },
    "health-summary": { columns: healthSummaryCols, data: asTableData(healthSummary.data), loading: healthSummary.isLoading },
    appointments: { columns: appointmentsCols, data: asTableData(appointments.data), loading: appointments.isLoading },
    medications: { columns: medicationsCols, data: asTableData(medications.data), loading: medications.isLoading },
    "lab-results": { columns: labResultsCols, data: asTableData(labResults.data), loading: labResults.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="منصة المواطن" description="إدارة منصة المواطن" />
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
