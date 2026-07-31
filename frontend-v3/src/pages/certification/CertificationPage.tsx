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
import { Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "level", label: "level", icon: FileText },
  { id: "report", label: "report", icon: Activity },
  { id: "metrics", label: "metrics", icon: List },
  { id: "dimensions", label: "dimensions", icon: ClipboardList },
  { id: "checks", label: "checks", icon: BookOpen },
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

export default function CertificationPage() {
  const [activeTab, setActiveTab] = useState<TabId>("level");
  const col = createColumnHelper<Record<string, unknown>>();

  const level = useQuery({
    queryKey: ["certification", "level"],
    enabled: false,
    queryFn: () => api.get("/certification/level").then((r) => r.data),
  });
  const report = useQuery({
    queryKey: ["certification", "report"],
    enabled: false,
    queryFn: () => api.get("/certification/report").then((r) => r.data),
  });
  const metrics = useQuery({
    queryKey: ["certification", "metrics"],
    queryFn: () => api.get("/certification/metrics").then((r) => r.data),
  });
  const dimensions = useQuery({
    queryKey: ["certification", "dimensions"],
    queryFn: () => api.get("/certification/dimensions").then((r) => r.data),
  });
  const checks = useQuery({
    queryKey: ["certification", "checks"],
    enabled: false,
    queryFn: () => api.get("/certification/dimensions//checks").then((r) => r.data),
  });

  const levelCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const reportCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const metricsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const dimensionsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const checksCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    level: { columns: levelCols, data: asTableData(level.data), loading: level.isLoading },
    report: { columns: reportCols, data: asTableData(report.data), loading: report.isLoading },
    metrics: { columns: metricsCols, data: asTableData(metrics.data), loading: metrics.isLoading },
    dimensions: { columns: dimensionsCols, data: asTableData(dimensions.data), loading: dimensions.isLoading },
    checks: { columns: checksCols, data: asTableData(checks.data), loading: checks.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="التصديق" description="إدارة التصديق" />
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
