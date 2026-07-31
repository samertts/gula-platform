import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Dialog } from "@/components/ui/Dialog";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Globe, Link, Handshake, FileText } from "lucide-react";

const tabs = [
  { id: "providers", label: "مزودو الخدمة", icon: Globe },
  { id: "identities", label: "الهويات المرتبطة", icon: Link },
  { id: "trust", label: "الثقة المتبادلة", icon: Handshake },
  { id: "agreements", label: "الاتفاقيات", icon: FileText },
] as const;
type TabId = (typeof tabs)[number]["id"];

export default function FederationPage() {
  const [activeTab, setActiveTab] = useState<TabId>("providers");
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const col = createColumnHelper<Record<string, unknown>>();

  const providers = useQuery({
    queryKey: ["federation", "providers"],
    queryFn: () => api.get("/niam/federation/providers").then((r) => r.data),
  });

  const identities = useQuery({
    queryKey: ["federation", "identities"],
    enabled: false,
    queryFn: () => api.get("/niam/federation/identities").then((r) => r.data),
  });

  const trustList = useQuery({
    queryKey: ["federation", "trust"],
    queryFn: () => api.get("/niam/trust/federation").then((r) => r.data),
  });

  const agreements = useQuery({
    queryKey: ["federation", "agreements"],
    queryFn: () => api.get("/niam/federation/agreements").then((r) => r.data),
  });

  const createProvider = useMutation({
    mutationFn: (data: unknown) => api.post("/niam/federation/providers", data).then((r) => r.data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["federation"] });setDialogOpen(false); },
  });

  const providerCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("provider_id", { header: "المعرف" }),
    col.accessor("name_en", { header: "الاسم" }),
    col.accessor("provider_type", { header: "النوع" }),
    col.accessor("issuer_url", { header: "رابط الإصدار" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={(getValue() as string) === "active" ? "success" : "default"}>{getValue() as string}</Badge> }),
  ];

  const identityCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("fed_id", { header: "المعرف الموحد" }),
    col.accessor("provider_id", { header: "المزود" }),
    col.accessor("external_subject_id", { header: "المعرف الخارجي" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant="success">{getValue() as string}</Badge> }),
    col.accessor("linked_at", { header: "تاريخ الربط", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const trustCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("trust_id", { header: "رقم الثقة" }),
    col.accessor("source_org_id", { header: "الجهة المصدرة" }),
    col.accessor("target_org_id", { header: "الجهة المستهدفة" }),
    col.accessor("trust_level", { header: "مستوى الثقة" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={(getValue() as string) === "active" ? "success" : "warning"}>{getValue() as string}</Badge> }),
  ];

  const agreementCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("agreement_id", { header: "رقم الاتفاقية" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("agreement_type", { header: "النوع" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={(getValue() as string) === "active" ? "success" : "default"}>{getValue() as string}</Badge> }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    providers: { columns: providerCols, data: asTableData(providers.data), loading: providers.isLoading },
    identities: { columns: identityCols, data: asTableData(identities.data), loading: identities.isLoading },
    trust: { columns: trustCols, data: asTableData(trustList.data), loading: trustList.isLoading },
    agreements: { columns: agreementCols, data: asTableData(agreements.data), loading: agreements.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الاتحاد (Federation)" description="إدارة مزودي الخدمة والهويات الموحدة واتفاقيات الثقة"
        actions={<Button onClick={() =>setDialogOpen(true)}>إضافة مزود</Button>} />
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
          <h2 className="text-lg font-semibold">إضافة مزود خدمة</h2>
          <form onSubmit={(e) => { e.preventDefault(); createProvider.mutate(Object.fromEntries(new FormData(e.currentTarget))); }} className="space-y-4">
            <Input name="provider_id" placeholder="معرف المزود" required />
            <Input name="name_en" placeholder="الاسم (إنجليزي)" required />
            <Input name="issuer_url" placeholder="رابط الإصدار" required />
            <Select name="provider_type" options={[{ label: "OAuth2", value: "oauth2" }, { label: "OIDC", value: "oidc" }, { label: "SAML", value: "saml" }]} placeholder="النوع" />
            <Button type="submit" loading={createProvider.isPending}>حفظ</Button>
          </form>
        </div>
      </Dialog>
    </div>
  );
}
