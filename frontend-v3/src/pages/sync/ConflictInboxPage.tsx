import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Bell, CheckCircle2, Clock3, Loader2, RefreshCw, ShieldAlert } from "lucide-react";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { syncApi, type ClinicalNotification, type SyncConflict } from "@/api/endpoints";

const severityLabel: Record<string, string> = {
  P0_CRITICAL: "حرج — تدخل فوري",
  P1_URGENT: "عاجل",
  P2_HIGH: "مرتفع",
  P3_ROUTINE: "اعتيادي",
};

export default function ConflictInboxPage() {
  const [conflicts, setConflicts] = useState<SyncConflict[]>([]);
  const [notifications, setNotifications] = useState<ClinicalNotification[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [conflictRows, notificationRows] = await Promise.all([syncApi.conflicts({ status: "pending", limit: 100 }), syncApi.notifications("unread")]);
      setConflicts(conflictRows);
      setNotifications(notificationRows.items);
    } catch {
      setError("تعذر تحميل مركز التعارضات؛ تحقق من الاتصال والصلاحية.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const acknowledge = async (notification: ClinicalNotification) => {
    setBusy(notification.notification_id);
    try {
      await syncApi.acknowledgeNotification(notification.notification_id);
      setNotifications((items) => items.filter((item) => item.notification_id !== notification.notification_id));
      setMessage("تم تسجيل إقرار الاستلام. الإقرار لا يحل التعارض تلقائيًا.");
    } catch { setError("تعذر تسجيل الإقرار."); } finally { setBusy(null); }
  };

  const resolve = async (conflict: SyncConflict, decision: "accept_server" | "reject_operation") => {
    setBusy(conflict.conflict_id);
    try {
      await syncApi.resolveConflict(conflict.conflict_id, {
        decision,
        reason_code: decision === "accept_server" ? "LATEST_SERVER_VERSION" : "REJECT_STALE_OPERATION",
        reason_note: notes[conflict.conflict_id]?.trim() || "قرار مراجع مخول بعد مقارنة النسخ.",
        expected_server_version: conflict.server_version ?? undefined,
      });
      setMessage("تم إغلاق التعارض مع حفظ سبب القرار في سجل التدقيق.");
      await load();
    } catch { setError("لم يُحل التعارض؛ ربما تغيرت النسخة ويجب إعادة تحميل المقارنة."); } finally { setBusy(null); }
  };

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="مركز التعارضات السريرية" description="الإقرار والتصعيد والحل الموثق — لا توجد قاعدة آخر تعديل يفوز." />
      {notifications.length > 0 && <Card className="border-red-300 bg-red-50 dark:border-red-900/60 dark:bg-red-950/20"><CardHeader><CardTitle className="flex items-center gap-2 text-red-800 dark:text-red-200"><Bell className="h-5 w-5" />تنبيهات تحتاج إقرارًا</CardTitle></CardHeader><CardContent className="space-y-3">{notifications.map((item) => <div key={item.notification_id} className="flex flex-col gap-3 rounded-lg border border-red-200 bg-white p-4 dark:border-red-900/50 dark:bg-background sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{item.title}</p><p className="text-sm text-muted-foreground">{item.message} · {severityLabel[item.severity] || item.severity}</p></div><Button size="sm" onClick={() => void acknowledge(item)} disabled={busy === item.notification_id}>{busy === item.notification_id ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}إقرار الاستلام</Button></div>)}</CardContent></Card>}

      <Card><CardHeader><div className="flex items-center justify-between gap-3"><CardTitle className="flex items-center gap-2"><ShieldAlert className="h-5 w-5 text-amber-600" />التعارضات المفتوحة ({conflicts.length})</CardTitle><Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}تحديث</Button></div></CardHeader><CardContent className="space-y-4">
        {conflicts.length === 0 && <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">لا توجد تعارضات مفتوحة ضمن نطاق صلاحيتك.</div>}
        {conflicts.map((conflict) => <div key={conflict.conflict_id} className="rounded-xl border p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-amber-600" /><h3 className="font-semibold">{conflict.entity_type} · {conflict.entity_id || "عملية محلية"}</h3></div><p className="mt-1 text-xs text-muted-foreground">التعارض: {conflict.conflict_id} · العملية: {conflict.operation_id}</p></div><Badge variant={conflict.severity === "P0_CRITICAL" ? "warning" : "outline"}>{severityLabel[conflict.severity] || conflict.severity}</Badge></div><div className="mt-4 grid gap-3 md:grid-cols-2"><div className="rounded-lg bg-muted/50 p-3"><p className="mb-2 text-xs font-semibold">الاقتراح المحلي</p><pre className="overflow-auto text-xs">{JSON.stringify(conflict.local_payload, null, 2)}</pre></div><div className="rounded-lg bg-muted/50 p-3"><p className="mb-2 text-xs font-semibold">نسخة الخادم</p><pre className="overflow-auto text-xs">{JSON.stringify(conflict.server_snapshot || { version: conflict.server_version }, null, 2)}</pre></div></div><div className="mt-4 flex flex-col gap-3"><label className="text-sm"><span className="mb-1 block font-medium">سبب القرار</span><Input value={notes[conflict.conflict_id] || ""} onChange={(event) => setNotes((current) => ({ ...current, [conflict.conflict_id]: event.target.value }))} placeholder="اكتب سببًا مختصرًا إلزاميًا" /></label><div className="flex flex-wrap gap-2"><Button size="sm" onClick={() => void resolve(conflict, "accept_server")} disabled={busy === conflict.conflict_id}><CheckCircle2 className="h-4 w-4" />اعتماد نسخة الخادم</Button><Button variant="outline" size="sm" onClick={() => void resolve(conflict, "reject_operation")} disabled={busy === conflict.conflict_id}><Clock3 className="h-4 w-4" />رفض العملية المحلية وإبقاء السجل</Button></div></div></div>)}
      </CardContent></Card>
      {(message || error) && <div className={`rounded-lg border px-4 py-3 text-sm ${error ? "border-red-200 bg-red-50 text-red-800" : "border-emerald-200 bg-emerald-50 text-emerald-800"}`} role="status">{error || message}</div>}
    </div>
  );
}
