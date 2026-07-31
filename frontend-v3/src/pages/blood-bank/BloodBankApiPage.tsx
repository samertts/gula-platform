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
  { id: "donors", label: "المتبرعون", icon: FileText },
  { id: "inventory", label: "المخزون", icon: Activity },
  { id: "critical", label: "critical", icon: List },
  { id: "compatible-groups", label: "compatible-groups", icon: ClipboardList },
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

export default function BloodBankApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("donors");
  const col = createColumnHelper<Record<string, unknown>>();

  const donors = useQuery({
    queryKey: ["bloodBankApi", "donors"],
    queryFn: () => api.get("/blood-bank/donors").then((r) => r.data),
  });
  const inventory = useQuery({
    queryKey: ["bloodBankApi", "inventory"],
    queryFn: () => api.get("/blood-bank/inventory").then((r) => r.data),
  });
  const critical = useQuery({
    queryKey: ["bloodBankApi", "critical"],
    queryFn: () => api.get("/blood-bank/inventory/critical").then((r) => r.data),
  });
  const compatibleGroups = useQuery({
    queryKey: ["bloodBankApi", "compatible-groups"],
    enabled: false,
    queryFn: () => api.get("/blood-bank/crossmatch/compatible-groups").then((r) => r.data),
  });
  const dashboard = useQuery({
    queryKey: ["bloodBankApi", "dashboard"],
    queryFn: () => api.get("/blood-bank/dashboard").then((r) => r.data),
  });
  const health = useQuery({
    queryKey: ["bloodBankApi", "health"],
    queryFn: () => api.get("/blood-bank/health").then((r) => r.data),
  });

  const donorsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const inventoryCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const criticalCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const compatibleGroupsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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
    donors: { columns: donorsCols, data: asTableData(donors.data), loading: donors.isLoading },
    inventory: { columns: inventoryCols, data: asTableData(inventory.data), loading: inventory.isLoading },
    critical: { columns: criticalCols, data: asTableData(critical.data), loading: critical.isLoading },
    "compatible-groups": { columns: compatibleGroupsCols, data: asTableData(compatibleGroups.data), loading: compatibleGroups.isLoading },
    dashboard: { columns: dashboardCols, data: asTableData(dashboard.data), loading: dashboard.isLoading },
    health: { columns: healthCols, data: asTableData(health.data), loading: health.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="بنك الدم" description="إدارة بنك الدم" />
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
