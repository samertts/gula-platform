import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Building2, Users, Building, UserCircle, Shield } from "lucide-react";

const tabs = [
  { id: "enterprise", label: "المؤسسات", icon: Building2 },
  { id: "workforce", label: "القوى العاملة", icon: Users },
  { id: "government", label: "التوظيف الحكومي", icon: Building },
  { id: "citizen", label: "المواطنون", icon: UserCircle },
  { id: "guardian", label: "الأوصياء", icon: Shield },
] as const;

type TabId = (typeof tabs)[number]["id"];

const badgeVariant = (s: string) => {
  const m: Record<string, "success" | "warning" | "destructive" | "default"> = {
    active: "success", approved: "success", activated: "success",
    pending: "warning", draft: "default", rejected: "destructive",
    terminated: "destructive", deactivated: "destructive",
  };
  return m[s?.toLowerCase()] ?? "default";
};

export default function LifecyclePage() {
  const [activeTab, setActiveTab] = useState<TabId>("enterprise");
  const col = createColumnHelper<Record<string, unknown>>();

  const enterprise = useQuery({
    queryKey: ["lifecycle", "enterprise"],
    enabled: false,
    queryFn: () => api.get("/niam/lifecycle/enterprise").then((r) => r.data),
  });

  const workforce = useQuery({
    queryKey: ["lifecycle", "workforce"],
    enabled: false,
    queryFn: () => api.get("/niam/lifecycle/workforce").then((r) => r.data),
  });

  const appointments = useQuery({
    queryKey: ["lifecycle", "government"],
    enabled: false,
    queryFn: () => api.get("/niam/lifecycle/government/appointments").then((r) => r.data),
  });

  const citizens = useQuery({
    queryKey: ["lifecycle", "citizen"],
    enabled: false,
    queryFn: () => api.get("/niam/lifecycle/citizen").then((r) => r.data),
  });

  const guardians = useQuery({
    queryKey: ["lifecycle", "guardian"],
    enabled: false,
    queryFn: () => api.get("/niam/lifecycle/guardians").then((r) => r.data),
  });

  const enterpriseCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("reg_id", { header: "رقم التسجيل" }),
    col.accessor("organization_id", { header: "المؤسسة" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("current_step", { header: "الخطوة الحالية" }),
    col.accessor("submitted_at", { header: "تاريخ التقديم", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const workforceCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("request_id", { header: "رقم الطلب" }),
    col.accessor("request_type", { header: "النوع" }),
    col.accessor("requesting_org_id", { header: "الجهة" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
  ];

  const govCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("appointment_id", { header: "رقم التعيين" }),
    col.accessor("person_id", { header: "الشخص" }),
    col.accessor("position", { header: "المنصب" }),
    col.accessor("grade", { header: "الدرجة" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
  ];

  const citizenCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("citizen_id", { header: "رقم المواطن" }),
    col.accessor("person_id", { header: "الشخص" }),
    col.accessor("health_id", { header: "الرقم الصحي" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("registration_date", { header: "تاريخ التسجيل", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const guardianCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("guardian_id", { header: "رقم الوصي" }),
    col.accessor("guardian_person_id", { header: "الوصي" }),
    col.accessor("dependent_person_id", { header: "المكفول" }),
    col.accessor("relationship", { header: "العلاقة" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    enterprise: { columns: enterpriseCols, data: asTableData(enterprise.data), loading: enterprise.isLoading, error: enterprise.error, onRetry: () => enterprise.refetch() },
    workforce: { columns: workforceCols, data: asTableData(workforce.data), loading: workforce.isLoading, error: workforce.error, onRetry: () => workforce.refetch() },
    government: { columns: govCols, data: asTableData(appointments.data), loading: appointments.isLoading, error: appointments.error, onRetry: () => appointments.refetch() },
    citizen: { columns: citizenCols, data: asTableData(citizens.data), loading: citizens.isLoading, error: citizens.error, onRetry: () => citizens.refetch() },
    guardian: { columns: guardianCols, data: asTableData(guardians.data), loading: guardians.isLoading, error: guardians.error, onRetry: () => guardians.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="دورة حياة الهوية" description="إدارة دورة حياة المؤسسات والقوى العاملة والمواطنين والأوصياء" />

      <Card>
        <CardContent className="p-0">
          <div className="flex border-b flex-wrap">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-indigo-600 text-indigo-600" : "text-gray-500 hover:text-gray-700"}`}>
                  <Icon className="h-4 w-4" />
                  {tab.label}
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
