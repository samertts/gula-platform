import { useQuery } from "@tanstack/react-query";
import { complianceApi } from "@/api/endpoints";
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { FileCheck, Shield, Activity, AlertTriangle } from "lucide-react";

export function CompliancePage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["compliance"],
    queryFn: () => complianceApi.systemStatus(),
  });
  const { data: audit } = useQuery({
    queryKey: ["compliance", "audit"],
    queryFn: () => complianceApi.auditSummary(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const dbOk = data?.services?.database?.status === "pass";
  const apiOk = data?.services?.api?.status === "pass";
  const overall = dbOk && apiOk ? "pass" : "fail";
  const checklist = data?.compliance_checklist ?? {};

  return (
    <div className="space-y-6">
      <PageHeader title="الامتثال" description="حالة الامتثال التنظيمي والفني" />

      <Card>
        <CardContent className="flex items-center gap-4 p-6">
          <div className={`flex h-16 w-16 items-center justify-center rounded-full ${overall === "pass" ? "bg-emerald-100 dark:bg-emerald-900/30" : "bg-red-100 dark:bg-red-900/30"}`}>
            <Shield className={`h-8 w-8 ${overall === "pass" ? "text-emerald-600" : "text-red-600"}`} />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">حالة النظام</p>
            <Badge variant={overall === "pass" ? "success" : "destructive"} className="mt-1 text-sm">
              {overall === "pass" ? "متوافق" : "يوجد خلل"}
            </Badge>
            <p className="mt-1 text-xs text-muted-foreground">
              قاعدة البيانات: {dbOk ? "سليمة" : "تعذّر الوصول"} · النظام الأساسي: {apiOk ? "سليم" : "خلل"} · البيئة: {data?.environment ?? "-"}
            </p>
          </div>
        </CardContent>
      </Card>

      {(data?.alerts ?? []).length > 0 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> التنبيهات</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {(data?.alerts ?? []).map((alert) => (
                <li key={alert} className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-sm">{alert}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><FileCheck className="h-5 w-5" /> قائمة التحقق من الامتثال</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(checklist).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between gap-2 rounded-lg border p-2">
                  <span dir="ltr" className="font-mono text-xs text-muted-foreground">{key}</span>
                  <span className="text-xs">{value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5" /> سجل التدقيق</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border p-3">
                <p className="text-2xl font-bold" dir="ltr">{audit?.total_audit_events ?? 0}</p>
                <p className="text-xs text-muted-foreground">إجمالي أحداث التدقيق</p>
              </div>
              <div className="rounded-lg border p-3">
                <p className="text-2xl font-bold">{Object.keys(audit?.actions_breakdown ?? {}).length}</p>
                <p className="text-xs text-muted-foreground">أنواع الأحداث</p>
              </div>
            </div>
            <div className="space-y-1">
              {Object.entries(audit?.actions_breakdown ?? {}).slice(0, 6).map(([action, count]) => (
                <div key={action} className="flex items-center justify-between text-sm">
                  <span dir="ltr" className="font-mono text-xs">{action}</span>
                  <span className="font-medium" dir="ltr">{count}</span>
                </div>
              ))}
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()}>تحديث</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
