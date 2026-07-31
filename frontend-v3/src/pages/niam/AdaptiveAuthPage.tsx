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
import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Shield, AlertTriangle, Key, Activity } from "lucide-react";

const tabs = [
  { id: "policies", label: "سياسات المخاطر", icon: Shield },
  { id: "events", label: "أحداث المخاطر", icon: AlertTriangle },
  { id: "sessions", label: "جلسات MFA", icon: Key },
  { id: "travel", label: "السفر المستحيل", icon: Activity },
] as const;
type TabId = (typeof tabs)[number]["id"];

const severityVariant = (s: string) => {
  const m: Record<string, "success" | "warning" | "destructive" | "default"> = {
    low: "default", medium: "warning", high: "destructive", critical: "destructive",
  };
  return m[s?.toLowerCase()] ?? "default";
};

export default function AdaptiveAuthPage() {
  const [activeTab, setActiveTab] = useState<TabId>("policies");
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();
  const col = createColumnHelper<Record<string, unknown>>();

  const riskPolicies = useQuery({
    queryKey: ["adaptive-auth", "policies"],
    queryFn: () => api.get("/niam/adaptive-auth/policies").then((r) => r.data),
  });

  const events = useQuery({
    queryKey: ["adaptive-auth", "events"],
    enabled: false,
    queryFn: () => api.get("/niam/adaptive-auth/risk-history").then((r) => r.data),
  });

  const sessionPolicies = useQuery({
    queryKey: ["adaptive-auth", "session-policies"],
    queryFn: () => api.get("/niam/adaptive-auth/session-policies").then((r) => r.data),
  });

  const createPolicy = useMutation({
    mutationFn: (data: unknown) => api.post("/niam/adaptive-auth/policies", data).then((r) => r.data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["adaptive-auth"] });setDialogOpen(false); },
  });

  const policyCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("policy_id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("risk_threshold_medium", { header: "حد متوسط" }),
    col.accessor("risk_threshold_high", { header: "حد عالي" }),
    col.accessor("enabled", { header: "مفعل", cell: ({ getValue }) => getValue() ? <Badge variant="success">نعم</Badge> : <Badge variant="destructive">لا</Badge> }),
  ];

  const eventCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("event_type", { header: "النوع" }),
    col.accessor("severity", { header: "الخطورة", cell: ({ getValue }) => <Badge variant={severityVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("risk_score", { header: "درجة المخاطرة" }),
    col.accessor("ip_address", { header: "عنوان IP" }),
    col.accessor("timestamp", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleString("ar-IQ") }),
  ];

  const sessionPolicyCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("policy_id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("applies_to", { header: "ينطبق على" }),
    col.accessor("max_sessions", { header: "الحد الأقصى" }),
    col.accessor("session_timeout_minutes", { header: "مهلة الجلسة (د)" }),
    col.accessor("require_mfa", { header: "MFA", cell: ({ getValue }) => getValue() ? <Badge variant="success">مطلوب</Badge> : <Badge variant="default">لا</Badge> }),
  ];

  const tables = {
    policies: { columns: policyCols, data: asTableData(riskPolicies.data), loading: riskPolicies.isLoading },
    events: { columns: eventCols, data: asTableData(events.data), loading: events.isLoading },
    sessions: { columns: sessionPolicyCols, data: asTableData(sessionPolicies.data), loading: sessionPolicies.isLoading },
    travel: { columns: eventCols, data: [] as Record<string, unknown>[], loading: false },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="المصادقة التكيفية" description="إدارة سياسات المخاطر وأحداث الأمن وجلسات MFA"
        actions={<Button onClick={() =>setDialogOpen(true)}>سياسة مخاطر جديدة</Button>} />
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
      <Dialog open={dialogOpen} onClose={() =>setDialogOpen(false)}>
        <div className="space-y-4 p-6">
          <h2 className="text-lg font-semibold">سياسة مخاطر جديدة</h2>
          <form onSubmit={(e) => { e.preventDefault(); createPolicy.mutate(Object.fromEntries(new FormData(e.currentTarget))); }} className="space-y-4">
            <Input name="policy_id" placeholder="معرف السياسة" required />
            <Input name="name" placeholder="الاسم" required />
            <Input name="risk_threshold_low" type="number" placeholder="حد المخاطرة المنخفض" />
            <Input name="risk_threshold_medium" type="number" placeholder="حد المخاطرة المتوسط" />
            <Input name="risk_threshold_high" type="number" placeholder="حد المخاطرة العالي" />
            <Input name="risk_threshold_critical" type="number" placeholder="حد المخاطرة الخطير" />
            <Button type="submit" loading={createPolicy.isPending}>حفظ</Button>
          </form>
        </div>
      </Dialog>
    </div>
  );
}
