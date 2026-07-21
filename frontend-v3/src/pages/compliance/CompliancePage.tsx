import { useQuery } from "@tanstack/react-query";
import { complianceApi } from "@/api/endpoints";
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { FileCheck, Shield, Activity } from "lucide-react";

export function CompliancePage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["compliance"],
    queryFn: () => complianceApi.systemStatus(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const status = (data as any)?.status || "unknown";

  return (
    <div className="space-y-6">
      <PageHeader title="الامتثال" description="حالة الامتثال التنظيمي والفني" />

      <Card>
        <CardContent className="flex items-center gap-4 p-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
            <Shield className="h-8 w-8 text-emerald-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">حالة النظام</p>
            <Badge variant={status === "compliant" ? "success" : status === "warning" ? "warning" : "destructive"} className="mt-1 text-sm">
              {status}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><FileCheck className="h-5 w-5" /> تقارير الامتثال</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b">
                <span className="text-sm">التدقيق</span>
                <Button variant="outline" size="sm">عرض</Button>
              </div>
              <div className="flex items-center justify-between py-2 border-b">
                <span className="text-sm">الأمان</span>
                <Button variant="outline" size="sm">عرض</Button>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-sm">FHIR</span>
                <Button variant="outline" size="sm">تصدير</Button>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5" /> مؤشرات الأداء</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">سيتم عرض مؤشرات أداء الامتثال هنا</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
