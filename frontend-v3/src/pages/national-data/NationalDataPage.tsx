import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { nationalDataApi } from "@/api/endpoints";
import {
  Card, CardContent, CardHeader, CardTitle,
  Badge, DataTable,
} from "@/components/ui";
import {
  PageHeader, LoadingSpinner, EmptyState, ErrorDisplay,
} from "@/components/shared/PageComponents";
import { formatDate } from "@/lib/utils";
import type { ColumnDef } from "@tanstack/react-table";
import { Database, BookOpen, Shield, CheckCircle2 } from "lucide-react";

function getStatusBadgeVariant(
  status: string,
): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" {
  const map: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    active: "success",
    resolved: "default",
    pending: "warning",
    failed: "destructive",
    completed: "success",
    in_progress: "secondary",
    duplicate: "destructive",
  };
  return map[status] || "secondary";
}

function extractList<T>(data: unknown): T[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  const obj = data as Record<string, unknown>;
  return (obj.items as T[]) || (obj.records as T[]) || (obj.results as T[]) || [];
}

interface GoldenRecord {
  id: string;
  patient_name: string;
  national_id: string;
  confidence_score: number;
  status: string;
}

interface CatalogEntry {
  id: string;
  name: string;
  type: string;
  description: string;
  source: string;
  created_at: string;
}

interface DeidJob {
  job_id: string;
  status: string;
  records_processed: number;
  created_at: string;
  completed_at: string | null;
}

interface QualitySummary {
  id: string;
  overall_score: number;
  completeness: number;
  accuracy: number;
  consistency: number;
  timeliness: number;
  checked_at: string;
  issues_found: number;
  status: string;
}

