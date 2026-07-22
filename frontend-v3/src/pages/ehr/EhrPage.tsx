import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { patientsApi, ordersApi, resultsApi } from "@/api/endpoints";
import {
  Card, CardContent, CardHeader, CardTitle,
  Badge, Input, Button, DataTable,
} from "@/components/ui";
import {
  PageHeader, LoadingSpinner, EmptyState, ErrorDisplay,
} from "@/components/shared/PageComponents";
import { formatDate, formatDateTime, getGenderLabel } from "@/lib/utils";
import type { ColumnDef } from "@tanstack/react-table";
import type { LabOrder, LabResult } from "@/types";
import { Search, User, ClipboardList, Activity, Clock } from "lucide-react";

function getStatusBadgeVariant(
  status: string,
): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" {
  const map: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    pending: "warning",
    completed: "success",
    validated: "default",
    cancelled: "destructive",
    in_progress: "secondary",
  };
  return map[status] || "secondary";
}

function getFlagBadgeVariant(
  flag: string | null | undefined,
): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" {
  const map: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    normal: "success",
    high: "warning",
    low: "warning",
    critical_high: "destructive",
    critical_low: "destructive",
  };
  return map[flag || ""] || "secondary";
}

function extractList<T>(data: unknown): T[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  const obj = data as Record<string, unknown>;
  return (obj.items as T[]) || (obj.orders as T[]) || (obj.results as T[]) || [];
}

