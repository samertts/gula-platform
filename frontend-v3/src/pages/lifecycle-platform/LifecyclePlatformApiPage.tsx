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
  { id: "components", label: "المكونات", icon: FileText },
  { id: "name", label: "name", icon: Activity },
  { id: "releases", label: "الإصدارات", icon: List },
  { id: "check", label: "check", icon: ClipboardList },
  { id: "compatibility", label: "التوافق", icon: BookOpen },
  { id: "upgrade-paths", label: "upgrade-paths", icon:  FolderOpen },
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

export default function LifecyclePlatformApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("components");
  const col = createColumnHelper<Record<string, unknown>>();

  const components = useQuery({
    queryKey: ["lifecyclePlatformApi", "components"],
    queryFn: () => api.get("/lifecycle/components").then((r) => r.data),
  });
  const name = useQuery({
    queryKey: ["lifecyclePlatformApi", "name"],
    enabled: false,
    queryFn: () => api.get("/lifecycle/components/name").then((r) => r.data),
  });
  const releases = useQuery({
    queryKey: ["lifecyclePlatformApi", "releases"],
    queryFn: () => api.get("/lifecycle/releases").then((r) => r.data),
  });
  const check = useQuery({
    queryKey: ["lifecyclePlatformApi", "check"],
    queryFn: () => api.get("/lifecycle/compatibility/check").then((r) => r.data),
  });
  const compatibility = useQuery({
    queryKey: ["lifecyclePlatformApi", "compatibility"],
    queryFn: () => api.get("/lifecycle/compatibility/check").then((r) => r.data),
  });
  const upgradePaths = useQuery({
    queryKey: ["lifecyclePlatformApi", "upgrade-paths"],
    queryFn: () => api.get("/lifecycle/upgrade-paths").then((r) => r.data),
  });

  const componentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const nameCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const releasesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const checkCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const compatibilityCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const upgradePathsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    components: { columns: componentsCols, data: asTableData(components.data), loading: components.isLoading, error: components.error, onRetry: () => components.refetch() },
    name: { columns: nameCols, data: asTableData(name.data), loading: name.isLoading, error: name.error, onRetry: () => name.refetch() },
    releases: { columns: releasesCols, data: asTableData(releases.data), loading: releases.isLoading, error: releases.error, onRetry: () => releases.refetch() },
    check: { columns: checkCols, data: asTableData(check.data), loading: check.isLoading, error: check.error, onRetry: () => check.refetch() },
    compatibility: { columns: compatibilityCols, data: asTableData(compatibility.data), loading: compatibility.isLoading, error: compatibility.error, onRetry: () => compatibility.refetch() },
    "upgrade-paths": { columns: upgradePathsCols, data: asTableData(upgradePaths.data), loading: upgradePaths.isLoading, error: upgradePaths.error, onRetry: () => upgradePaths.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="دورة حياة المنصة" description="إدارة دورة حياة المنصة" />
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
