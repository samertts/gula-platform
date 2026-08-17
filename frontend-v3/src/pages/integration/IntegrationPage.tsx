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
  { id: "gateways", label: "البوابات", icon: FileText },
  { id: "gateway", label: "gateway", icon: Activity },
  { id: "catalog", label: "الفهرس", icon: List },
  { id: "connectors", label: "الموصلات", icon: ClipboardList },
  { id: "standards", label: "المعايير", icon: BookOpen },
  { id: "dashboard", label: "لوحة القيادة", icon:  FolderOpen },
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

export default function IntegrationPage() {
  const [activeTab, setActiveTab] = useState<TabId>("gateways");
  const col = createColumnHelper<Record<string, unknown>>();

  const gateways = useQuery({
    queryKey: ["integration", "gateways"],
    queryFn: () => api.get("/integration/gateways").then((r) => r.data),
  });
  const gateway = useQuery({
    queryKey: ["integration", "gateway"],
    queryFn: () => api.get("/integration/gateways").then((r) => r.data),
  });
  const catalog = useQuery({
    queryKey: ["integration", "catalog"],
    queryFn: () => api.get("/integration/catalog").then((r) => r.data),
  });
  const connectors = useQuery({
    queryKey: ["integration", "connectors"],
    queryFn: () => api.get("/integration/connectors").then((r) => r.data),
  });
  const standards = useQuery({
    queryKey: ["integration", "standards"],
    queryFn: () => api.get("/integration/standards").then((r) => r.data),
  });
  const dashboard = useQuery({
    queryKey: ["integration", "dashboard"],
    queryFn: () => api.get("/integration/monitoring/dashboard").then((r) => r.data),
    staleTime: 30_000,
  });
  const ehr = useQuery({
    queryKey: ["integration", "ehr", "status"],
    queryFn: () => api.get("/integrations/ehr/status").then((r) => r.data as { enabled: boolean; health_status: string; readiness?: { ready: boolean; checks?: Record<string, boolean> } }),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
  const ehrOutbox = useQuery({
    queryKey: ["integration", "ehr", "outbox"],
    queryFn: () => api.get("/integrations/ehr/outbox/metrics").then((r) => r.data as { pending: number; failed: number; processing: number; dead_letter: number; oldest_pending_age_seconds: number }),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });

  const gatewaysCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const gatewayCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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
  const connectorsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const standardsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
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

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    gateways: { columns: gatewaysCols, data: (gateways.data ?? []) as Record<string, unknown>[], loading: gateways.isLoading },
    gateway: { columns: gatewayCols, data: (gateway.data ?? []) as Record<string, unknown>[], loading: gateway.isLoading },
    catalog: { columns: catalogCols, data: (catalog.data ?? []) as Record<string, unknown>[], loading: catalog.isLoading },
    connectors: { columns: connectorsCols, data: (connectors.data ?? []) as Record<string, unknown>[], loading: connectors.isLoading },
    standards: { columns: standardsCols, data: (standards.data ?? []) as Record<string, unknown>[], loading: standards.isLoading },
    dashboard: { columns: dashboardCols, data: (dashboard.data ?? []) as Record<string, unknown>[], loading: dashboard.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="التكامل" description="إدارة التكامل" />
      <Card className="border-sky-200 bg-sky-50/40">
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
          <div dir="rtl" className="contents">
          <div>
            <h2 className="font-semibold text-slate-900">تكامل السجل الصحي الإلكتروني</h2>
            <p className="mt-1 text-sm text-slate-600">يُفعّل تلقائياً فقط بعد اجتياز العقد والموافقة ومرجع الثقة. لا تعرض هذه البطاقة أسرار الاتصال.</p>
          </div>
          <div className="text-right text-sm">
            <span className={`inline-flex rounded-full px-3 py-1 font-medium ${ehr.data?.enabled ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
              {ehr.data?.enabled ? "مفعّل" : "محجوب حتى اكتمال التحقق"}
            </span>
            <p className="mt-2 text-xs text-slate-500">حالة الفحص: {ehr.data?.health_status ?? (ehr.isLoading ? "جارٍ الفحص" : "غير متاح")}</p>
            <p className="mt-1 text-xs text-slate-500">Outbox: {ehrOutbox.data?.pending ?? 0} قيد الانتظار، {ehrOutbox.data?.dead_letter ?? 0} معزولة، أقدمها {Math.floor((ehrOutbox.data?.oldest_pending_age_seconds ?? 0) / 60)} دقيقة</p>
          </div>
        </div>
        </CardContent>
      </Card>
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