export function EhrPage() {
  const [patientIdInput, setPatientIdInput] = useState("");
  const [submittedId, setSubmittedId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState("overview");

  const patientQuery = useQuery({
    queryKey: ["ehr-patient", submittedId],
    queryFn: () => patientsApi.get(submittedId!),
    enabled: submittedId !== null,
    retry: false,
  });

  const ordersQuery = useQuery({
    queryKey: ["ehr-orders", submittedId],
    queryFn: () => ordersApi.list({ limit: 200 }),
    enabled: submittedId !== null,
  });

  const healthId = patientQuery.data?.health_id;

  const resultsQuery = useQuery({
    queryKey: ["ehr-results", healthId],
    queryFn: () =>
      resultsApi.list({ ...(healthId ? { health_id: healthId } : {}), limit: 200 }),
    enabled: submittedId !== null && !!healthId,
  });

  const patientOrders = useMemo(() => {
    const all = extractList<LabOrder>(ordersQuery.data);
    return submittedId ? all.filter((o) => o.patient_id === submittedId) : [];
  }, [ordersQuery.data, submittedId]);

  const patientResults = useMemo(() => {
    return extractList<LabResult>(resultsQuery.data);
  }, [resultsQuery.data]);

  const recentOrders = useMemo(
    () =>
      [...patientOrders]
        .sort(
          (a, b) =>
            new Date(b.created_at || "").getTime() -
            new Date(a.created_at || "").getTime(),
        )
        .slice(0, 5),
    [patientOrders],
  );

  const recentResults = useMemo(
    () =>
      [...patientResults]
        .sort(
          (a, b) =>
            new Date(b.created_at || "").getTime() -
            new Date(a.created_at || "").getTime(),
        )
        .slice(0, 5),
    [patientResults],
  );

  const timelineItems = useMemo(() => {
    const items: Array<{
      type: "order" | "result";
      date: string;
      data: LabOrder | LabResult;
    }> = [];
    patientOrders.forEach((o) => {
      if (o.created_at) items.push({ type: "order" as const, date: o.created_at, data: o });
    });
    patientResults.forEach((r) => {
      if (r.created_at) items.push({ type: "result" as const, date: r.created_at, data: r });
    });
    return items.sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
    );
  }, [patientOrders, patientResults]);

  const handleSearch = () => {
    const id = parseInt(patientIdInput, 10);
    if (!isNaN(id)) setSubmittedId(id);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  };

  const tabs = [
    { id: "overview", label: "نظرة عامة", icon: User },
    { id: "orders", label: "سجل الطلبات", icon: ClipboardList },
    { id: "results", label: "سجل النتائج", icon: Activity },
    { id: "timeline", label: "الخط الزمني", icon: Clock },
  ];

  const orderColumns: ColumnDef<LabOrder>[] = [
    { accessorKey: "id", header: "رقم الطلب" },
    { accessorKey: "patient_name", header: "اسم المريض" },
    { accessorKey: "doctor_name", header: "اسم الطبيب" },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={getStatusBadgeVariant(row.original.status)}>
          {row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: "results_count",
      header: "عدد الفحوصات",
      cell: ({ row }) => row.original.results_count ?? "-",
    },
    {
      accessorKey: "created_at",
      header: "التاريخ",
      cell: ({ row }) => formatDate(row.original.created_at),
    },
  ];

  const resultColumns: ColumnDef<LabResult>[] = [
    { accessorKey: "id", header: "معرف النتيجة" },
    { accessorKey: "test_name", header: "اسم الفحص" },
    {
      accessorKey: "value",
      header: "القيمة",
      cell: ({ row }) => row.original.value ?? row.original.value_text ?? "-",
    },
    {
      accessorKey: "flag",
      header: "العلامة",
      cell: ({ row }) => {
        const flag = row.original.flag;
        return flag ? (
          <Badge variant={getFlagBadgeVariant(flag)}>{flag}</Badge>
        ) : (
          <Badge variant="outline">-</Badge>
        );
      },
    },
    {
      accessorKey: "created_at",
      header: "التاريخ",
      cell: ({ row }) => formatDate(row.original.created_at),
    },
  ];

  if (submittedId === null) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="السجل الصحي الإلكتروني"
          description="عرض السجل الصحي الكامل للمريض"
        />
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <Input
                type="number"
                placeholder="أدخل رقم المريض..."
                value={patientIdInput}
                onChange={(e) => setPatientIdInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="max-w-xs"
              />
              <Button onClick={handleSearch}>
                <Search className="h-4 w-4" />
                بحث
              </Button>
            </div>
          </CardContent>
        </Card>
        <EmptyState
          icon={User}
          title="أدخل رقم المريض"
          description="أدخل رقم المريض في الحقل أعلاه لعرض سجله الصحي"
        />
      </div>
    );
  }

  if (patientQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="السجل الصحي الإلكتروني"
          description="جاري تحميل بيانات المريض..."
        />
        <LoadingSpinner />
      </div>
    );
  }

  if (patientQuery.error) {
    return (
      <div className="space-y-6">
        <PageHeader title="السجل الصحي الإلكتروني" />
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <Input
                type="number"
                placeholder="أدخل رقم المريض..."
                value={patientIdInput}
                onChange={(e) => setPatientIdInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="max-w-xs"
              />
              <Button onClick={handleSearch}>
                <Search className="h-4 w-4" />
                بحث
              </Button>
            </div>
          </CardContent>
        </Card>
        <ErrorDisplay
          error="تعذر العثور على المريض. يرجى التحقق من الرقم."
          onRetry={() => setSubmittedId(null)}
        />
      </div>
    );
  }

  const patient = patientQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="السجل الصحي الإلكتروني"
        description={`المريض: ${patient?.full_name || ""}`}
      />

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Input
              type="number"
              placeholder="أدخل رقم المريض..."
              value={patientIdInput}
              onChange={(e) => setPatientIdInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="max-w-xs"
            />
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4" />
              بحث
            </Button>
            <span className="text-sm text-muted-foreground">
              المريض رقم: {submittedId}
            </span>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-1 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                معلومات المريض
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">الاسم</p>
                  <p className="font-medium">{patient?.full_name || "—"}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">رقم الهاتف</p>
                  <p className="font-medium" dir="ltr">{patient?.phone || "—"}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">تاريخ الميلاد</p>
                  <p className="font-medium">{formatDate(patient?.birth_date)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">الجنس</p>
                  <p className="font-medium">{getGenderLabel(patient?.gender)}</p>
                </div>
              </div>
              {patient?.health_id && (
                <div className="mt-3">
                  <p className="text-sm text-muted-foreground">معرف الصحة</p>
                  <p className="font-medium font-mono text-xs">{patient.health_id}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ClipboardList className="h-5 w-5" />
                  آخر الطلبات
                </CardTitle>
              </CardHeader>
              <CardContent>
                {ordersQuery.isLoading ? (
                  <LoadingSpinner />
                ) : recentOrders.length === 0 ? (
                  <EmptyState icon={ClipboardList} title="لا توجد طلبات" />
                ) : (
                  <ul className="space-y-3">
                    {recentOrders.map((order) => (
                      <li
                        key={order.id}
                        className="flex items-center justify-between border-b pb-2 last:border-b-0"
                      >
                        <div>
                          <p className="font-medium text-sm">
                            طلب #{order.id}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(order.created_at)}
                          </p>
                        </div>
                        <Badge variant={getStatusBadgeVariant(order.status)}>
                          {order.status}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  آخر النتائج
                </CardTitle>
              </CardHeader>
              <CardContent>
                {resultsQuery.isLoading ? (
                  <LoadingSpinner />
                ) : recentResults.length === 0 ? (
                  <EmptyState icon={Activity} title="لا توجد نتائج" />
                ) : (
                  <ul className="space-y-3">
                    {recentResults.map((result) => (
                      <li
                        key={result.id}
                        className="flex items-center justify-between border-b pb-2 last:border-b-0"
                      >
                        <div>
                          <p className="font-medium text-sm">
                            {result.test_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(result.created_at)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm">
                            {result.value ?? result.value_text ?? "-"}
                          </span>
                          {result.flag && (
                            <Badge variant={getFlagBadgeVariant(result.flag)}>
                              {result.flag}
                            </Badge>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {activeTab === "orders" && (
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={orderColumns}
              data={patientOrders}
              loading={ordersQuery.isLoading}
            />
          </CardContent>
        </Card>
      )}

      {activeTab === "results" && (
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={resultColumns}
              data={patientResults}
              loading={resultsQuery.isLoading}
            />
          </CardContent>
        </Card>
      )}

      {activeTab === "timeline" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              الخط الزمني
            </CardTitle>
          </CardHeader>
          <CardContent>
            {ordersQuery.isLoading || resultsQuery.isLoading ? (
              <LoadingSpinner />
            ) : timelineItems.length === 0 ? (
              <EmptyState
                icon={Clock}
                title="لا توجد أحداث"
                description="لا توجد طلبات أو نتائج لهذا المريض"
              />
            ) : (
              <div className="relative space-y-4 before:absolute before:start-[11px] before:top-2 before:h-[calc(100%-16px)] before:w-0.5 before:bg-border">
                {timelineItems.map((item, idx) => (
                  <div
                    key={`${item.type}-${(item.data as LabOrder & LabResult).id}-${idx}`}
                    className="relative flex items-start gap-4"
                  >
                    <div
                      className={`mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 ${
                        item.type === "order"
                          ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
                          : "border-emerald-500 bg-emerald-50 dark:bg-emerald-950"
                      }`}
                    >
                      {item.type === "order" ? (
                        <ClipboardList className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                      ) : (
                        <Activity className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium">
                        {item.type === "order"
                          ? `طلب #${(item.data as LabOrder).id}`
                          : `نتيجة: ${(item.data as LabResult).test_name}`}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatDateTime(item.date)}
                      </p>
                      <div className="mt-1 flex items-center gap-2">
                        {item.type === "order" ? (
                          <Badge
                            variant={getStatusBadgeVariant(
                              (item.data as LabOrder).status,
                            )}
                          >
                            {(item.data as LabOrder).status}
                          </Badge>
                        ) : (
                          <>
                            <span className="text-sm font-medium">
                              {(item.data as LabResult).value ??
                                (item.data as LabResult).value_text ??
                                "-"}
                            </span>
                            {(item.data as LabResult).flag && (
                              <Badge
                                variant={getFlagBadgeVariant(
                                  (item.data as LabResult).flag,
                                )}
                              >
                                {(item.data as LabResult).flag}
                              </Badge>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
