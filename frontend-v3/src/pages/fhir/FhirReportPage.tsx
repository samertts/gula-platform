import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { complianceApi } from "@/api/endpoints";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Badge,
  Button,
} from "@/components/ui";
import {
  PageHeader,
  ErrorDisplay,
} from "@/components/shared/PageComponents";
import {
  FileText,
  Calendar,
  User,
  Download,
  Printer,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { formatDateTime } from "@/lib/utils";

interface FhirDiagnosticReport {
  resourceType: string;
  id: string;
  status?: string;
  category?: { coding?: { code?: string; display?: string }[]; text?: string }[];
  code?: { coding?: { code?: string; display?: string }[]; text?: string };
  subject?: { reference?: string; display?: string };
  issued?: string;
  performer?: { reference?: string; display?: string }[];
  resultsInterpreter?: { reference?: string; display?: string }[];
  result?: { reference?: string; display?: string }[];
  conclusion?: string;
  presentedForm?: { url?: string; title?: string }[];
  meta?: { versionId?: string; lastUpdated?: string };
}

function ReportSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-start gap-3 py-3 border-b last:border-0">
          <div className="h-8 w-8 rounded-full bg-muted animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-24 bg-muted animate-pulse rounded" />
            <div className="h-4 w-48 bg-muted animate-pulse rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: string | undefined }) {
  if (!status) return null;
  const variant =
    status === "final"
      ? "success"
      : status === "amended" || status === "corrected"
        ? "warning"
        : status === "preliminary" || status === "partial"
          ? "secondary"
          : status === "cancelled" || status === "entered-in-error"
            ? "destructive"
            : "default";
  return <Badge variant={variant}>{status}</Badge>;
}

export function FhirReportPage() {
  const [orderId, setOrderId] = useState("");
  const [searchId, setSearchId] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["fhir-report", searchId],
    queryFn: () => complianceApi.fhirDiagnosticReport(Number(searchId)) as unknown as Promise<FhirDiagnosticReport>,
    enabled: !!searchId,
  });

  const report = data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="تقرير التشخيص FHIR"
        description="عرض تقارير التشخيص المخبرية بتنسيق FHIR DiagnosticReport"
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            البحث عن تقرير
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input
              placeholder="أدخل رقم الطلب..."
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && setSearchId(orderId.trim())}
            />
            <button
              onClick={() => setSearchId(orderId.trim())}
              disabled={!orderId.trim()}
              className="inline-flex h-10 shrink-0 items-center justify-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              بحث
            </button>
          </div>
        </CardContent>
      </Card>

      {isLoading && (
        <Card>
          <CardContent>
            <ReportSkeleton />
          </CardContent>
        </Card>
      )}

      {error && <ErrorDisplay onRetry={() => refetch()} />}

      {!searchId && !isLoading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">أدخل رقم الطلب للبحث</p>
          </CardContent>
        </Card>
      )}

      {report && !isLoading && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  {report.code?.text || report.code?.coding?.[0]?.display || "تقرير تشخيصي"}
                  <StatusBadge status={report.status} />
                </CardTitle>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => window.print()}>
                  <Printer className="h-4 w-4" />
                  طباعة
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4" />
                  تحميل
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-0 md:grid-cols-2">
                {report.category && report.category.length > 0 && (
                  <div className="flex items-start gap-3 py-3 border-b md:border-b-0">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">التصنيف</p>
                      <p className="text-sm font-medium">
                        {report.category.map((c) => c.text || c.coding?.[0]?.display || c.coding?.[0]?.code || "").join(", ")}
                      </p>
                    </div>
                  </div>
                )}
                <div className="flex items-start gap-3 py-3 border-b md:border-b-0">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">تاريخ الإصدار</p>
                    <p className="text-sm font-medium">
                      {report.issued ? formatDateTime(report.issued) : "—"}
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 py-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <User className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">المريض</p>
                    <p className="text-sm font-medium">
                      {report.subject?.display || report.subject?.reference?.replace("Patient/", "") || "—"}
                    </p>
                  </div>
                </div>
                {report.performer && report.performer.length > 0 && (
                  <div className="flex items-start gap-3 py-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                      <User className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">المنفذ</p>
                      <p className="text-sm font-medium">
                        {report.performer.map((p) => p.display || p.reference || "").join(", ") || "—"}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {report.result && report.result.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  النتائج
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {report.result.map((res, idx) => (
                    <li key={idx} className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                      <span>{res.display || res.reference || `نتيجة ${idx + 1}`}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {report.conclusion && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">الاستنتاج</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{report.conclusion}</p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">البيانات الخام (JSON)</CardTitle>
            </CardHeader>
            <CardContent>
              <pre
                className="overflow-auto rounded-lg bg-muted p-4 text-xs max-h-80"
                dir="ltr"
              >
                <code>{JSON.stringify(report, null, 2)}</code>
              </pre>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
