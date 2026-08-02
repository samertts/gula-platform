import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "incidents", label: "الحوادث", icon: FileText },
  { id: "ambulances", label: "الإسعاف", icon: Activity },
  { id: "crew", label: "الطاقم", icon: List },
  { id: "triage", label: "الفرز", icon: ClipboardList },
  { id: "epcr", label: "السجلات", icon: BookOpen },
  { id: "nearby", label: "nearby", icon:  FolderOpen },
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

export default function EmsApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("incidents");
  const col = createColumnHelper<Record<string, unknown>>();

  const incidents = useQuery({
    queryKey: ["emsApi", "incidents"],
    queryFn: () => api.get("/ems/incidents").then((r) => r.data),
  });
  const ambulances = useQuery({
    queryKey: ["emsApi", "ambulances"],
    queryFn: () => api.get("/ems/ambulances").then((r) => r.data),
  });
  const crew = useQuery({
    queryKey: ["emsApi", "crew"],
    queryFn: () => api.get("/ems/crew").then((r) => r.data),
  });
  const triage = useQuery({
    queryKey: ["emsApi", "triage"],
    enabled: false,
    queryFn: () => api.get("/ems/triage").then((r) => r.data),
  });
  const epcr = useQuery({
    queryKey: ["emsApi", "epcr"],
    queryFn: () => api.get("/ems/epcr").then((r) => r.data),
  });
  const nearby = useQuery({
    queryKey: ["emsApi", "nearby"],
    queryFn: () => api.get("/ems/hospitals/nearby").then((r) => r.data),
  });

  const incidentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const ambulancesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const crewCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const triageCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const epcrCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const nearbyCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    incidents: { columns: incidentsCols, data: asTableData(incidents.data), loading: incidents.isLoading, error: incidents.error, onRetry: () => incidents.refetch() },
    ambulances: { columns: ambulancesCols, data: asTableData(ambulances.data), loading: ambulances.isLoading, error: ambulances.error, onRetry: () => ambulances.refetch() },
    crew: { columns: crewCols, data: asTableData(crew.data), loading: crew.isLoading, error: crew.error, onRetry: () => crew.refetch() },
    triage: { columns: triageCols, data: asTableData(triage.data), loading: triage.isLoading, error: triage.error, onRetry: () => triage.refetch() },
    epcr: { columns: epcrCols, data: asTableData(epcr.data), loading: epcr.isLoading, error: epcr.error, onRetry: () => epcr.refetch() },
    nearby: { columns: nearbyCols, data: asTableData(nearby.data), loading: nearby.isLoading, error: nearby.error, onRetry: () => nearby.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الطوارئ" description="إدارة الطوارئ" />
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
            <DataTable columns={tables[activeTab].columns} data={tables[activeTab].data} loading={tables[activeTab].loading} error={tables[activeTab].error} onRetry={tables[activeTab].onRetry} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
