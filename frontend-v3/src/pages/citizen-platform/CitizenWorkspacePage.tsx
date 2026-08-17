import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {
  Activity,
  BellRing,
  CalendarClock,
  CheckCircle2,
  FileText,
  FlaskConical,
  Pill,
  ShieldCheck,
  UsersRound,
} from "lucide-react";

type TabId =
  | "dashboard"
  | "profile"
  | "health-summary"
  | "appointments"
  | "medications"
  | "medication-dispenses"
  | "lab-results"
  | "family"
  | "notifications";

type RecordRow = Record<string, unknown>;
type ListResponse = { total?: number; [key: string]: unknown };
type DashboardSummary = {
  appointments?: { upcoming?: number };
  medications?: { active?: number };
  laboratory?: { recent_results?: number };
  radiology?: { recent_studies?: number };
  family?: { members?: number };
  notifications?: { unread?: number };
  certificates?: { active?: number };
};

type QueryState<T> = {
  data?: T;
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
};

const tabs: Array<{ id: TabId; label: string; icon: typeof Activity }> = [
  { id: "dashboard", label: "نظرة عامة", icon: FileText },
  { id: "profile", label: "ملفي الصحي", icon: Activity },
  { id: "health-summary", label: "ملخصي الصحي", icon: ShieldCheck },
  { id: "appointments", label: "مواعيدي", icon: CalendarClock },
  { id: "medications", label: "أدويتي", icon: Pill },
  { id: "medication-dispenses", label: "العلاجات المصروفة", icon: Pill },
  { id: "lab-results", label: "نتائج المختبر", icon: FlaskConical },
  { id: "family", label: "أسرتي", icon: UsersRound },
  { id: "notifications", label: "تنبيهاتي", icon: BellRing },
];

const badgeVariant = (value: unknown) => {
  const status = String(value ?? "").toLowerCase();
  const variants: Record<string, "success" | "warning" | "destructive" | "default"> = {
    active: "success",
    completed: "success",
    approved: "success",
    pending: "warning",
    draft: "default",
    rejected: "destructive",
    inactive: "default",
    expired: "warning",
    revoked: "destructive",
  };
  return variants[status] ?? "default";
};

const displayDate = (value: unknown) => {
  if (!value) return "—";
  const date = new Date(String(value));
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString("ar-IQ");
};

function QueryStateMessage({ query }: { query: QueryState<unknown> }) {
  if (query.isLoading) {
    return <div className="rounded-lg border border-dashed p-6 text-center text-sm text-slate-500">جارٍ تحميل بياناتك بشكل آمن…</div>;
  }
  if (query.isError) {
    return <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700">تعذر تحميل هذه البيانات. حاول مرة أخرى لاحقاً.</div>;
  }
  return null;
}

function MetricCard({ label, value, description, icon: Icon }: { label: string; value: number; description: string; icon: typeof Activity }) {
  return (
    <Card className="border-slate-200 shadow-sm">
      <CardContent className="flex items-start justify-between gap-3 p-4">
        <div>
          <p className="text-sm text-slate-500">{label}</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
          <p className="mt-1 text-xs text-slate-500">{description}</p>
        </div>
        <div className="rounded-xl bg-indigo-50 p-3 text-indigo-700"><Icon className="h-5 w-5" /></div>
      </CardContent>
    </Card>
  );
}