export function NationalDataPage() {
  const [activeTab, setActiveTab] = useState("golden-records");

  const goldenRecordsQuery = useQuery({
    queryKey: ["national-data", "golden-records"],
    queryFn: () => nationalDataApi.listGoldenRecords(),
  });

  const dataCatalogQuery = useQuery({
    queryKey: ["national-data", "data-catalog"],
    queryFn: () => nationalDataApi.listDataCatalog(),
  });

  const deidJobsQuery = useQuery({
    queryKey: ["national-data", "deid-jobs"],
    queryFn: () => nationalDataApi.listDeidentificationJobs(),
  });

  const qualityQuery = useQuery({
    queryKey: ["national-data", "quality"],
    queryFn: () => nationalDataApi.recordDataQualityCheck({}),
  });

  const goldenRecords = extractList<GoldenRecord>(goldenRecordsQuery.data);
  const catalogEntries = extractList<CatalogEntry>(dataCatalogQuery.data);
  const deidJobs = extractList<DeidJob>(deidJobsQuery.data);
  const qualityData = qualityQuery.data as QualitySummary | null;

  const tabs = [
    { id: "golden-records", label: "السجلات الذهبية", icon: Database },
    { id: "data-catalog", label: "كتالوج البيانات", icon: BookOpen },
    { id: "deid-jobs", label: "وظائف إخفاء الهوية", icon: Shield },
    { id: "quality", label: "جودة البيانات", icon: CheckCircle2 },
  ];

  const goldenRecordColumns: ColumnDef<GoldenRecord>[] = [
    { accessorKey: "id", header: "معرف السجل" },
    { accessorKey: "patient_name", header: "اسم المريض" },
    { accessorKey: "national_id", header: "الرقم الوطني" },
    {
      accessorKey: "confidence_score",
      header: "درجة الثقة",
      cell: ({ row }) => {
        const score = row.original.confidence_score;
        const pct = typeof score === "number" ? Math.round(score * 100) : score;
        const variant = score >= 0.9 ? "success" : score >= 0.7 ? "warning" : "destructive";
        return <Badge variant={variant}>{pct}%</Badge>;
      },
    },
    {
      accessorKey: "status",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={getStatusBadgeVariant(row.original.status)}>
          {row.original.status}
        </Badge>
      ),
    },
  ];

  const catalogColumns: ColumnDef<CatalogEntry>[] = [
    { accessorKey: "name", header: "اسم المدخل" },
    { accessorKey: "type", header: "النوع" },
    { accessorKey: "description", header: "الوصف" },
    { accessorKey: "source", header: "المصدر" },
    {
      accessorKey: "created_at",
      header: "تاريخ الإنشاء",
      cell: ({ row }) => formatDate(row.original.created_at),
    },
  ];

  const deidJobColumns: ColumnDef<DeidJob>[] = [
    { accessorKey: "job_id", header: "معرف الوظيفة" },
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
      accessorKey: "records_processed",
      header: "السجلات المعالجة",
      cell: ({ row }) => row.original.records_processed?.toLocaleString() ?? "-",
    },
    {
      accessorKey: "created_at",
      header: "تاريخ الإنشاء",
      cell: ({ row }) => formatDate(row.original.created_at),
    },
    {
      accessorKey: "completed_at",
      header: "تاريخ الإكمال",
      cell: ({ row }) => (row.original.completed_at ? formatDate(row.original.completed_at) : "—"),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="البيانات الوطنية"
        description="إدارة البيانات الصحية الوطنية والسجلات الذهبية"
      />

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

      {activeTab === "golden-records" && (
        <Card>
          <CardContent className="pt-6">
            {goldenRecordsQuery.isLoading ? (
              <LoadingSpinner />
            ) : goldenRecordsQuery.error ? (
              <ErrorDisplay onRetry={() => goldenRecordsQuery.refetch()} />
            ) : goldenRecords.length === 0 ? (
              <EmptyState
                icon={Database}
                title="لا توجد سجلات ذهبية"
                description="لم يتم العثور على أي سجلات ذهبية بعد"
              />
            ) : (
              <DataTable
                columns={goldenRecordColumns}
                data={goldenRecords}
                loading={false}
              />
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === "data-catalog" && (
        <Card>
          <CardContent className="pt-6">
            {dataCatalogQuery.isLoading ? (
              <LoadingSpinner />
            ) : dataCatalogQuery.error ? (
              <ErrorDisplay onRetry={() => dataCatalogQuery.refetch()} />
            ) : catalogEntries.length === 0 ? (
              <EmptyState
                icon={BookOpen}
                title="كتالوج البيانات فارغ"
                description="لم يتم إضافة أي مدخلات إلى كتالوج البيانات بعد"
              />
            ) : (
              <DataTable
                columns={catalogColumns}
                data={catalogEntries}
                loading={false}
              />
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === "deid-jobs" && (
        <Card>
          <CardContent className="pt-6">
            {deidJobsQuery.isLoading ? (
              <LoadingSpinner />
            ) : deidJobsQuery.error ? (
              <ErrorDisplay onRetry={() => deidJobsQuery.refetch()} />
            ) : deidJobs.length === 0 ? (
              <EmptyState
                icon={Shield}
                title="لا توجد وظائف إخفاء هوية"
                description="لم يتم إنشاء أي وظائف إخفاء هوية بعد"
              />
            ) : (
              <DataTable
                columns={deidJobColumns}
                data={deidJobs}
                loading={false}
              />
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === "quality" && (
        <>
          {qualityQuery.isLoading ? (
            <LoadingSpinner />
          ) : qualityQuery.error ? (
            <ErrorDisplay onRetry={() => qualityQuery.refetch()} />
          ) : !qualityData ? (
            <EmptyState
              icon={CheckCircle2}
              title="لا توجد بيانات جودة"
              description="لم يتم تسجيل أي فحص جودة للبيانات بعد"
            />
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                    النتيجة الإجمالية
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">
                    {Math.round((qualityData.overall_score ?? 0) * 100)}%
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    آخر فحص: {formatDate(qualityData.checked_at)}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-blue-500" />
                    الاكتمال
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">
                    {Math.round((qualityData.completeness ?? 0) * 100)}%
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-purple-500" />
                    الدقة
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">
                    {Math.round((qualityData.accuracy ?? 0) * 100)}%
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-amber-500" />
                    الاتساق
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">
                    {Math.round((qualityData.consistency ?? 0) * 100)}%
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-indigo-500" />
                    التوقيت
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">
                    {Math.round((qualityData.timeliness ?? 0) * 100)}%
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-rose-500" />
                    المشكلات
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">
                    {qualityData.issues_found ?? 0}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    مشكلة تم اكتشافها
                  </p>
                </CardContent>
              </Card>

              <Card className="md:col-span-2 lg:col-span-3">
                <CardHeader>
                  <CardTitle>حالة الجودة</CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge
                    variant={
                      qualityData.status === "good"
                        ? "success"
                        : qualityData.status === "fair"
                          ? "warning"
                          : "destructive"
                    }
                    className="text-sm px-3 py-1"
                  >
                    {qualityData.status === "good"
                      ? "جيدة"
                      : qualityData.status === "fair"
                        ? "متوسطة"
                        : qualityData.status === "poor"
                          ? "ضعيفة"
                          : qualityData.status}
                  </Badge>
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  );
}
