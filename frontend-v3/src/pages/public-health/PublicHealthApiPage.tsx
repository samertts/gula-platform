import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "disease-cases", label: "disease-cases", icon: FileText },
  { id: "stats", label: "stats", icon: Activity },
  { id: "outbreak-alerts", label: "outbreak-alerts", icon: List },
  { id: "surveillance-signals", label: "surveillance-signals", icon: ClipboardList },
  { id: "vaccinations", label: "vaccinations", icon: BookOpen },
  { id: "coverage", label: "coverage", icon:  FolderOpen },
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

export default function PublicHealthApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("disease-cases");
  const col = createColumnHelper<Record<string, unknown>>();

  const diseaseCases = useQuery({
    queryKey: ["publicHealthApi", "disease-cases"],
    queryFn: () => api.get("/public-health/disease-cases").then((r) => r.data),
  });
  const stats = useQuery({
    queryKey: ["publicHealthApi", "stats"],
    queryFn: () => api.get("/public-health/disease-cases/stats").then((r) => r.data),
  });
  const outbreakAlerts = useQuery({
    queryKey: ["publicHealthApi", "outbreak-alerts"],
    queryFn: () => api.get("/public-health/outbreak-alerts").then((r) => r.data),
  });
  const surveillanceSignals = useQuery({
    queryKey: ["publicHealthApi", "surveillance-signals"],
    queryFn: () => api.get("/public-health/surveillance-signals").then((r) => r.data),
  });
  const vaccinations = useQuery({
    queryKey: ["publicHealthApi", "vaccinations"],
    queryFn: () => api.get("/public-health/vaccinations").then((r) => r.data),
  });
  const coverage = useQuery({
    queryKey: ["publicHealthApi", "coverage"],
    queryFn: () => api.get("/public-health/vaccinations/coverage").then((r) => r.data),
  });

  const diseaseCasesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const statsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const outbreakAlertsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const surveillanceSignalsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const vaccinationsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const coverageCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    "disease-cases": { columns: diseaseCasesCols, data: (diseaseCases.data ?? []) as Record<string, unknown>[], loading: diseaseCases.isLoading },
    stats: { columns: statsCols, data: (stats.data ?? []) as Record<string, unknown>[], loading: stats.isLoading },
    "outbreak-alerts": { columns: outbreakAlertsCols, data: (outbreakAlerts.data ?? []) as Record<string, unknown>[], loading: outbreakAlerts.isLoading },
    "surveillance-signals": { columns: surveillanceSignalsCols, data: (surveillanceSignals.data ?? []) as Record<string, unknown>[], loading: surveillanceSignals.isLoading },
    vaccinations: { columns: vaccinationsCols, data: (vaccinations.data ?? []) as Record<string, unknown>[], loading: vaccinations.isLoading },
    coverage: { columns: coverageCols, data: (coverage.data ?? []) as Record<string, unknown>[], loading: coverage.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الصحة العامة" description="إدارة الصحة العامة" />
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