export default function CitizenPlatformPage() {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const columnHelper = createColumnHelper<RecordRow>();

  const dashboard = useQuery<DashboardSummary>({
    queryKey: ["citizenPlatform", "dashboard"],
    queryFn: () => api.get("/citizen-platform/me/dashboard").then((response) => response.data),
  });
  const profile = useQuery<RecordRow | RecordRow[]>({
    queryKey: ["citizenPlatform", "profile"],
    queryFn: () => api.get("/citizen-platform/me/profile").then((response) => response.data),
  });
  const healthSummary = useQuery<ListResponse>({
    queryKey: ["citizenPlatform", "health-summary"],
    queryFn: () => api.get("/citizen-platform/me/health-summary").then((response) => response.data),
  });
  const appointments = useQuery<ListResponse>({
    queryKey: ["citizenPlatform", "appointments"],
    queryFn: () => api.get("/citizen-platform/me/appointments").then((response) => response.data),
  });
  const medications = useQuery<ListResponse>({
    queryKey: ["citizenPlatform", "medications"],
    queryFn: () => api.get("/citizen-platform/me/medications").then((response) => response.data),
  });
  const labResults = useQuery<ListResponse>({
    queryKey: ["citizenPlatform", "lab-results"],
    queryFn: () => api.get("/citizen-platform/me/lab-results").then((response) => response.data),
  });
  const medicationDispenses = useQuery<{ dispenses?: RecordRow[]; total?: number }>({
    queryKey: ["citizenPlatform", "medication-dispenses"],
    queryFn: () => api.get("/citizen-platform/me/medication-dispenses").then((response) => response.data),
  });
  const family = useQuery<{ members?: RecordRow[]; total?: number }>({
    queryKey: ["citizenPlatform", "family"],
    queryFn: () => api.get("/citizen-platform/me/family").then((response) => response.data),
  });
  const notifications = useQuery<{ notifications?: RecordRow[]; total?: number }>({
    queryKey: ["citizenPlatform", "notifications"],
    queryFn: () => api.get("/citizen-platform/me/notifications").then((response) => response.data),
  });

  const columns: ColumnDef<RecordRow, unknown>[] = [
    columnHelper.accessor("id", { header: "المعرف" }),
    columnHelper.accessor("name", { header: "الاسم" }),
    columnHelper.accessor("status", {
      header: "الحالة",
      cell: ({ getValue }) => <Badge variant={badgeVariant(getValue())}>{String(getValue() ?? "غير محدد")}</Badge>,
    }),
    columnHelper.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => displayDate(getValue()) }),
  ];
  const medicationDispenseColumns: ColumnDef<RecordRow, unknown>[] = [
    columnHelper.accessor("medication_name_ar", { header: "العلاج", cell: ({ row }) => String(row.original.medication_name_ar || row.original.medication_name || "—") }),
    columnHelper.accessor("quantity", { header: "الكمية" }),
    columnHelper.accessor("quantity_unit", { header: "الوحدة" }),
    columnHelper.accessor("lot_number", { header: "الدفعة" }),
    columnHelper.accessor("expiry_date", { header: "الصلاحية", cell: ({ getValue }) => displayDate(getValue()) }),
    columnHelper.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue())}>{String(getValue() ?? "غير محدد")}</Badge> }),
    columnHelper.accessor("dispensed_at", { header: "تاريخ الصرف", cell: ({ getValue }) => displayDate(getValue()) }),
  ];
  const familyColumns: ColumnDef<RecordRow, unknown>[] = [
    columnHelper.accessor("full_name", { header: "الاسم" }),
    columnHelper.accessor("relationship", { header: "صلة القرابة" }),
    columnHelper.accessor("status", { header: "حالة الصلاحية", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue())}>{String(getValue() ?? "مرتبط")}</Badge> }),
  ];
  const notificationColumns: ColumnDef<RecordRow, unknown>[] = [
    columnHelper.accessor("title_ar", { header: "التنبيه", cell: ({ row }) => String(row.original.title_ar || row.original.title || "تنبيه") }),
    columnHelper.accessor("message_ar", { header: "التفاصيل", cell: ({ row }) => String(row.original.message_ar || row.original.message || "—") }),
    columnHelper.accessor("is_read", { header: "الحالة", cell: ({ getValue }) => <Badge variant={getValue() ? "default" : "warning"}>{getValue() ? "مقروء" : "جديد"}</Badge> }),
    columnHelper.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => displayDate(getValue()) }),
  ];

  const tableConfig: Record<TabId, { query: QueryState<unknown>; rows: RecordRow[]; columns: ColumnDef<RecordRow, unknown>[]; empty: string }> = {
    dashboard: { query: dashboard, rows: [], columns, empty: "ستظهر ملخصاتك هنا." },
    profile: { query: profile, rows: Array.isArray(profile.data) ? profile.data : profile.data ? [profile.data] : [], columns, empty: "لا توجد معلومات ملف متاحة." },
    "health-summary": { query: healthSummary, rows: [], columns, empty: "لا يوجد ملخص صحي مسجل حالياً." },
    appointments: { query: appointments, rows: Array.isArray(appointments.data) ? appointments.data : [], columns, empty: "لا توجد مواعيد قادمة." },
    medications: { query: medications, rows: Array.isArray(medications.data) ? medications.data : [], columns, empty: "لا توجد أدوية فعالة مسجلة." },
    "medication-dispenses": { query: medicationDispenses, rows: medicationDispenses.data?.dispenses ?? [], columns: medicationDispenseColumns, empty: "لا توجد عمليات صرف مسجلة." },
    "lab-results": { query: labResults, rows: Array.isArray(labResults.data) ? labResults.data : [], columns, empty: "لا توجد نتائج مختبر متاحة." },
    family: { query: family, rows: family.data?.members ?? [], columns: familyColumns, empty: "لا توجد علاقات أسرية مفعلة." },
    notifications: { query: notifications, rows: notifications.data?.notifications ?? [], columns: notificationColumns, empty: "لا توجد تنبيهات جديدة." },
  };

  const dashboardData = dashboard.data ?? {};
  const current = tableConfig[activeTab];

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="مساحتي الصحية" description="ملخص آمن ومفهوم لخدماتك الصحية وخدمات أسرتك المرتبطة بحساب GULA" />

      {activeTab === "dashboard" ? (
        <>
          <Card className="border-indigo-100 bg-gradient-to-l from-indigo-50 to-white shadow-sm">
            <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-medium text-indigo-700">صحتك أقرب إليك</p>
                <h2 className="mt-1 text-xl font-bold text-slate-900">تابع موعدك ودواءك ونتيجتك من مكان واحد</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">هذه المساحة تعرض فقط البيانات التي يسمح بها ارتباطك الصحي. لا يتم إنشاء جلسة أو صلاحية من خلال الواجهة وحدها.</p>
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-white px-4 py-3 text-sm text-slate-600 shadow-sm"><CheckCircle2 className="h-5 w-5 text-emerald-600" /> وصولك محمي بعلاقة صحية موثقة</div>
            </CardContent>
          </Card>
          <QueryStateMessage query={dashboard} />
          {!dashboard.isLoading && !dashboard.isError && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <MetricCard label="المواعيد القادمة" value={dashboardData.appointments?.upcoming ?? 0} description="مواعيد بحالة محجوز" icon={CalendarClock} />
              <MetricCard label="الأدوية الفعالة" value={dashboardData.medications?.active ?? 0} description="أدوية ظاهرة في ملفك" icon={Pill} />
              <MetricCard label="نتائج المختبر" value={dashboardData.laboratory?.recent_results ?? 0} description="أحدث النتائج المتاحة" icon={FlaskConical} />
              <MetricCard label="الدراسات الشعاعية" value={dashboardData.radiology?.recent_studies ?? 0} description="دراسات حديثة" icon={Activity} />
              <MetricCard label="أفراد الأسرة" value={dashboardData.family?.members ?? 0} description="علاقات أسرية مرتبطة" icon={UsersRound} />
              <MetricCard label="التنبيهات غير المقروءة" value={dashboardData.notifications?.unread ?? 0} description="تنبيهات تحتاج انتباهك" icon={BellRing} />
            </div>
          )}
        </>
      ) : (
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <QueryStateMessage query={current.query} />
            {!current.query.isLoading && !current.query.isError && current.rows.length === 0 && (
              <div className="rounded-lg border border-dashed p-8 text-center text-sm text-slate-500">{current.empty}</div>
            )}
            {!current.query.isLoading && !current.query.isError && current.rows.length > 0 && (
              <DataTable columns={current.columns} data={current.rows} loading={current.query.isLoading} />
            )}
          </CardContent>
        </Card>
      )}

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="flex flex-wrap border-b" role="tablist" aria-label="خدماتي الصحية">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const selected = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 border-b-2 px-3 py-3 text-sm font-medium transition-colors sm:px-4 ${selected ? "border-indigo-600 text-indigo-700" : "border-transparent text-slate-500 hover:border-slate-200 hover:text-slate-700"}`}
                >
                  <Icon className="h-4 w-4" />{tab.label}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
