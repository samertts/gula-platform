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
  { id: "definitions", label: "التعريفات", icon: FileText },
  { id: "executions", label: "executions", icon: Activity },
  { id: "steps", label: "steps", icon: List },
  { id: "approvals", label: "الموافقات", icon: ClipboardList },
  { id: "pending", label: "pending", icon: BookOpen },
  { id: "templates", label: "القوالب", icon:  FolderOpen },
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

export default function NationalWorkflowRuntimeApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("definitions");
  const col = createColumnHelper<Record<string, unknown>>();

  const definitions = useQuery({
    queryKey: ["nationalWorkflowRuntimeApi", "definitions"],
    queryFn: () => api.get("/national/workflows/definitions").then((r) => r.data),
  });
  const executions = useQuery({
    queryKey: ["nationalWorkflowRuntimeApi", "executions"],
    queryFn: () => api.get("/national/workflows/executions").then((r) => r.data),
  });
  const steps = useQuery({
    queryKey: ["nationalWorkflowRuntimeApi", "steps"],
    queryFn: () => api.get("/national/workflows/executions//steps").then((r) => r.data),
  });
  const approvals = useQuery({
    queryKey: ["nationalWorkflowRuntimeApi", "approvals"],
    queryFn: () => api.get("/national/workflows/executions//approvals").then((r) => r.data),
  });
  const pending = useQuery({
    queryKey: ["nationalWorkflowRuntimeApi", "pending"],
    queryFn: () => api.get("/national/workflows/approvals/pending").then((r) => r.data),
  });
  const templates = useQuery({
    queryKey: ["nationalWorkflowRuntimeApi", "templates"],
    queryFn: () => api.get("/national/workflows/templates").then((r) => r.data),
  });

  const definitionsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const executionsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const stepsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const approvalsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const pendingCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const templatesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    definitions: { columns: definitionsCols, data: (definitions.data ?? []) as Record<string, unknown>[], loading: definitions.isLoading },
    executions: { columns: executionsCols, data: (executions.data ?? []) as Record<string, unknown>[], loading: executions.isLoading },
    steps: { columns: stepsCols, data: (steps.data ?? []) as Record<string, unknown>[], loading: steps.isLoading },
    approvals: { columns: approvalsCols, data: (approvals.data ?? []) as Record<string, unknown>[], loading: approvals.isLoading },
    pending: { columns: pendingCols, data: (pending.data ?? []) as Record<string, unknown>[], loading: pending.isLoading },
    templates: { columns: templatesCols, data: (templates.data ?? []) as Record<string, unknown>[], loading: templates.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="تشغيل سير العمل" description="إدارة تشغيل سير العمل" />
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
