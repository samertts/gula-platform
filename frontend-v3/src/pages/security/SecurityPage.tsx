import { useQuery } from "@tanstack/react-query";
import { securityApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { Shield, Key, Lock, AlertTriangle } from "lucide-react";

export function SecurityPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["security"],
    queryFn: () => securityApi.status(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader title="الأمان" description="إعدادات الأمان والحماية" />

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Key className="h-5 w-5" /> كلمة المرور</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">آخر تغيير: -</p>
            <Button variant="outline">تغيير كلمة المرور</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Lock className="h-5 w-5" /> المصادقة الثنائية</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Badge variant="secondary">غير مفعلة</Badge>
            <div><Button variant="outline">تفعيل المصادقة الثنائية</Button></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Shield className="h-5 w-5" /> جلسات النشطة</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">لا توجد جلسات نشطة أخرى</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> سجل الأمان</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">سيتم عرض سجل الأمان هنا</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
