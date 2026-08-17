import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { AlertTriangle, ArrowLeft, CheckCircle2, Clock3, CloudOff, CloudUpload, Loader2, Plus, RefreshCw, ShieldCheck, Wifi } from "lucide-react";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { patientFlowApi, syncApi, type PatientFlowRecord } from "@/api/endpoints";
import { enqueueOfflineOperation, listOfflineOperations, markOfflineOperation, removeOfflineOperation, type OfflineOperation } from "@/services/offlineQueue";

const NEXT_STATE: Record<string, string | undefined> = {
  arrived: "triaged",
  triaged: "in_progress",
  in_progress: "admitted",
  admitted: "discharge_pending",
  discharge_pending: "discharged",
};

const STATE_LABEL: Record<string, string> = {
  planned: "مخطط",
  arrived: "وصل",
  triaged: "تم الفرز",
  in_progress: "قيد الخدمة",
  admitted: "مقبول/منوّم",
  transfer_pending: "بانتظار النقل",
  discharge_pending: "جاهز للخروج",
  discharged: "خرج",
  cancelled: "ملغى",
};

function activeHospitalId(): number {
  const stored = Number(window.localStorage.getItem("gula.activeHospitalId") || "0");
  return Number.isInteger(stored) && stored > 0 ? stored : 0;
}

function deviceId(): string {
  const key = "gula.emergency.deviceId";
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;
  const created = `ER-${crypto.randomUUID()}`;
  window.localStorage.setItem(key, created);
  return created;
}

function deviceSessionToken(): string {
  return window.localStorage.getItem("gula.emergency.deviceSessionToken") || "";
}

function saveDeviceSessionToken(token: string): void {
  window.localStorage.setItem("gula.emergency.deviceSessionToken", token);
}

function operationId(): string {
  return crypto.randomUUID();
}

