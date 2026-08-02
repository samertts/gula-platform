import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { kernelRuntimeApi } from "@/api/endpoints";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge, Button } from "@/components/ui";



import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List, Gauge, Play } from "lucide-react";

const tabs = [
  { id: "status", label: "status", icon: FileText },
  { id: "services", label: "الخدمات", icon: Activity },
  { id: "capabilities", label: "capabilities", icon: List },
  { id: "plugins", label: "الإضافات", icon: ClipboardList },
  { id: "modules", label: "الوحدات", icon: BookOpen },
  { id: "config", label: "الإعدادات", icon:  FolderOpen },
  { id: "runtime", label: "مراقبة النواة", icon: Gauge },
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

export default function KernelPage() {
  const [activeTab, setActiveTab] = useState<TabId>("status");
  const col = createColumnHelper<Record<string, unknown>>();

  const status = useQuery({
    queryKey: ["kernel", "status"],
    queryFn: () => api.get("/kernel/status").then((r) => r.data),
  });
  const services = useQuery({
    queryKey: ["kernel", "services"],
    queryFn: () => api.get("/kernel/services").then((r) => r.data),
  });
  const capabilities = useQuery({
    queryKey: ["kernel", "capabilities"],
    queryFn: () => api.get("/kernel/capabilities").then((r) => r.data),
  });
  const plugins = useQuery({
    queryKey: ["kernel", "plugins"],
    queryFn: () => api.get("/kernel/plugins").then((r) => r.data),
  });
  const modules = useQuery({
    queryKey: ["kernel", "modules"],
    queryFn: () => api.get("/kernel/modules").then((r) => r.data),
  });
  const config = useQuery({
    queryKey: ["kernel", "config"],
    queryFn: () => api.get("/kernel/config").then((r) => r.data),
  });
  const runtimeHealth = useQuery({
    queryKey: ["kernel", "runtime", "health"],
    queryFn: () => kernelRuntimeApi.health(),
    refetchInterval: 30000,
  });
  const runtimeResources = useQuery({
    queryKey: ["kernel", "runtime", "resources"],
    queryFn: () => kernelRuntimeApi.resources(),
    refetchInterval: 30000,
  });
  const slowQueries = useQuery({
    queryKey: ["kernel", "runtime", "slow-queries"],
    queryFn: () => kernelRuntimeApi.slowQueries(),
  });
  const validationReport = useQuery({
    queryKey: ["kernel", "runtime", "validation"],
    queryFn: () => kernelRuntimeApi.validationReport(),
  });
  const runValidationMutation = useMutation({
    mutationFn: () => kernelRuntimeApi.runValidation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kernel", "runtime", "validation"] });
    },
  });

  const queryClient = useQueryClient();

  const statusCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const servicesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const capabilitiesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const pluginsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const modulesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const configCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const slowQueriesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("query", { header: "الاستعلام" }),
    col.accessor("duration_ms", { header: "المدة (مللي ثانية)" }),
    col.accessor("count", { header: "العدد" }),
    col.accessor("last_seen", { header: "آخر ظهور", cell: ({ getValue }) => new Date(getValue() as string).toLocaleString("ar-IQ") }),
  ];

  const kvRows = (obj: Record<string, unknown> | undefined) =>
    obj
      ? Object.entries(obj).map(([k, v]) => ({
          key: k,
          value: typeof v === "object" ? JSON.stringify(v) : String(v ?? "-"),
        }))
      : [];

  const kvCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("key", { header: "المفتاح" }),
    col.accessor("value", { header: "القيمة", cell: ({ getValue }) => <span dir="ltr" className="font-mono text-sm">{getValue() as string}</span> }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    status: { columns: statusCols, data: (status.data ?? []) as Record<string, unknown>[], loading: status.isLoading, error: status.error, onRetry: () => status.refetch() },
    services: { columns: servicesCols, data: (services.data ?? []) as Record<string, unknown>[], loading: services.isLoading, error: services.error, onRetry: () => services.refetch() },
    capabilities: { columns: capabilitiesCols, data: (capabilities.data ?? []) as Record<string, unknown>[], loading: capabilities.isLoading, error: capabilities.error, onRetry: () => capabilities.refetch() },
    plugins: { columns: pluginsCols, data: (plugins.data ?? []) as Record<string, unknown>[], loading: plugins.isLoading, error: plugins.error, onRetry: () => plugins.refetch() },
    modules: { columns: modulesCols, data: (modules.data ?? []) as Record<string, unknown>[], loading: modules.isLoading, error: modules.error, onRetry: () => modules.refetch() },
    config: { columns: configCols, data: (config.data ?? []) as Record<string, unknown>[], loading: config.isLoading, error: config.error, onRetry: () => config.refetch() },
    runtime: { columns: kvCols, data: [], loading: false, error: null, onRetry: () => undefined },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="النواة" description="إدارة النواة" />
      <Card>
        <CardContent className="p-0">
          <div className="flex border-b flex-wrap">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} role="tab" aria-selected={activeTab === tab.id} onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-indigo-600 text-indigo-600" : "text-gray-500 hover:text-gray-700"}`}>
                  <Icon className="h-4 w-4" />{tab.label}
                </button>
              );
            })}
          </div>
          <div className="p-4">
            {activeTab === "runtime" ? (
              <div className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardContent className="space-y-3">
                      <div className="flex items-center gap-2 font-medium"><Activity className="h-4 w-4" /> صحة النواة</div>
                      <DataTable columns={kvCols} data={kvRows(runtimeHealth.data as Record<string, unknown>)} loading={runtimeHealth.isLoading} error={runtimeHealth.error} onRetry={() => runtimeHealth.refetch()} />
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="space-y-3">
                      <div className="flex items-center gap-2 font-medium"><Gauge className="h-4 w-4" /> الموارد</div>
                      <DataTable columns={kvCols} data={kvRows(runtimeResources.data as Record<string, unknown>)} loading={runtimeResources.isLoading} error={runtimeResources.error} onRetry={() => runtimeResources.refetch()} />
                    </CardContent>
                  </Card>
                </div>
                <Card>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 font-medium"><ClipboardList className="h-4 w-4" /> الاستعلامات البطيئة</div>
                      <Button size="sm" variant="outline" onClick={() => slowQueries.refetch()}><Activity className="h-4 w-4" /> تحديث</Button>
                    </div>
                    <DataTable columns={slowQueriesCols} data={(slowQueries.data as unknown as Record<string, unknown>[]) ?? []} loading={slowQueries.isLoading} error={slowQueries.error} onRetry={() => slowQueries.refetch()} />
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 font-medium"><Play className="h-4 w-4" /> تقرير التحقق</div>
                      <Button size="sm" onClick={() => runValidationMutation.mutate()} disabled={runValidationMutation.isPending}>
                        <Play className="h-4 w-4" /> تشغيل التحقق
                      </Button>
                    </div>
                    <DataTable columns={kvCols} data={kvRows(validationReport.data as Record<string, unknown>)} loading={validationReport.isLoading} error={validationReport.error} onRetry={() => validationReport.refetch()} />
                    {runValidationMutation.isError && (
                      <p className="text-sm text-destructive">فشل تشغيل التحقق</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : (
              <DataTable columns={tables[activeTab].columns} data={tables[activeTab].data} loading={tables[activeTab].loading} error={tables[activeTab].error} onRetry={tables[activeTab].onRetry} />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
