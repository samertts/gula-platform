import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { FolderOpen, Activity, BookOpen, ClipboardList, FileText, List, Pill } from "lucide-react";

const tabs = [
  { id: "dashboard", label: "لوحة القيادة", icon: FileText },
  { id: "profile", label: "الملف الشخصي", icon: Activity },
  { id: "health-summary", label: "ملخصي الصحي", icon: List },
  { id: "appointments", label: "مواعيدي", icon: ClipboardList },
  { id: "medications", label: "أدويتي", icon: BookOpen },
  { id: "medication-dispenses", label: "العلاجات المصروفة", icon: Pill },
  { id: "lab-results", label: "نتائج المختبر", icon: FolderOpen },
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
    queryFn: () => api.get("/citizen-platform/me/dashboard").then((r) => r.data),
  });
  const profile = useQuery({
    queryKey: ["citizenPlatform", "profile"],
    queryFn: () => api.get("/citizen-platform/me/profile").then((r) => r.data),
  });
  const healthSummary = useQuery({
    queryKey: ["citizenPlatform", "health-summary"],
    queryFn: () => api.get("/citizen-platform/me/health-summary").then((r) => r.data),
  });
  const appointments = useQuery({
    queryKey: ["citizenPlatform", "appointments"],
    queryFn: () => api.get("/citizen-platform/me/appointments").then((r) => r.data),
  });
  const medications = useQuery({
    queryKey: ["citizenPlatform", "medications"],
    queryFn: () => api.get("/citizen-platform/me/medications").then((r) => r.data),
  });
  const labResults = useQuery({
    queryKey: ["citizenPlatform", "lab-results"],
    queryFn: () => api.get("/citizen-platform/me/lab-results").then((r) => r.data),
  });
  const medicationDispenses = useQuery({
    queryKey: ["citizenPlatform", "medication-dispenses"],
    queryFn: () => api.get("/citizen-platform/me/medication-dispenses").then((r) => r.data as { dispenses?: Record<string, unknown>[] }),
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
  const medicationDispensesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("medication_name_ar", { header: "العلاج", cell: ({ row }) => row.original.medication_name_ar || row.original.medication_name || "—" }),
    col.accessor("quantity", { header: "الكمية" }),
    col.accessor("quantity_unit", { header: "الوحدة" }),
    col.accessor("lot_number", { header: "الدفعة" }),
    col.accessor("expiry_date", { header: "الصلاحية" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("dispensed_at", { header: "تاريخ الصرف", cell: ({ getValue }) => getValue() ? new Date(getValue() as string).toLocaleDateString("ar-IQ") : "—" }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    dashboard: { columns: dashboardCols, data: (dashboard.data ?? []) as Record<string, unknown>[], loading: dashboard.isLoading },
    profile: { columns: profileCols, data: (profile.data ?? []) as Record<string, unknown>[], loading: profile.isLoading },
    "health-summary": { columns: healthSummaryCols, data: (healthSummary.data ?? []) as Record<string, unknown>[], loading: healthSummary.isLoading },
    appointments: { columns: appointmentsCols, data: (appointments.data ?? []) as Record<string, unknown>[], loading: appointments.isLoading },
    medications: { columns: medicationsCols, data: (medications.data ?? []) as Record<string, unknown>[], loading: medications.isLoading },
    "medication-dispenses": { columns: medicationDispensesCols, data: (medicationDispenses.data?.dispenses ?? []) as Record<string, unknown>[], loading: medicationDispenses.isLoading },
    "lab-results": { columns: labResultsCols, data: (labResults.data ?? []) as Record<string, unknown>[], loading: labResults.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="مساحة المواطن" description="مساحة عمل صحية مرتبطة بحساب GULA الموحّد" />
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
