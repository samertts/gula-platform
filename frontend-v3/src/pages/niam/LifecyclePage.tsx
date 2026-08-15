import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, apiClient, type AccountRequestStatus, type AccountRequestSummary } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {
  Building2,
  CheckCircle2,
  Clock3,
  Eye,
  Shield,
  UserCircle,
  Users,
  XCircle,
} from "lucide-react";

const tabs = [
  { id: "enterprise", label: "المؤسسات", icon: Building2 },
  { id: "workforce", label: "القوى العاملة", icon: Users },
  { id: "government", label: "التوظيف الحكومي", icon: Building2 },
  { id: "citizen", label: "المواطنون", icon: UserCircle },
  { id: "guardian", label: "الأوصياء", icon: Shield },
  { id: "account_requests", label: "طلبات الحسابات", icon: CheckCircle2 },
] as const;

type TabId = (typeof tabs)[number]["id"];
type LegacyRow = Record<string, unknown>;
type AccountRequestAction = "review" | "approve" | "reject" | "expire";

const badgeVariant = (s: string) => {
  const m: Record<string, "success" | "warning" | "destructive" | "default"> = {
    active: "success",
    approved: "success",
    activated: "success",
    verified: "success",
    pending: "warning",
    pending_review: "warning",
    pending_verification: "warning",
    pending_approval: "warning",
    under_review: "warning",
    draft: "default",
    rejected: "destructive",
    expired: "destructive",
    terminated: "destructive",
    deactivated: "destructive",
  };
  return m[s?.toLowerCase()] ?? "default";
};

const accountRequestStatusLabel: Record<AccountRequestStatus, string> = {
  pending_review: "بانتظار المراجعة",
  under_review: "قيد المراجعة",
  pending_verification: "بانتظار التحقق",
  verified: "تم التحقق",
  pending_approval: "بانتظار الاعتماد",
  approved: "معتمد",
  rejected: "مرفوض",
  expired: "منتهي",
  cancelled: "ملغى",
};

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleDateString("ar-IQ") : "—";
}

