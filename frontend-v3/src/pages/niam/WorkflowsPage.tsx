import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Dialog } from "@/components/ui/Dialog";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Workflow, PlayCircle, CheckCircle2 } from "lucide-react";

const tabs = [
  { id: "definitions", label: "تعريفات سير العمل", icon: Workflow },
  { id: "instances", label: "الحالات النشطة", icon: PlayCircle },
  { id: "approvals", label: "الموافقات المعلقة", icon: CheckCircle2 },
] as const;
type TabId = (typeof tabs)[number]["id"];

const badgeVariant = (s: string) => {
  const m: Record<string, "success" | "warning" | "destructive" | "default"> = {
    active: "success", completed: "success", pending: "warning",
    cancelled: "destructive", rejected: "destructive",
  };
  return m[s?.toLowerCase()] ?? "default";
};

export default function WorkflowsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("definitions");
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();
  const col = createColumnHelper<Record<string, unknown>>();

  const definitions = useQuery({
    queryKey: ["workflows", "definitions"],
    queryFn: () => api.get("/niam/workflows/definitions").then((r) => r.data),
  });

  const instances = useQuery({
    queryKey: ["workflows", "instances"],
    queryFn: () => api.get("/niam/workflows/instances").then((r) => r.data),
  });

  const createDef = useMutation({
    mutationFn: (data: unknown) => api.post("/niam/workflows/definitions", data).then((r) => r.data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["workflows"] });setDialogOpen(false); },
  });

  const defCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("def_id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("workflow_type", { header: "النوع" }),
    col.accessor("version", { header: "الإصدار" }),
    col.accessor("is_active", { header: "مفعل", cell: ({ getValue }) => getValue() ? "نعم" : "لا" }),
  ];

  const instanceCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("instance_id", { header: "المعرف" }),
    col.accessor("workflow_type", { header: "النوع" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("current_step", { header: "الخطوة الحالية" }),
    col.accessor("started_at", { header: "تاريخ البدء", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables = {
    definitions: { columns: defCols, data: (definitions.data ?? []) as Record<string, unknown>[], loading: definitions.isLoading },
    instances: { columns: instanceCols, data: (instances.data ?? []) as Record<string, unknown>[], loading: instances.isLoading },
    approvals: { columns: instanceCols, data: [], loading: false },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="سير العمل" description="إدارة تعريفات وحالات سير العمل والموافقات"
        actions={<Button onClick={() =>setDialogOpen(true)}>تعريف سير عمل جديد</Button>} />
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
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <div className="space-y-4 p-6">
          <h2 className="text-lg font-semibold">تعريف سير عمل جديد</h2>
          <form onSubmit={(e) => { e.preventDefault(); createDef.mutate(Object.fromEntries(new FormData(e.currentTarget))); }} className="space-y-4">
            <Input name="def_id" placeholder="معرف التعريف" required />
            <Input name="name" placeholder="الاسم" required />
            <Input name="workflow_type" placeholder="نوع سير العمل" required />
            <Button type="submit" loading={createDef.isPending}>حفظ</Button>
          </form>
        </div>
      </Dialog>
    </div>
  );
}
