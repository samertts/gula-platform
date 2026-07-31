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
  { id: "rules", label: "rules", icon: FileText },
  { id: "versions", label: "versions", icon: Activity },
  { id: "evaluations", label: "evaluations", icon: List },
  { id: "categories", label: "categories", icon: ClipboardList },
  { id: "health", label: "الحالة", icon: BookOpen },
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

export default function NationalRulesEngineApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("rules");
  const col = createColumnHelper<Record<string, unknown>>();

  const rules = useQuery({
    queryKey: ["nationalRulesEngineApi", "rules"],
    queryFn: () => api.get("/national/rules").then((r) => r.data),
  });
  const versions = useQuery({
    queryKey: ["nationalRulesEngineApi", "versions"],
    enabled: false,
    queryFn: () => api.get("/national/rules//versions").then((r) => r.data),
  });
  const evaluations = useQuery({
    queryKey: ["nationalRulesEngineApi", "evaluations"],
    enabled: false,
    queryFn: () => api.get("/national/rules//evaluations").then((r) => r.data),
  });
  const categories = useQuery({
    queryKey: ["nationalRulesEngineApi", "categories"],
    queryFn: () => api.get("/national/rules/categories").then((r) => r.data),
  });
  const health = useQuery({
    queryKey: ["nationalRulesEngineApi", "health"],
    queryFn: () => api.get("/national/rules/health").then((r) => r.data),
  });

  const rulesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const versionsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const evaluationsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const categoriesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    rules: { columns: rulesCols, data: asTableData(rules.data), loading: rules.isLoading, error: rules.error, onRetry: () => rules.refetch() },
    versions: { columns: versionsCols, data: asTableData(versions.data), loading: versions.isLoading, error: versions.error, onRetry: () => versions.refetch() },
    evaluations: { columns: evaluationsCols, data: asTableData(evaluations.data), loading: evaluations.isLoading, error: evaluations.error, onRetry: () => evaluations.refetch() },
    categories: { columns: categoriesCols, data: asTableData(categories.data), loading: categories.isLoading, error: categories.error, onRetry: () => categories.refetch() },
    health: { columns: healthCols, data: asTableData(health.data), loading: health.isLoading, error: health.error, onRetry: () => health.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="محرك القواعد" description="إدارة محرك القواعد" />
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
            <DataTable columns={tables[activeTab].columns} data={tables[activeTab].data} loading={tables[activeTab].loading} error={tables[activeTab].error} onRetry={tables[activeTab].onRetry} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
