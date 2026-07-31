import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Button, Card, CardContent, Dialog, Input, Select, Badge } from "@/components/ui";







import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Shield, Fingerprint, Anchor, Scale } from "lucide-react";

const tabs = [
  { id: "frameworks", label: "أطر الثقة", icon: Shield },
  { id: "profiles", label: "مستويات الضمان", icon: Fingerprint },
  { id: "anchors", label: "مراسي الثقة", icon: Anchor },
  { id: "evaluate", label: "تقييم الثقة", icon: Scale },
] as const;

type TabId = (typeof tabs)[number]["id"];

export default function TrustPage() {
  const [activeTab, setActiveTab] = useState<TabId>("frameworks");
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const frameworks = useQuery({
    queryKey: ["trust", "frameworks"],
    queryFn: () => api.get("/niam/trust/frameworks").then((r) => r.data),
  });

  const profiles = useQuery({
    queryKey: ["trust", "profiles"],
    queryFn: () => api.get("/niam/trust/assurance-profiles").then((r) => r.data),
  });

  const anchors = useQuery({
    queryKey: ["trust", "anchors"],
    queryFn: () => api.get("/niam/trust/anchors").then((r) => r.data),
  });

  const createFramework = useMutation({
    mutationFn: (data: unknown) =>
      api.post("/niam/trust/frameworks", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trust"] });
     setDialogOpen(false);
    },
  });

  const col = createColumnHelper<Record<string, unknown>>();

  const frameworkColumns: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("name", { header: "الاسم" }),
    col.accessor("framework_type", { header: "النوع" }),
    col.accessor("version", { header: "الإصدار" }),
    col.accessor("status", {
      header: "الحالة",
      cell: ({ getValue }) => (
        <Badge variant={(getValue() as string) === "active" ? "success" : "default"}>
          {getValue() as string}
        </Badge>
      ),
    }),
  ];

  const profileColumns: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("profile_type", { header: "النوع" }),
    col.accessor("ial_level", { header: "IAL" }),
    col.accessor("aal_level", { header: "AAL" }),
    col.accessor("fal_level", { header: "FAL" }),
    col.accessor("status", {
      header: "الحالة",
      cell: ({ getValue }) => <Badge variant="success">{getValue() as string}</Badge>,
    }),
  ];

  const anchorColumns: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("name", { header: "الاسم" }),
    col.accessor("anchor_type", { header: "النوع" }),
    col.accessor("status", {
      header: "الحالة",
      cell: ({ getValue }) => <Badge variant="success">{getValue() as string}</Badge>,
    }),
    col.accessor("registered_at", {
      header: "تاريخ التسجيل",
      cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ"),
    }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry?: () => void }> = {
    frameworks: { columns: frameworkColumns, data: asTableData(frameworks.data), loading: frameworks.isLoading, error: frameworks.error, onRetry: () => frameworks.refetch() },
    profiles: { columns: profileColumns, data: asTableData(profiles.data), loading: profiles.isLoading, error: profiles.error, onRetry: () => profiles.refetch() },
    anchors: { columns: anchorColumns, data: asTableData(anchors.data), loading: anchors.isLoading, error: anchors.error, onRetry: () => anchors.refetch() },
    evaluate: { columns: frameworkColumns, data: [], loading: false, error: null, onRetry: undefined },
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="إطار الثقة الوطني"
        description="إدارة أطر الثقة ومستويات الضمان ومراسي الثقة"
        actions={
          <Button onClick={() =>setDialogOpen(true)}>إضافة إطار ثقة</Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          <div className="flex border-b">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? "border-b-2 border-indigo-600 text-indigo-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
          <div className="p-4">
            <DataTable
              columns={tables[activeTab].columns}
              data={tables[activeTab].data}
              loading={tables[activeTab].loading} error={tables[activeTab].error} onRetry={tables[activeTab].onRetry}
            />
          </div>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <div className="space-y-4 p-6">
          <h2 className="text-lg font-semibold">إضافة إطار ثقة</h2>
          <form onSubmit={(e) => {
            e.preventDefault();
            const fd = new FormData(e.currentTarget);
            createFramework.mutate(Object.fromEntries(fd));
          }} className="space-y-4">
            <Input name="name" placeholder="الاسم" required />
            <Select
              name="framework_type"
              options={[
                { label: "NIST 800-63", value: "nist_800_63" },
                { label: "eIDAS", value: "eidas" },
                { label: "مخصص", value: "custom" },
              ]}
              placeholder="نوع الإطار"
            />
            <Input name="version" placeholder="الإصدار" />
            <Button type="submit" loading={createFramework.isPending}>حفظ</Button>
          </form>
        </div>
      </Dialog>
    </div>
  );
}
