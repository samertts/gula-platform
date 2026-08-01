import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { mfaApi, securityApi, serviceAccountsApi, adminApi } from "@/api/endpoints";
import type { ServiceAccount } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Input } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { Shield, Key, Lock, AlertTriangle, Plus, Trash2, RefreshCw, Copy, Smartphone } from "lucide-react";

export function SecurityPage() {
  const queryClient = useQueryClient();
  const { isLoading, error, refetch } = useQuery({
    queryKey: ["security"],
    queryFn: () => securityApi.status(),
  });
  const { data: mfa, isLoading: loadingMfa } = useQuery({
    queryKey: ["mfa"],
    queryFn: () => mfaApi.status(),
  });
  const { data: accounts, isLoading: loadingAccounts } = useQuery({
    queryKey: ["service-accounts"],
    queryFn: () => serviceAccountsApi.list(),
  });
  const { data: audit, isLoading: loadingAudit, refetch: refetchAudit } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => adminApi.auditLogs({ limit: 20 }),
  });
  const [name, setName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [mfaStep, setMfaStep] = useState<"idle" | "setup" | "verify">("idle");
  const [mfaSecret, setMfaSecret] = useState<string | null>(null);
  const [mfaUri, setMfaUri] = useState<string | null>(null);
  const [mfaBackupCodes, setMfaBackupCodes] = useState<string[]>([]);
  const [totpToken, setTotpToken] = useState("");

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

  const setupMfaMutation = useMutation({
    mutationFn: () => mfaApi.setupTotp(),
    onSuccess: (result) => {
      setMfaSecret(result.secret);
      setMfaUri(result.uri);
      setMfaBackupCodes(result.backup_codes);
      setMfaStep("verify");
      setErrorMsg(null);
    },
    onError: (e: Error) => setErrorMsg(e.message),
  });

  const verifyMfaMutation = useMutation({
    mutationFn: (token: string) => mfaApi.verifyTotp(token),
    onSuccess: () => {
      setMfaStep("idle");
      setTotpToken("");
      setMfaSecret(null);
      setMfaUri(null);
      setMfaBackupCodes([]);
      queryClient.invalidateQueries({ queryKey: ["mfa"] });
    },
    onError: (e: Error) => setErrorMsg(e.message),
  });

  const removeDeviceMutation = useMutation({
    mutationFn: (deviceId: number) => mfaApi.removeDevice(deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mfa"] });
    },
    onError: (e: Error) => setErrorMsg(e.message),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const copyKey = async (value: string) => {
    if (value) await navigator.clipboard.writeText(value);
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
            {loadingMfa ? (
              <LoadingSpinner />
            ) : mfa?.mfa_enabled ? (
              <>
                <Badge variant="success">مفعلة</Badge>
                <div className="rounded-lg border">
                  {(mfa.devices ?? []).length > 0 ? (
                    <div className="divide-y">
                      {mfa.devices.map((device) => (
                        <div key={device.id} className="flex items-center justify-between gap-2 p-3">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <Smartphone className="h-4 w-4 text-muted-foreground" />
                              <span className="font-medium">{device.device_name || device.device_type}</span>
                              {device.is_primary && <Badge variant="secondary">أساسي</Badge>}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              {device.device_type} · أُضيف {new Date(device.created_at).toLocaleDateString("ar-IQ")}
                            </p>
                          </div>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => removeDeviceMutation.mutate(device.id)}
                            disabled={removeDeviceMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4" /> إزالة
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="p-3 text-sm text-muted-foreground">لا توجد أجهزة مقيدة</p>
                  )}
                </div>
                <Button variant="outline" size="sm" onClick={() => setMfaStep("idle")} disabled={setupMfaMutation.isPending}>
                  <Plus className="h-4 w-4" /> إضافة جهاز جديد
                </Button>
              </>
            ) : (
              <>
                <Badge variant="secondary">غير مفعلة</Badge>
                <p className="text-sm text-muted-foreground">فعّل المصادقة الثنائية لحماية حسابك من الوصول غير المصرح به</p>
                {mfaStep === "idle" && (
                  <div><Button onClick={() => setupMfaMutation.mutate()} disabled={setupMfaMutation.isPending}><Lock className="h-4 w-4" /> تفعيل المصادقة الثنائية</Button></div>
                )}
                {mfaStep === "verify" && mfaSecret && (
                  <div className="space-y-3 rounded-lg border border-primary/40 bg-primary/5 p-3">
                    <p className="text-sm">1. أضف المفتاح إلى تطبيق المصادقة:</p>
                    <div className="flex items-center justify-between gap-2">
                      <code dir="ltr" className="break-all text-sm">{mfaSecret}</code>
                      <Button size="sm" variant="outline" onClick={() => copyKey(mfaSecret)}><Copy className="h-4 w-4" /></Button>
                    </div>
                    <p className="text-xs text-muted-foreground break-all" dir="ltr">{mfaUri}</p>
                    <p className="text-sm">2. أدخل الرمز من التطبيق:</p>
                    <div className="flex gap-2">
                      <Input
                        dir="ltr"
                        placeholder="000000"
                        value={totpToken}
                        onChange={(e) => setTotpToken(e.target.value)}
                        className="max-w-[140px] font-mono"
                      />
                      <Button onClick={() => verifyMfaMutation.mutate(totpToken)} disabled={!totpToken.trim() || verifyMfaMutation.isPending}>
                        تأكيد
                      </Button>
                    </div>
                    {mfaBackupCodes.length > 0 && (
                      <div>
                        <p className="text-sm">رموز النسخ الاحتياطي (احتفظ بها بأمان):</p>
                        <div className="flex flex-wrap gap-1 pt-1" dir="ltr">
                          {mfaBackupCodes.map((code) => (
                            <code key={code} className="rounded bg-muted px-1.5 py-0.5 text-xs">{code}</code>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Shield className="h-5 w-5" /> جلسات النشطة</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">لا توجد جلسات نشطة أخرى</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center justify-between"><span className="flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> سجل الأمان</span><Button size="sm" variant="outline" onClick={() => refetchAudit()}>تحديث</Button></CardTitle></CardHeader>
          <CardContent>
            {loadingAudit ? (
              <LoadingSpinner />
            ) : (audit?.logs ?? []).length > 0 ? (
              <div className="max-h-64 space-y-1 overflow-y-auto">
                {(audit?.logs ?? []).slice(0, 20).map((log) => (
                  <div key={log.id} className="flex items-center justify-between gap-2 rounded border p-2 text-sm">
                    <div className="min-w-0">
                      <span dir="ltr"><Badge variant="secondary" className="mr-2">{log.action}</Badge></span>
                      <span className="text-xs text-muted-foreground">{log.resource_type}</span>
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground" dir="ltr">
                      {log.created_at ? new Date(log.created_at).toLocaleString("ar-IQ") : "-"}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">لا توجد أحداث أمنية مسجلة</p>
            )}
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
              <Button size="sm" variant="outline" onClick={() => copyKey(createdKey ?? "")}><Copy className="h-4 w-4" /> نسخ</Button>
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
