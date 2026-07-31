import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "connectors", label: "الموصلات", icon: FileText },
  { id: "health", label: "الحالة", icon: Activity },
  { id: "schemas", label: "المخططات", icon: List },
  { id: "partners", label: "partners", icon: ClipboardList },
  { id: "audit", label: "التدقيق", icon: BookOpen },
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

export default function NationalEcosystemPage() {
  const [activeTab, setActiveTab] = useState<TabId>("connectors");
  const col = createColumnHelper<Record<string, unknown>>();

  const connectors = useQuery({
    queryKey: ["nationalEcosystem", "connectors"],
    queryFn: () => api.get("/ecosystem/connectors").then((r) => r.data),
  });
  const health = useQuery({
    queryKey: ["nationalEcosystem", "health"],
    enabled: false,
    queryFn: () => api.get("/ecosystem/connectors//health").then((r) => r.data),
  });
  const schemas = useQuery({
    queryKey: ["nationalEcosystem", "schemas"],
    queryFn: () => api.get("/ecosystem/schemas").then((r) => r.data),
  });
  const partners = useQuery({
    queryKey: ["nationalEcosystem", "partners"],
    queryFn: () => api.get("/ecosystem/partners").then((r) => r.data),
  });
  const audit = useQuery({
    queryKey: ["nationalEcosystem", "audit"],
    enabled: false,
    queryFn: () => api.get("/ecosystem/partners//audit").then((r) => r.data),
  });

  const connectorsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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
  const schemasCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const partnersCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const auditCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    connectors: { columns: connectorsCols, data: asTableData(connectors.data), loading: connectors.isLoading },
    health: { columns: healthCols, data: asTableData(health.data), loading: health.isLoading },
    schemas: { columns: schemasCols, data: asTableData(schemas.data), loading: schemas.isLoading },
    partners: { columns: partnersCols, data: asTableData(partners.data), loading: partners.isLoading },
    audit: { columns: auditCols, data: asTableData(audit.data), loading: audit.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="النظام البيئي" description="إدارة النظام البيئي" />
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
