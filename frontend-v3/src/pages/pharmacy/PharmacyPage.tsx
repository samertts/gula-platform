import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "dispense-queue", label: "dispense-queue", icon: FileText },
  { id: "guidelines", label: "guidelines", icon: Activity },
  { id: "stock-levels", label: "stock-levels", icon: List },
  { id: "alerts", label: "التنبيهات", icon: ClipboardList },
  { id: "movements", label: "movements", icon: BookOpen },
  { id: "transfers", label: "transfers", icon:  FolderOpen },
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

export default function PharmacyPage() {
  const [activeTab, setActiveTab] = useState<TabId>("dispense-queue");
  const col = createColumnHelper<Record<string, unknown>>();

  const dispenseQueue = useQuery({
    queryKey: ["pharmacy", "dispense-queue"],
    queryFn: () => api.get("/pharmacy/dispense-queue").then((r) => r.data),
  });
  const guidelines = useQuery({
    queryKey: ["pharmacy", "guidelines"],
    queryFn: () => api.get("/pharmacy/clinical/guidelines").then((r) => r.data),
  });
  const stockLevels = useQuery({
    queryKey: ["pharmacy", "stock-levels"],
    queryFn: () => api.get("/pharmacy/inventory/stock-levels").then((r) => r.data),
  });
  const alerts = useQuery({
    queryKey: ["pharmacy", "alerts"],
    queryFn: () => api.get("/pharmacy/inventory/stock-levels/alerts").then((r) => r.data),
  });
  const movements = useQuery({
    queryKey: ["pharmacy", "movements"],
    queryFn: () => api.get("/pharmacy/inventory/movements").then((r) => r.data),
  });
  const transfers = useQuery({
    queryKey: ["pharmacy", "transfers"],
    queryFn: () => api.get("/pharmacy/inventory/transfers").then((r) => r.data),
  });

  const dispenseQueueCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const guidelinesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const stockLevelsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const alertsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const movementsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const transfersCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    "dispense-queue": { columns: dispenseQueueCols, data: (dispenseQueue.data ?? []) as Record<string, unknown>[], loading: dispenseQueue.isLoading },
    guidelines: { columns: guidelinesCols, data: (guidelines.data ?? []) as Record<string, unknown>[], loading: guidelines.isLoading },
    "stock-levels": { columns: stockLevelsCols, data: (stockLevels.data ?? []) as Record<string, unknown>[], loading: stockLevels.isLoading },
    alerts: { columns: alertsCols, data: (alerts.data ?? []) as Record<string, unknown>[], loading: alerts.isLoading },
    movements: { columns: movementsCols, data: (movements.data ?? []) as Record<string, unknown>[], loading: movements.isLoading },
    transfers: { columns: transfersCols, data: (transfers.data ?? []) as Record<string, unknown>[], loading: transfers.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الصيدلة" description="إدارة الصيدلة" />
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