export default function LifecyclePage() {
  const [activeTab, setActiveTab] = useState<TabId>("enterprise");
  const [mutationError, setMutationError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const col = createColumnHelper<LegacyRow>();

  const enterprise = useQuery({
    queryKey: ["lifecycle", "enterprise"],
    queryFn: () => api.get("/niam/lifecycle/enterprise").then((r) => r.data),
  });

  const workforce = useQuery({
    queryKey: ["lifecycle", "workforce"],
    queryFn: () => api.get("/niam/lifecycle/workforce").then((r) => r.data),
  });

  const appointments = useQuery({
    queryKey: ["lifecycle", "government"],
    queryFn: () => api.get("/niam/lifecycle/government/appointments").then((r) => r.data),
  });

  const citizens = useQuery({
    queryKey: ["lifecycle", "citizen"],
    queryFn: () => api.get("/niam/lifecycle/citizen").then((r) => r.data),
  });

  const guardians = useQuery({
    queryKey: ["lifecycle", "guardian"],
    queryFn: () => api.get("/niam/lifecycle/guardians").then((r) => r.data),
  });

  const accountRequests = useQuery({
    queryKey: ["niam", "account-requests"],
    queryFn: () => apiClient.listAccountRequests(),
    enabled: activeTab === "account_requests",
  });

  const accountRequestMutation = useMutation({
    mutationFn: async ({ requestId, action }: { requestId: string; action: AccountRequestAction }) => {
      if (action === "review") return apiClient.reviewAccountRequest(requestId);
      if (action === "approve") return apiClient.approveAccountRequest(requestId);
      if (action === "reject") return apiClient.rejectAccountRequest(requestId, "manual_governance_rejection");
      return apiClient.expireAccountRequest(requestId);
    },
    onSuccess: () => {
      setMutationError(null);
      void queryClient.invalidateQueries({ queryKey: ["niam", "account-requests"] });
    },
    onError: (error) => {
      setMutationError(error instanceof Error ? error.message : "تعذر تنفيذ العملية المحمية");
    },
  });

  const enterpriseCols: ColumnDef<LegacyRow, unknown>[] = [
    col.accessor("reg_id", { header: "رقم التسجيل" }),
    col.accessor("organization_id", { header: "المؤسسة" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("current_step", { header: "الخطوة الحالية" }),
    col.accessor("submitted_at", { header: "تاريخ التقديم", cell: ({ getValue }) => formatDate(getValue() as string) }),
  ];

  const workforceCols: ColumnDef<LegacyRow, unknown>[] = [
    col.accessor("request_id", { header: "رقم الطلب" }),
    col.accessor("request_type", { header: "النوع" }),
    col.accessor("requesting_org_id", { header: "الجهة" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
  ];

  const govCols: ColumnDef<LegacyRow, unknown>[] = [
    col.accessor("appointment_id", { header: "رقم التعيين" }),
    col.accessor("person_id", { header: "الشخص" }),
    col.accessor("position", { header: "المنصب" }),
    col.accessor("grade", { header: "الدرجة" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
  ];

  const citizenCols: ColumnDef<LegacyRow, unknown>[] = [
    col.accessor("citizen_id", { header: "رقم المواطن" }),
    col.accessor("person_id", { header: "الشخص" }),
    col.accessor("health_id", { header: "الرقم الصحي" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("registration_date", { header: "تاريخ التسجيل", cell: ({ getValue }) => formatDate(getValue() as string) }),
  ];

  const guardianCols: ColumnDef<LegacyRow, unknown>[] = [
    col.accessor("guardian_id", { header: "رقم الوصي" }),
    col.accessor("guardian_person_id", { header: "الوصي" }),
    col.accessor("dependent_person_id", { header: "المكفول" }),
    col.accessor("relationship", { header: "العلاقة" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
  ];

  const accountRequestCols = useMemo<ColumnDef<AccountRequestSummary, unknown>[]>(
    () => [
      {
        accessorKey: "request_id",
        header: "رقم الطلب",
        cell: ({ getValue }) => <span className="font-mono text-xs">{getValue() as string}</span>,
      },
      {
        accessorKey: "status",
        header: "الحالة",
        cell: ({ getValue }) => {
          const value = getValue() as AccountRequestStatus;
          return <Badge variant={badgeVariant(value)}>{accountRequestStatusLabel[value] ?? value}</Badge>;
        },
      },
      { accessorKey: "requested_account_type", header: "نوع الحساب" },
      { accessorKey: "account_id", header: "الحساب المنشأ", cell: ({ getValue }) => <span className="font-mono text-xs">{(getValue() as string | null) ?? "—"}</span> },
      { accessorKey: "reviewed_at", header: "آخر مراجعة", cell: ({ getValue }) => formatDate(getValue() as string | null) },
      { accessorKey: "verified_at", header: "التحقق", cell: ({ getValue }) => formatDate(getValue() as string | null) },
      {
        id: "actions",
        header: "الإجراءات المحمية",
        cell: ({ row }) => {
          const item = row.original;
          const busy = accountRequestMutation.isPending && accountRequestMutation.variables?.requestId === item.request_id;
          const canReview = item.status === "pending_review";
          const canApprove = item.status === "verified" || item.status === "pending_approval";
          const canReject = ["pending_review", "under_review", "pending_verification", "verified", "pending_approval"].includes(item.status);
          return (
            <div className="flex flex-wrap gap-2" onClick={(event) => event.stopPropagation()}>
              {canReview && (
                <Button
                  size="sm"
                  variant="outline"
                  loading={busy}
                  aria-label={`بدء مراجعة الطلب ${item.request_id}`}
                  onClick={() => accountRequestMutation.mutate({ requestId: item.request_id, action: "review" })}
                >
                  <Eye aria-hidden="true" /> مراجعة
                </Button>
              )}
              {canApprove && (
                <Button
                  size="sm"
                  loading={busy}
                  aria-label={`اعتماد الطلب ${item.request_id}`}
                  onClick={() => accountRequestMutation.mutate({ requestId: item.request_id, action: "approve" })}
                >
                  <CheckCircle2 aria-hidden="true" /> اعتماد
                </Button>
              )}
              {canReject && (
                <Button
                  size="sm"
                  variant="destructive"
                  loading={busy}
                  aria-label={`رفض الطلب ${item.request_id}`}
                  onClick={() => accountRequestMutation.mutate({ requestId: item.request_id, action: "reject" })}
                >
                  <XCircle aria-hidden="true" /> رفض
                </Button>
              )}
              {!canReview && !canApprove && !canReject && item.status === "pending_verification" && (
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground" role="status">
                  <Clock3 aria-hidden="true" /> بانتظار مزود التحقق
                </span>
              )}
            </div>
          );
        },
      },
    ],
    [accountRequestMutation],
  );

  const legacyTables: Record<TabId & Exclude<TabId, "account_requests">, { columns: ColumnDef<LegacyRow, unknown>[]; data: LegacyRow[]; loading: boolean }> = {
    enterprise: { columns: enterpriseCols, data: (enterprise.data ?? []) as LegacyRow[], loading: enterprise.isLoading },
    workforce: { columns: workforceCols, data: (workforce.data ?? []) as LegacyRow[], loading: workforce.isLoading },
    government: { columns: govCols, data: (appointments.data ?? []) as LegacyRow[], loading: appointments.isLoading },
    citizen: { columns: citizenCols, data: (citizens.data ?? []) as LegacyRow[], loading: citizens.isLoading },
    guardian: { columns: guardianCols, data: (guardians.data ?? []) as LegacyRow[], loading: guardians.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="دورة حياة الهوية" description="إدارة دورة حياة المؤسسات والقوى العاملة والمواطنين والأوصياء وطلبات الحسابات" />

      <Card>
        <CardContent className="p-0">
          <div className="flex flex-wrap border-b" role="tablist" aria-label="مساحات دورة حياة الهوية">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const selected = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  aria-controls={`lifecycle-panel-${tab.id}`}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors gula-focus-ring ${selected ? "border-b-2 border-indigo-600 text-indigo-600" : "text-gray-500 hover:text-gray-700"}`}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {tab.label}
                </button>
              );
            })}
          </div>
          <div id={`lifecycle-panel-${activeTab}`} role="tabpanel" className="p-4">
            {mutationError && activeTab === "account_requests" && (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">
                {mutationError}
              </div>
            )}
            {activeTab === "account_requests" ? (
              <DataTable<AccountRequestSummary>
                columns={accountRequestCols}
                data={accountRequests.data?.requests ?? []}
                loading={accountRequests.isLoading}
              />
            ) : (
              <DataTable<LegacyRow>
                columns={legacyTables[activeTab].columns}
                data={legacyTables[activeTab].data}
                loading={legacyTables[activeTab].loading}
              />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