export default function RapidPatientFlowPage() {
  const [hospitalId, setHospitalId] = useState(activeHospitalId);
  const [patientId, setPatientId] = useState("");
  const [priority, setPriority] = useState("routine");
  const [queue, setQueue] = useState<PatientFlowRecord[]>([]);
  const [offlineQueue, setOfflineQueue] = useState<OfflineOperation[]>([]);
  const [criticalNotifications, setCriticalNotifications] = useState(0);
  const [online, setOnline] = useState(() => navigator.onLine);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refreshOfflineQueue = useCallback(async () => {
    try {
      setOfflineQueue(await listOfflineOperations());
    } catch {
      setError("تعذر قراءة الطابور المحلي؛ لا تغلق الشاشة قبل حفظ الحالات يدويًا.");
    }
  }, []);

  const refresh = useCallback(async () => {
    if (!hospitalId || !navigator.onLine) return;
    setLoading(true);
    setError("");
    try {
      setQueue(await patientFlowApi.queue(hospitalId, { limit: 200 }));
      const notifications = await syncApi.notifications("unread");
      setCriticalNotifications(notifications.items.filter((item) => item.severity === "P0_CRITICAL").length);
    } catch {
      setError("تعذر تحميل الطابور. استمر بالوضع المحلي أو تحقق من الاتصال.");
    } finally {
      setLoading(false);
    }
  }, [hospitalId]);

  const flushOfflineQueue = useCallback(async () => {
    if (!navigator.onLine) return;
    const pending = await listOfflineOperations();
    if (pending.length === 0) return;
    try {
      let token = deviceSessionToken();
      if (!token) {
        const session = await syncApi.registerDevice({ device_id: deviceId(), hospital_id: hospitalId });
        token = session.device_session_token;
        saveDeviceSessionToken(token);
      }
      let result: Awaited<ReturnType<typeof syncApi.pushBatch>>;
      try {
        result = await syncApi.pushBatch({ device_id: deviceId(), operations: pending }, token);
      } catch (cause) {
        const responseStatus = (cause as { response?: { status?: number } }).response?.status;
        if (responseStatus !== 409) throw cause;
        window.localStorage.removeItem("gula.emergency.deviceSessionToken");
        const session = await syncApi.registerDevice({ device_id: deviceId(), hospital_id: hospitalId });
        token = session.device_session_token;
        saveDeviceSessionToken(token);
        result = await syncApi.pushBatch({ device_id: deviceId(), operations: pending }, token);
      }
      for (const item of result.results as { operation_id?: string; status?: string }[]) {
        if (!item.operation_id) continue;
        if (item.status === "accepted" || item.status === "duplicate") {
          await removeOfflineOperation(item.operation_id);
        } else if (item.status === "conflict") {
          await markOfflineOperation(item.operation_id, "conflict");
        } else {
          await markOfflineOperation(item.operation_id, "failed");
        }
      }
      await refreshOfflineQueue();
      setMessage(`اكتملت المزامنة: ${result.accepted_count} مقبولة، ${result.conflict_count} تحتاج مراجعة.`);
    } catch {
      setError("تعذرت المزامنة؛ بقيت العمليات محفوظة محليًا ولم تُحذف.");
    }
  }, [refreshOfflineQueue]);

  useEffect(() => {
    void refreshOfflineQueue();
    void refresh();
    const onOnline = () => {
      setOnline(true);
      void flushOfflineQueue();
      void refresh();
    };
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    const timer = window.setInterval(() => {
      void refreshOfflineQueue();
      void refresh();
      if (navigator.onLine) void flushOfflineQueue();
    }, 15000);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
      window.clearInterval(timer);
    };
  }, [flushOfflineQueue, refresh, refreshOfflineQueue]);

  useEffect(() => {
    if (!online || typeof EventSource === "undefined") return;
    const stream = new EventSource("/national/sync/notifications/stream", { withCredentials: true });
    const onConflict = () => {
      setCriticalNotifications((count) => count + 1);
      setMessage("وصل تنبيه سريري جديد؛ افتح مركز التعارضات للمراجعة.");
    };
    stream.addEventListener("clinical-conflict", onConflict);
    return () => {
      stream.removeEventListener("clinical-conflict", onConflict);
      stream.close();
    };
  }, [online]);

  const activeCount = useMemo(() => queue.filter((entry) => !["discharged", "cancelled"].includes(entry.flow_state)).length, [queue]);

  const queueLocally = async (operation: OfflineOperation, text: string): Promise<boolean> => {
    try {
      await enqueueOfflineOperation(operation);
      await refreshOfflineQueue();
      setMessage(`${text} تم الحفظ على هذا الجهاز وبانتظار المزامنة؛ لم يعتمد مركزيًا بعد.`);
      return true;
    } catch (cause) {
      const detail = cause instanceof Error ? cause.message : "";
      if (detail.toLowerCase().includes("queue is full")) {
        setError("امتلأ الطابور المحلي (5000 عملية). أوقف استقبال الحالات غير الحرجة، واتبع إجراء المؤسسة الورقي، ولا تغلق الشاشة قبل إبلاغ المشرف.");
      } else {
        setError("تعذر حفظ العملية محليًا. لا تغلق الشاشة، واتبع إجراء المؤسسة البديل وأبلغ المشرف فورًا.");
      }
      return false;
    }
  };

  const registerArrival = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!hospitalId || !patientId.trim()) {
      setError("أدخل رقم المريض الوطني ورقم المؤسسة الحكومية.");
      return;
    }
    setBusyId("arrival");
    setError("");
    setMessage("");
    const id = operationId();
    const payload = {
      patient_id: patientId.trim(),
      hospital_id: hospitalId,
      priority,
      is_emergency: priority === "stat",
    };
    try {
      let completed = false;
      if (!navigator.onLine) {
        completed = await queueLocally({ operation_id: id, idempotency_key: id, operation_type: "encounter.arrival", entity_type: "Encounter", priority: priority === "stat" ? "critical" : priority, payload, device_id: deviceId(), created_at: new Date().toISOString() }, "تم تسجيل الوصول محليًا.");
      } else {
        await patientFlowApi.createArrival({ ...payload, idempotency_key: id });
        setMessage("تم تسجيل الوصول مركزيًا دون إنشاء سجل مكرر.");
        await refresh();
        completed = true;
      }
      if (completed) {
        setPatientId("");
        setPriority("routine");
      }
    } catch {
      if (!navigator.onLine) {
        await queueLocally({ operation_id: id, idempotency_key: id, operation_type: "encounter.arrival", entity_type: "Encounter", priority: priority === "stat" ? "critical" : priority, payload, device_id: deviceId(), created_at: new Date().toISOString() }, "تعذر الاتصال؛ تم تحويل العملية إلى الطابور المحلي.");
      } else {
        setError("لم يتم تسجيل الوصول. راجع هوية المريض أو اطلب من المشرف معالجة التعارض.");
      }
    } finally {
      setBusyId(null);
    }
  };

  const advance = async (entry: PatientFlowRecord) => {
    const target = NEXT_STATE[entry.flow_state];
    if (!target) return;
    setBusyId(entry.id);
    setError("");
    try {
      if (!navigator.onLine) {
        const id = operationId();
        await queueLocally({ operation_id: id, idempotency_key: id, operation_type: "encounter.transition", entity_type: "Encounter", entity_id: entry.id, base_version: entry.version, priority: entry.is_emergency ? "critical" : entry.priority || "routine", payload: { target_state: target, hospital_id: hospitalId }, device_id: deviceId(), created_at: new Date().toISOString() }, `تم حفظ انتقال ${STATE_LABEL[target]} محليًا.`);
      } else {
        await patientFlowApi.transition(entry.id, { target_state: target, expected_version: entry.version });
        setMessage(`تم نقل الحالة إلى: ${STATE_LABEL[target]}.`);
        await refresh();
      }
    } catch {
      setError("رُفض الانتقال لأن الحالة تغيّرت أو أن الانتقال غير مسموح. حدّث الطابور قبل المحاولة.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="مسار المريض السريع" description="وصول واحد، طابور موحد، ومزامنة آمنة عند انقطاع الشبكة." />
      <Card className={online ? "border-emerald-200 bg-emerald-50/60 dark:border-emerald-900/50 dark:bg-emerald-950/20" : "border-amber-300 bg-amber-50 dark:border-amber-900/60 dark:bg-amber-950/20"}>
        <CardContent className="p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">{online ? <Wifi className="h-5 w-5 text-emerald-600" /> : <CloudOff className="h-5 w-5 text-amber-600" />}<div><p className="font-semibold">{online ? "متصل — المزامنة فعالة" : "غير متصل — العمل المحلي فعال"}</p><p className="text-sm text-muted-foreground">الحالات النشطة: {activeCount} · عمليات محلية: {offlineQueue.length} · تعارضات حرجة: {criticalNotifications}</p></div></div>
            <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-emerald-600" /><span className="text-xs text-muted-foreground">لا تعتبر العملية معتمدة حتى يؤكدها الخادم</span><Button variant="outline" size="sm" onClick={() => void flushOfflineQueue()} disabled={!online || offlineQueue.length === 0}><CloudUpload className="h-4 w-4" />مزامنة</Button></div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[minmax(300px,0.7fr)_minmax(0,1.3fr)]">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Plus className="h-4 w-4" />تسجيل وصول مختصر</CardTitle></CardHeader>
          <CardContent><form className="space-y-4" onSubmit={registerArrival}>
            <label className="block space-y-1.5 text-sm"><span className="font-medium">رقم المؤسسة الحكومية</span><Input type="number" min={1} value={hospitalId || ""} onChange={(event) => { const value = Number(event.target.value); setHospitalId(value); window.localStorage.setItem("gula.activeHospitalId", String(value)); }} placeholder="مثال: 12" /></label>
            <label className="block space-y-1.5 text-sm"><span className="font-medium">رقم المريض الوطني</span><Input value={patientId} onChange={(event) => setPatientId(event.target.value)} placeholder="أدخل المعرف الوطني فقط" autoFocus /></label>
            <label className="block space-y-1.5 text-sm"><span className="font-medium">الأولوية</span><select value={priority} onChange={(event) => setPriority(event.target.value)} className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"><option value="routine">عادية</option><option value="urgent">عاجلة</option><option value="asap">سريعة</option><option value="stat">حرجة</option></select></label>
            <Button type="submit" className="w-full" disabled={busyId === "arrival"}>{busyId === "arrival" ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}تسجيل الوصول</Button>
            <p className="text-xs leading-6 text-muted-foreground">في Offline تُحفظ العملية في IndexedDB على الجهاز وفق سياسة الجهاز، وتظهر بوضوح كعملية بانتظار المزامنة؛ لا تعتبر معتمدة قبل تأكيد الخادم.</p>
          </form></CardContent>
        </Card>

        <Card>
          <CardHeader><div className="flex items-center justify-between gap-3"><CardTitle className="flex items-center gap-2 text-base"><Clock3 className="h-4 w-4" />الطابور الموحد</CardTitle><Button variant="outline" size="sm" onClick={() => void refresh()} disabled={loading || !online}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}تحديث</Button></div></CardHeader>
          <CardContent className="space-y-3">
            {offlineQueue.length > 0 && <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200"><AlertTriangle className="me-2 inline h-4 w-4" />توجد {offlineQueue.length} عمليات محلية؛ لا تغلق الجهاز قبل عودة الاتصال والمزامنة.</div>}
            {queue.length === 0 && <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">لا توجد حالات مركزية نشطة. في Offline راجع العمليات المحلية أعلى الشاشة.</div>}
            {queue.map((entry, index) => <div key={entry.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">{index + 1}</span><div><p className="font-semibold">{entry.patient_id}</p><p className="mt-1 text-xs text-muted-foreground">{entry.is_emergency ? "أولوية حرجة" : "أولوية " + (entry.priority || "عادية")} · {entry.id}</p></div></div><div className="flex items-center gap-2"><Badge variant={entry.is_emergency ? "warning" : "outline"}>{STATE_LABEL[entry.flow_state] || entry.flow_state}</Badge>{NEXT_STATE[entry.flow_state] && <Button size="sm" onClick={() => void advance(entry)} disabled={busyId === entry.id}>{busyId === entry.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowLeft className="h-4 w-4" />}التالي</Button>}</div></div>)}
          </CardContent>
        </Card>
      </div>

      {(message || error) && <div className={`rounded-lg border px-4 py-3 text-sm ${error ? "border-red-200 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300" : "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300"}`} role="status">{error || message}</div>}
    </div>
  );
}
