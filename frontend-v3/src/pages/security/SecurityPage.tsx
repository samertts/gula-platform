import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { securityApi, serviceAccountsApi } from "@/api/endpoints";
import type { ServiceAccount } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Input } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { Shield, Key, Lock, AlertTriangle, Plus, Trash2, RefreshCw, Copy } from "lucide-react";

export function SecurityPage() {
  const queryClient = useQueryClient();
  const { isLoading, error, refetch } = useQuery({
    queryKey: ["security"],
    queryFn: () => securityApi.status(),
  });
  const { data: accounts, isLoading: loadingAccounts } = useQuery({
    queryKey: ["service-accounts"],
    queryFn: () => serviceAccountsApi.list(),
  });
  const [name, setName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (accountName: string) => serviceAccountsApi.create({ name: accountName, roles: ["staff"] }),
    onSuccess: (result) => {
      setCreatedKey(result.api_key);
      setName("");
      queryClient.invalidateQueries({ queryKey: ["service-accounts"] });
    },
    onError: (e: Error) => setErrorMsg(e.message),
  });

  const revokeMutation = useMutation({
    mutationFn: (id: number) => serviceAccountsApi.revoke(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["service-accounts"] });
    },
    onError: (e: Error) => setErrorMsg(e.message),
  });

  const rotateMutation = useMutation({
    mutationFn: (id: number) => serviceAccountsApi.rotate(id),
    onSuccess: (result) => {
      setCreatedKey(result.api_key);
      setErrorMsg(null);
    },
    onError: (e: Error) => setErrorMsg(e.message),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const copyKey = async () => {
    if (createdKey) await navigator.clipboard.writeText(createdKey);
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الأمان" description="إعدادات الأمان والحماية" />

      {errorMsg && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{errorMsg}</div>
      )}

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

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" /> حسابات الخدمة
            <span className="text-sm font-normal text-muted-foreground">مفاتيح API للتكاملات والأنظمة الخارجية</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {createdKey && (
            <div className="flex items-center justify-between gap-2 rounded-lg border border-primary/40 bg-primary/10 p-3 text-sm">
              <code dir="ltr" className="break-all">{createdKey}</code>
              <Button size="sm" variant="outline" onClick={copyKey}><Copy className="h-4 w-4" /> نسخ</Button>
            </div>
          )}
          <div className="flex gap-2">
            <Input
              placeholder="اسم الحساب (مثال: نظام التحاليل الخارجي)"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Button onClick={() => createMutation.mutate(name)} disabled={!name.trim() || createMutation.isPending}>
              <Plus className="h-4 w-4" /> إنشاء
            </Button>
          </div>
          {loadingAccounts ? (
            <LoadingSpinner />
          ) : (
            <div className="rounded-lg border">
              {accounts && accounts.length > 0 ? (
                <div className="divide-y">
                  {accounts.map((a: ServiceAccount) => (
                    <div key={a.id} className="flex items-center justify-between gap-2 p-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{a.name}</span>
                          <Badge variant={a.is_active ? "default" : "secondary"}>{a.is_active ? "نشط" : "ملغى"}</Badge>
                        </div>
                        {a.description && <p className="text-sm text-muted-foreground">{a.description}</p>}
                        <p className="text-xs text-muted-foreground">
                          آخر استخدام: {a.last_used_at ? new Date(a.last_used_at).toLocaleString("ar-IQ") : "لم يُستخدم"}
                        </p>
                      </div>
                      <div className="flex shrink-0 gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => rotateMutation.mutate(a.id)}
                          disabled={rotateMutation.isPending}
                        >
                          <RefreshCw className="h-4 w-4" /> تدوير المفتاح
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => revokeMutation.mutate(a.id)}
                          disabled={!a.is_active || revokeMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4" /> إلغاء
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="p-4 text-sm text-muted-foreground">لا توجد حسابات خدمة بعد</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
