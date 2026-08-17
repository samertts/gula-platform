import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Activity, ArrowLeft, CheckCircle2, Clock3, Loader2, Plus, RefreshCw, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { patientFlowApi, type PatientFlowRecord } from "@/api/endpoints";

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

export default function RapidPatientFlowPage() {
  const [hospitalId, setHospitalId] = useState(activeHospitalId);
  const [patientId, setPatientId] = useState("");
  const [priority, setPriority] = useState("routine");
  const [queue, setQueue] = useState<PatientFlowRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    if (!hospitalId) return;
    setLoading(true);
    setError("");
    try {
      setQueue(await patientFlowApi.queue(hospitalId, { limit: 200 }));
    } catch {
      setError("تعذر تحميل الطابور. تحقق من الصلاحية والاتصال ثم أعد المحاولة.");
    } finally {
      setLoading(false);
    }
  }, [hospitalId]);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 15000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const activeCount = useMemo(() => queue.filter((entry) => !["discharged", "cancelled"].includes(entry.flow_state)).length, [queue]);

  const registerArrival = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!hospitalId || !patientId.trim()) {
      setError("أدخل رقم المريض الوطني ورقم المؤسسة الحكومية.");
      return;
    }
    setBusyId("arrival");
    setError("");
    setMessage("");
    try {
      await patientFlowApi.createArrival({
        patient_id: patientId.trim(),
        hospital_id: hospitalId,
        priority,
        is_emergency: priority === "stat",
        idempotency_key: crypto.randomUUID(),
      });
      setPatientId("");
      setPriority("routine");
      setMessage("تم تسجيل الوصول ووضع المريض في الطابور دون إنشاء سجل مكرر.");
      await refresh();
    } catch {
      setError("لم يتم تسجيل الوصول. راجع هوية المريض ورقم المؤسسة أو اطلب من المشرف معالجة التعارض.");
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
      await patientFlowApi.transition(entry.id, { target_state: target, expected_version: entry.version });
      setMessage(`تم نقل الحالة إلى: ${STATE_LABEL[target]}.`);
      await refresh();
    } catch {
      setError("رُفض الانتقال لأن الحالة تغيّرت أو أن الانتقال غير مسموح. حدّث الطابور قبل المحاولة.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader
        title="مسار المريض السريع"
        description="وصول واحد، طابور موحد، وانتقالات خادمية محمية من التكرار والتعارض."
      />

      <Card className="border-emerald-200 bg-gradient-to-l from-emerald-50 via-white to-indigo-50 dark:border-emerald-900/50 dark:from-emerald-950/30 dark:via-background dark:to-indigo-950/30">
        <CardContent className="p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3"><Activity className="h-5 w-5 text-emerald-600" /><div><p className="font-semibold">لوحة التشغيل اليومية</p><p className="text-sm text-muted-foreground">الحالات النشطة: {activeCount} · التحديث تلقائي كل 15 ثانية</p></div></div>
            <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-emerald-600" /><span className="text-xs text-muted-foreground">التحقق والتدقيق على الخادم</span></div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[minmax(300px,0.7fr)_minmax(0,1.3fr)]">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Plus className="h-4 w-4" />تسجيل وصول مختصر</CardTitle></CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={registerArrival}>
              <label className="block space-y-1.5 text-sm"><span className="font-medium">رقم المؤسسة الحكومية</span><Input type="number" min={1} value={hospitalId || ""} onChange={(event) => { const value = Number(event.target.value); setHospitalId(value); window.localStorage.setItem("gula.activeHospitalId", String(value)); }} placeholder="مثال: 12" /></label>
              <label className="block space-y-1.5 text-sm"><span className="font-medium">رقم المريض الوطني</span><Input value={patientId} onChange={(event) => setPatientId(event.target.value)} placeholder="أدخل المعرف الوطني فقط" autoFocus /></label>
              <label className="block space-y-1.5 text-sm"><span className="font-medium">الأولوية</span><select value={priority} onChange={(event) => setPriority(event.target.value)} className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"><option value="routine">عادية</option><option value="urgent">عاجلة</option><option value="asap">سريعة</option><option value="stat">حرجة</option></select></label>
              <Button type="submit" className="w-full" disabled={busyId === "arrival"}>{busyId === "arrival" ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}تسجيل الوصول وإدخاله للطابور</Button>
              <p className="text-xs leading-6 text-muted-foreground">لا يتم إنشاء مريض جديد من هذه الشاشة؛ التسجيل يعتمد على هوية وطنية موجودة، ويُرفض الطلب إذا كانت الهوية غير فعالة.</p>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><div className="flex items-center justify-between gap-3"><CardTitle className="flex items-center gap-2 text-base"><Clock3 className="h-4 w-4" />الطابور الموحد</CardTitle><Button variant="outline" size="sm" onClick={() => void refresh()} disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}تحديث</Button></div></CardHeader>
          <CardContent className="space-y-3">
            {queue.length === 0 && <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">لا توجد حالات نشطة في هذه المؤسسة.</div>}
            {queue.map((entry, index) => <div key={entry.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">{index + 1}</span><div><p className="font-semibold">{entry.patient_id}</p><p className="mt-1 text-xs text-muted-foreground">{entry.is_emergency ? "أولوية حرجة" : "أولوية " + (entry.priority || "عادية")} · {entry.id}</p></div></div><div className="flex items-center gap-2"><Badge variant={entry.is_emergency ? "warning" : "outline"}>{STATE_LABEL[entry.flow_state] || entry.flow_state}</Badge>{NEXT_STATE[entry.flow_state] && <Button size="sm" onClick={() => void advance(entry)} disabled={busyId === entry.id}>{busyId === entry.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowLeft className="h-4 w-4" />}التالي</Button>}</div></div>)}
          </CardContent>
        </Card>
      </div>

      {(message || error) && <div className={`rounded-lg border px-4 py-3 text-sm ${error ? "border-red-200 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300" : "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300"}`} role="status">{error || message}</div>}
    </div>
  );
}
