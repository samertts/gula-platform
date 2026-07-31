import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Button, Card, CardContent, Dialog, Input, Select, Badge } from "@/components/ui";







import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Building2, Scale, Gavel, FileCheck, Ban } from "lucide-react";

type Authority = Record<string, unknown>;
type Council = Record<string, unknown>;
type Appeal = Record<string, unknown>;
type Suspension = Record<string, unknown>;
type Registry = Record<string, unknown>;

const tabs = [
  { id: "authorities", label: "السلطات", icon: Building2 },
  { id: "councils", label: "المجالس", icon: Scale },
  { id: "appeals", label: "الطعون", icon: Gavel },
  { id: "suspensions", label: "الإيقاف", icon: Ban },
  { id: "registries", label: "السجلات", icon: FileCheck },
] as const;

type TabId = (typeof tabs)[number]["id"];

const badgeVariant = (status: string) => {
  const map: Record<string, "success" | "warning" | "destructive" | "default"> = {
    active: "success",
    pending: "warning",
    suspended: "destructive",
    approved: "success",
    rejected: "destructive",
    draft: "default",
  };
  return map[status?.toLowerCase()] ?? "default";
};

export default function GovernancePage() {
  const [activeTab, setActiveTab] = useState<TabId>("authorities");
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const authorities = useQuery({
    queryKey: ["governance", "authorities"],
    queryFn: () => api.get("/niam/governance/authorities").then((r) => r.data),
  });

  const createAuthority = useMutation({
    mutationFn: (data: unknown) =>
      api.post("/niam/governance/authorities", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["governance"] });
     setDialogOpen(false);
    },
  });

  const councils = useQuery({
    queryKey: ["governance", "councils"],
    queryFn: () => api.get("/niam/governance/councils").then((r) => r.data),
  });

  const appeals = useQuery({
    queryKey: ["governance", "appeals"],
    queryFn: () => api.get("/niam/governance/appeals").then((r) => r.data),
  });

  const suspensions = useQuery({
    queryKey: ["governance", "suspensions"],
    queryFn: () => api.get("/niam/governance/suspensions/active").then((r) => r.data),
  });

  const registries = useQuery({
    queryKey: ["governance", "registries"],
    enabled: false,
    queryFn: () => api.get("/niam/governance/registries").then((r) => r.data),
  });

  const col = createColumnHelper<Authority>();

  const authorityColumns: ColumnDef<Authority, unknown>[] = [
    col.accessor("name_en", { header: "الاسم" }),
    col.accessor("authority_type", { header: "النوع" }),
    col.accessor("jurisdiction", { header: "الاختصاص" }),
    col.accessor("status", {
      header: "الحالة",
      cell: ({ getValue }) => {
        const v = getValue() as string;
        return <Badge variant={badgeVariant(v)}>{v}</Badge>;
      },
    }),
    col.accessor("established_at", {
      header: "تاريخ التأسيس",
      cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ"),
    }),
  ];

  const councilColumns: ColumnDef<Council, unknown>[] = [
    col.accessor("name_en", { header: "الاسم" }),
    col.accessor("council_type", { header: "النوع" }),
    col.accessor("status", {
      header: "الحالة",
      cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge>,
    }),
  ];

  const appealColumns: ColumnDef<Appeal, unknown>[] = [
    col.accessor("appeal_id", { header: "رقم الطعن" }),
    col.accessor("appeal_type", { header: "النوع" }),
    col.accessor("status", {
      header: "الحالة",
      cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge>,
    }),
    col.accessor("submitted_at", {
      header: "تاريخ التقديم",
      cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ"),
    }),
  ];

  const suspensionColumns: ColumnDef<Suspension, unknown>[] = [
    col.accessor("suspension_id", { header: "رقم الإيقاف" }),
    col.accessor("reason", { header: "السبب" }),
    col.accessor("status", {
      header: "الحالة",
      cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge>,
    }),
    col.accessor("suspended_at", {
      header: "تاريخ الإيقاف",
      cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ"),
    }),
  ];

  const registryColumns: ColumnDef<Registry, unknown>[] = [
    col.accessor("registry_type", { header: "نوع السجل" }),
    col.accessor("entity_type", { header: "نوع الكيان" }),
    col.accessor("status", {
      header: "الحالة",
      cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge>,
    }),
    col.accessor("registered_at", {
      header: "تاريخ التسجيل",
      cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ"),
    }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<unknown, unknown>[]; data: unknown[]; loading: boolean }> = {
    authorities: {
      columns: authorityColumns as ColumnDef<unknown, unknown>[],
      data: asTableData(authorities.data),
      loading: authorities.isLoading,
    },
    councils: {
      columns: councilColumns as ColumnDef<unknown, unknown>[],
      data: asTableData(councils.data),
      loading: councils.isLoading,
    },
    appeals: {
      columns: appealColumns as ColumnDef<unknown, unknown>[],
      data: asTableData(appeals.data),
      loading: appeals.isLoading,
    },
    suspensions: {
      columns: suspensionColumns as ColumnDef<unknown, unknown>[],
      data: asTableData(suspensions.data),
      loading: suspensions.isLoading,
    },
    registries: {
      columns: registryColumns as ColumnDef<unknown, unknown>[],
      data: asTableData(registries.data),
      loading: registries.isLoading,
    },
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="حوكمة الهوية الوطنية"
        description="إدارة سلطات الهوية والمجالس والطعون والسجلات"
        actions={
          <Button onClick={() =>setDialogOpen(true)}>إضافة سلطة</Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          <div className="flex border-b">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? "border-b-2 border-indigo-600 text-indigo-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
          <div className="p-4">
            <DataTable
              columns={tables[activeTab].columns}
              data={tables[activeTab].data as Record<string, unknown>[]}
              loading={tables[activeTab].loading}
            />
          </div>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <div className="space-y-4 p-6">
          <h2 className="text-lg font-semibold">إضافة سلطة هوية جديدة</h2>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              createAuthority.mutate(Object.fromEntries(fd));
            }}
            className="space-y-4"
          >
            <Input name="name_en" placeholder="الاسم (إنجليزي)" required />
            <Input name="name_ar" placeholder="الاسم (عربي)" required />
            <Select
              name="authority_type"
              options={[
                { label: "تسجيل", value: "registration" },
                { label: "تصديق", value: "certification" },
                { label: "رقابي", value: "supervisory" },
                { label: "تنظيمي", value: "regulatory" },
              ]}
              placeholder="نوع السلطة"
            />
            <Input name="jurisdiction" placeholder="الاختصاص" />
            <Button type="submit" loading={createAuthority.isPending}>
              حفظ
            </Button>
          </form>
        </div>
      </Dialog>
    </div>
  );
}
