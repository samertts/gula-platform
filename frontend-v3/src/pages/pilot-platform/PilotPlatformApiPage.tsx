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
  { id: "pilots", label: "pilots", icon: FileText },
  { id: "facilities", label: "facilities", icon: Activity },
  { id: "readiness", label: "readiness", icon: List },
  { id: "gates", label: "gates", icon: ClipboardList },
  { id: "deployments", label: "deployments", icon: BookOpen },
  { id: "certify", label: "certify", icon:  FolderOpen },
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

export default function PilotPlatformApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("pilots");
  const col = createColumnHelper<Record<string, unknown>>();

  const pilots = useQuery({
    queryKey: ["pilotPlatformApi", "pilots"],
    queryFn: () => api.get("/pilot-platform/pilots").then((r) => r.data),
  });
  const facilities = useQuery({
    queryKey: ["pilotPlatformApi", "facilities"],
    queryFn: () => api.get("/pilot-platform/pilots//facilities").then((r) => r.data),
  });
  const readiness = useQuery({
    queryKey: ["pilotPlatformApi", "readiness"],
    queryFn: () => api.get("/pilot-platform/facilities//readiness").then((r) => r.data),
  });
  const gates = useQuery({
    queryKey: ["pilotPlatformApi", "gates"],
    queryFn: () => api.get("/pilot-platform/pilots//gates").then((r) => r.data),
  });
  const deployments = useQuery({
    queryKey: ["pilotPlatformApi", "deployments"],
    queryFn: () => api.get("/pilot-platform/deployments").then((r) => r.data),
  });
  const certify = useQuery({
    queryKey: ["pilotPlatformApi", "certify"],
    queryFn: () => api.get("/pilot-platform/certify").then((r) => r.data),
  });

  const pilotsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const facilitiesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const readinessCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const gatesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const deploymentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const certifyCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    pilots: { columns: pilotsCols, data: (pilots.data ?? []) as Record<string, unknown>[], loading: pilots.isLoading },
    facilities: { columns: facilitiesCols, data: (facilities.data ?? []) as Record<string, unknown>[], loading: facilities.isLoading },
    readiness: { columns: readinessCols, data: (readiness.data ?? []) as Record<string, unknown>[], loading: readiness.isLoading },
    gates: { columns: gatesCols, data: (gates.data ?? []) as Record<string, unknown>[], loading: gates.isLoading },
    deployments: { columns: deploymentsCols, data: (deployments.data ?? []) as Record<string, unknown>[], loading: deployments.isLoading },
    certify: { columns: certifyCols, data: (certify.data ?? []) as Record<string, unknown>[], loading: certify.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="المنصة التجريبية" description="إدارة المنصة التجريبية" />
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
