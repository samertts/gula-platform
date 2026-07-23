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
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { ScrollText, Key, Shield, ShieldCheck } from "lucide-react";

const tabs = [
  { id: "certificates", label: "الشهادات الرقمية", icon: ScrollText },
  { id: "authorities", label: "سلطات التصديق", icon: Shield },
  { id: "apikeys", label: "مفاتيح API", icon: Key },
  { id: "expiring", label: "شبه منتهية", icon: ShieldCheck },
] as const;
type TabId = (typeof tabs)[number]["id"];

const badgeVariant = (s: string) => {
  const m: Record<string, "success" | "warning" | "destructive" | "default"> = { active: "success", expired: "warning", revoked: "destructive" };
  return m[s?.toLowerCase()] ?? "default";
};

export default function CertificatesPage() {
  const [activeTab, setActiveTab] = useState<TabId>("certificates");
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();
  const col = createColumnHelper<Record<string, unknown>>();

  const certificates = useQuery({
    queryKey: ["certificates", "list"],
    queryFn: () => api.get("/niam/certificates").then((r) => r.data),
  });

  const authorities = useQuery({
    queryKey: ["certificates", "authorities"],
    queryFn: () => api.get("/niam/certificates/authorities").then((r) => r.data),
  });

  const apiKeys = useQuery({
    queryKey: ["certificates", "apikeys"],
    queryFn: () => api.get("/niam/certificates/api-keys").then((r) => r.data),
  });

  const expiring = useQuery({
    queryKey: ["certificates", "expiring"],
    queryFn: () => api.get("/niam/certificates/expiring", { params: { days: 30 } }).then((r) => r.data),
  });

  const issueCert = useMutation({
    mutationFn: (data: unknown) => api.post("/niam/certificates/issue", data).then((r) => r.data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["certificates"] });setDialogOpen(false); },
  });

  const certCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("certificate_id", { header: "رقم الشهادة" }),
    col.accessor("subject", { header: "الموضوع" }),
    col.accessor("certificate_type", { header: "النوع" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("issued_at", { header: "تاريخ الإصدار", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
    col.accessor("expires_at", { header: "تاريخ الانتهاء", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const caCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("ca_id", { header: "رقم CA" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("ca_type", { header: "النوع" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant="success">{getValue() as string}</Badge> }),
  ];

  const keyCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("api_key_id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("key_prefix", { header: "البداية" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "تاريخ الإنشاء", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    certificates: { columns: certCols, data: (certificates.data ?? []) as Record<string, unknown>[], loading: certificates.isLoading },
    authorities: { columns: caCols, data: (authorities.data ?? []) as Record<string, unknown>[], loading: authorities.isLoading },
    apikeys: { columns: keyCols, data: (apiKeys.data ?? []) as Record<string, unknown>[], loading: apiKeys.isLoading },
    expiring: { columns: certCols, data: (expiring.data ?? []) as Record<string, unknown>[], loading: expiring.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="إدارة الشهادات الرقمية" description="الشهادات الرقمية وسلطات التصديق ومفاتيح API"
        actions={<Button onClick={() =>setDialogOpen(true)}>إصدار شهادة</Button>} />
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
          <h2 className="text-lg font-semibold">إصدار شهادة رقمية</h2>
          <form onSubmit={(e) => { e.preventDefault(); issueCert.mutate(Object.fromEntries(new FormData(e.currentTarget))); }} className="space-y-4">
            <Input name="subject" placeholder="الموضوع" required />
            <Select name="cert_type" options={[{ label: "TLS", value: "tls" }, { label: "توقيع", value: "signing" }, { label: "تشفير", value: "encryption" }, { label: "مصادقة", value: "authentication" }]} placeholder="النوع" />
            <Input name="validity_days" type="number" placeholder="مدة الصلاحية (أيام)" />
            <Button type="submit" loading={issueCert.isPending}>إصدار</Button>
          </form>
        </div>
      </Dialog>
    </div>
  );
}
