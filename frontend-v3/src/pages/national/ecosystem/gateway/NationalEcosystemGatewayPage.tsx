import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Activity, FileText, List } from "lucide-react";

const tabs = [
  { id: "status", label: "status", icon: FileText },
  { id: "policies", label: "السياسات", icon: Activity },
  { id: "catalog", label: "الفهرس", icon: List },
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

export default function NationalEcosystemGatewayPage() {
  const [activeTab, setActiveTab] = useState<TabId>("status");
  const col = createColumnHelper<Record<string, unknown>>();

  const status = useQuery({
    queryKey: ["nationalEcosystemGateway", "status"],
    queryFn: () => api.get("/gateway/status").then((r) => r.data),
  });
  const policies = useQuery({
    queryKey: ["nationalEcosystemGateway", "policies"],
    queryFn: () => api.get("/gateway/policies").then((r) => r.data),
  });
  const catalog = useQuery({
    queryKey: ["nationalEcosystemGateway", "catalog"],
    queryFn: () => api.get("/gateway/catalog").then((r) => r.data),
  });

  const statusCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const policiesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const catalogCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    status: { columns: statusCols, data: (status.data ?? []) as Record<string, unknown>[], loading: status.isLoading },
    policies: { columns: policiesCols, data: (policies.data ?? []) as Record<string, unknown>[], loading: policies.isLoading },
    catalog: { columns: catalogCols, data: (catalog.data ?? []) as Record<string, unknown>[], loading: catalog.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="بوابة النظام البيئي" description="إدارة بوابة النظام البيئي" />
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
