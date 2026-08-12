import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "status", label: "status", icon: FileText },
  { id: "services", label: "الخدمات", icon: Activity },
  { id: "capabilities", label: "capabilities", icon: List },
  { id: "plugins", label: "الإضافات", icon: ClipboardList },
  { id: "modules", label: "الوحدات", icon: BookOpen },
  { id: "config", label: "الإعدادات", icon:  FolderOpen },
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

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    status: { columns: statusCols, data: (status.data ?? []) as Record<string, unknown>[], loading: status.isLoading },
    services: { columns: servicesCols, data: (services.data ?? []) as Record<string, unknown>[], loading: services.isLoading },
    capabilities: { columns: capabilitiesCols, data: (capabilities.data ?? []) as Record<string, unknown>[], loading: capabilities.isLoading },
    plugins: { columns: pluginsCols, data: (plugins.data ?? []) as Record<string, unknown>[], loading: plugins.isLoading },
    modules: { columns: modulesCols, data: (modules.data ?? []) as Record<string, unknown>[], loading: modules.isLoading },
    config: { columns: configCols, data: (config.data ?? []) as Record<string, unknown>[], loading: config.isLoading },
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
