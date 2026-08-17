/**
 * تصميم الصفحة: لوحة سريرية عربية هادئة ذات تسلسل زمني واضح للجرعات، مع لون
 * كهرماني للحالات المتأخرة وأخضر للإعطاء المكتمل، وتجنّب عرض بيانات تعريفية أكثر من اللازم.
 */
import { type FormEvent, type ReactNode, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Dialog, Input } from "@/components/ui";
import { EmptyState, PageHeader } from "@/components/shared/PageComponents";
import { toast } from "@/hooks/useToast";
import { AlertTriangle, BellRing, CalendarClock, CheckCircle2, ShieldCheck, Syringe } from "lucide-react";

type ScheduleStatus = "scheduled" | "administered" | "overdue" | "refused" | "contraindicated" | "partial" | "complete";

type ScheduleItem = {
  id: string;
  patient_id: string;
  health_number: string;
  newborn_id?: string;
  schedule_version: string;
  vaccine: string;
  vaccine_code: string;
  dose_number: number;
  total_doses: number;
  due_date: string;
  scheduled_date?: string;
  status: ScheduleStatus;
  facility_id?: string;
  appointment_id?: string;
  reminder_sent: boolean;
  reminder_count: number;
};

type FollowUpTask = {
  id: string;
  schedule_id: string;
  patient_id: string;
  vaccine: string;
  due_date: string;
  status: "pending" | "queued" | "completed" | "suppressed";
  priority: "low" | "normal" | "high" | "urgent";
  reason?: string;
  next_action_at?: string;
  consent_verified: boolean;
};

type MonthlyStats = {
  scheduled_doses: number;
  administered_doses: number;
  overdue_doses: number;
  delivery_rate_pct: number;
  administered_by_vaccine: Record<string, number>;
};

const statusLabel: Record<ScheduleStatus, string> = {
  scheduled: "مجدولة",
  administered: "أُعطيت",
  overdue: "متأخرة",
  refused: "مرفوضة",
  contraindicated: "مانع طبي",
  partial: "جزئي",
  complete: "مكتمل",
};

const statusVariant: Record<ScheduleStatus, "default" | "success" | "warning" | "destructive"> = {
  scheduled: "default", administered: "success", overdue: "warning", refused: "destructive",
  contraindicated: "destructive", partial: "default", complete: "success",
};

function toLocalDateTimeInput(value: Date) {
  const offset = value.getTimezoneOffset() * 60_000;
  return new Date(value.getTime() - offset).toISOString().slice(0, 16);
}

function toIso(value: string) {
  return value ? new Date(value).toISOString() : undefined;
}

function formatDate(value?: string) {
  if (!value) return "غير محدد";
  return new Intl.DateTimeFormat("ar-IQ", { dateStyle: "medium" }).format(new Date(value));
}

export function ImmunizationProgramPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [patientId, setPatientId] = useState("");
  const [activePatientId, setActivePatientId] = useState("");
  const [healthNumber, setHealthNumber] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [scheduleVersion, setScheduleVersion] = useState("");
  const [selectedMonth, setSelectedMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [appointmentTarget, setAppointmentTarget] = useState<ScheduleItem | null>(null);
  const [appointmentAt, setAppointmentAt] = useState(() => toLocalDateTimeInput(new Date()));
  const [administrationTarget, setAdministrationTarget] = useState<ScheduleItem | null>(null);
  const [administrationAt, setAdministrationAt] = useState(() => toLocalDateTimeInput(new Date()));
  const [lotNumber, setLotNumber] = useState("");
  const [batchNumber, setBatchNumber] = useState("");
  const [manufacturer, setManufacturer] = useState("");
  const [consentObtained, setConsentObtained] = useState(true);

  const canSchedule = ["master_admin", "admin", "lab_admin", "doctor", "staff"].includes(user?.role ?? "");
  const canAdminister = ["master_admin", "admin", "lab_admin", "doctor", "staff", "midwife"].includes(user?.role ?? "");
  const canViewReports = ["master_admin", "ministry_admin", "province_admin", "admin", "lab_admin"].includes(user?.role ?? "");
  const [year, month] = selectedMonth.split("-").map(Number);

  const patientSchedule = useQuery({
    queryKey: ["immunization", "patient-schedule", activePatientId],
    queryFn: () => api.get(`/public-health/vaccinations/${encodeURIComponent(activePatientId)}/schedule`).then((response) => response.data as ScheduleItem[]),
    enabled: Boolean(activePatientId),
  });
  const overdue = useQuery({
    queryKey: ["immunization", "overdue"],
    queryFn: () => api.get("/public-health/vaccinations/overdue").then((response) => response.data as ScheduleItem[]),
  });
  const followUpTasks = useQuery({
    queryKey: ["immunization", "follow-up-tasks"],
    queryFn: () => api.get("/public-health/vaccinations/follow-up/tasks", { params: { status: "pending", limit: 25 } }).then((response) => response.data as FollowUpTask[]),
  });
  const monthlyStats = useQuery({
    queryKey: ["immunization", "monthly-statistics", year, month],
    queryFn: () => api.get("/public-health/vaccinations/statistics/monthly", { params: { year, month } }).then((response) => response.data as MonthlyStats),
    enabled: canViewReports && Number.isFinite(year) && Number.isFinite(month),
  });

  const refreshProgramme = () => {
    void queryClient.invalidateQueries({ queryKey: ["immunization"] });
  };

  const generateSchedule = useMutation({
    mutationFn: () => api.post("/public-health/vaccinations/schedule", {
      patient_id: patientId,
      health_number: healthNumber,
      date_of_birth: dateOfBirth,
      schedule_version: scheduleVersion,
    }).then((response) => response.data as ScheduleItem[]),
    onSuccess: () => {
      setActivePatientId(patientId);
      refreshProgramme();
      toast({ variant: "success", title: "تم إنشاء الجدول", description: "أضيفت الجرعات من النسخة المرجعية المعتمدة للمنشأة." });
    },
    onError: () => toast({ variant: "destructive", title: "تعذر إنشاء الجدول", description: "تحقق من رقم السجل الصحي ونسخة الجدول المرجعي المعتمدة." }),
  });

  const setAppointment = useMutation({
    mutationFn: ({ scheduleId, scheduledDate }: { scheduleId: string; scheduledDate: string }) => api.post(
      `/public-health/vaccinations/schedule/${encodeURIComponent(scheduleId)}/appointment`,
      { scheduled_date: toIso(scheduledDate) },
    ).then((response) => response.data as ScheduleItem),
    onSuccess: () => {
      setAppointmentTarget(null);
      refreshProgramme();
      toast({ variant: "success", title: "تم حفظ الموعد" });
    },
    onError: () => toast({ variant: "destructive", title: "تعذر حفظ الموعد" }),
  });

  const administerVaccine = useMutation({
    mutationFn: ({ scheduleId, administeredAt }: { scheduleId: string; administeredAt: string }) => api.post(
      `/public-health/vaccinations/schedule/${encodeURIComponent(scheduleId)}/administer`,
      {
        administration_date: toIso(administeredAt),
        lot_number: lotNumber || undefined,
        batch_number: batchNumber || undefined,
        manufacturer: manufacturer || undefined,
        consent_obtained: consentObtained,
      },
    ).then((response) => response.data),
    onSuccess: () => {
      setAdministrationTarget(null);
      setLotNumber(""); setBatchNumber(""); setManufacturer(""); setConsentObtained(true);
      refreshProgramme();
      toast({ variant: "success", title: "تم توثيق إعطاء الجرعة" });
    },
    onError: () => toast({ variant: "destructive", title: "تعذر توثيق الجرعة", description: "راجع حالة الجرعة وبيانات الدفعة قبل إعادة المحاولة." }),
  });

  const queueReminder = useMutation({
    mutationFn: (scheduleId: string) => api.post(`/public-health/vaccinations/schedule/${encodeURIComponent(scheduleId)}/reminder`).then((response) => response.data as ScheduleItem),
    onSuccess: () => { refreshProgramme(); toast({ variant: "success", title: "وُضع التذكير في طابور الإشعارات" }); },
    onError: () => toast({ variant: "destructive", title: "تعذر وضع التذكير في الطابور" }),
  });
  const completeFollowUp = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: "completed" | "suppressed" }) => api.patch(`/public-health/vaccinations/follow-up/tasks/${encodeURIComponent(taskId)}`, { status }),
    onSuccess: () => { refreshProgramme(); toast({ variant: "success", title: "تم تحديث مهمة المتابعة" }); },
    onError: () => toast({ variant: "destructive", title: "تعذر تحديث مهمة المتابعة" }),
  });

  const schedule = patientSchedule.data ?? [];
  const summary = useMemo(() => ({
    total: schedule.length,
    complete: schedule.filter((item) => item.status === "complete" || item.status === "administered").length,
    overdue: schedule.filter((item) => item.status === "overdue").length,
  }), [schedule]);

  const submitSchedule = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    generateSchedule.mutate();
  };

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="برنامج التحصين" description="متابعة الجدول المرجعي المعتمد، المواعيد، سجل الإعطاء، والجرعات المتأخرة ضمن الرعاية الصحية الأولية." />

      <section className="grid gap-4 md:grid-cols-3" aria-label="ملخص برنامج التحصين">
        <Metric icon={Syringe} label="جرعات جدول المراجع" value={activePatientId ? String(summary.total) : "—"} hint={activePatientId ? "للطفل المختار" : "اختر سجل طفل للمتابعة"} tone="sky" />
        <Metric icon={CheckCircle2} label="جرعات موثقة" value={activePatientId ? String(summary.complete) : "—"} hint="من جدول الطفل" tone="emerald" />
        <Metric icon={AlertTriangle} label="جرعات متأخرة" value={String(overdue.data?.length ?? 0)} hint="داخل المنشأة" tone="amber" />
      </section>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-5">
          {canSchedule ? (
            <Card className="border-sky-100 bg-gradient-to-bl from-sky-50/70 to-background shadow-sm">
              <CardHeader className="flex-row items-start gap-3 space-y-0">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-sky-700 text-white"><CalendarClock className="h-5 w-5" aria-hidden="true" /></div>
                <div><CardTitle className="text-lg">إنشاء جدول الطفل</CardTitle><p className="mt-1 text-sm text-muted-foreground">يُولد الجدول من نسخة مرجعية معتمدة ومهيأة مسبقاً للمنشأة، وليس من جدول مكتوب داخل الواجهة.</p></div>
              </CardHeader>
              <CardContent>
                <form onSubmit={submitSchedule} className="grid gap-4 md:grid-cols-2">
                  <ProgrammeField label="معرّف سجل الطفل" required htmlFor="patient_id"><Input id="patient_id" value={patientId} onChange={(event) => setPatientId(event.target.value)} required autoComplete="off" /></ProgrammeField>
                  <ProgrammeField label="الرقم الصحي" required htmlFor="health_number"><Input id="health_number" value={healthNumber} onChange={(event) => setHealthNumber(event.target.value)} required autoComplete="off" /></ProgrammeField>
                  <ProgrammeField label="تاريخ الولادة" required htmlFor="date_of_birth"><Input id="date_of_birth" type="date" value={dateOfBirth} onChange={(event) => setDateOfBirth(event.target.value)} required /></ProgrammeField>
                  <ProgrammeField label="نسخة الجدول المعتمدة" required htmlFor="schedule_version"><Input id="schedule_version" value={scheduleVersion} onChange={(event) => setScheduleVersion(event.target.value)} required maxLength={40} placeholder="مثال: MOH-EPI-2026" autoComplete="off" /></ProgrammeField>
                  <div className="md:col-span-2 flex justify-end"><Button type="submit" loading={generateSchedule.isPending} className="bg-sky-700 hover:bg-sky-800">إنشاء أو استعادة جدول الطفل</Button></div>
                </form>
              </CardContent>
            </Card>
          ) : null}

          <Card className="shadow-sm">
            <CardHeader className="flex-row items-center justify-between gap-3 space-y-0">
              <div><CardTitle className="text-lg">جدول الطفل</CardTitle><p className="mt-1 text-sm text-muted-foreground">أدخل معرّف السجل لعرض الجرعات والحالة الحالية.</p></div>
              <div className="flex items-center gap-2"><Input aria-label="معرّف سجل الطفل لعرض الجدول" value={activePatientId || patientId} onChange={(event) => setPatientId(event.target.value)} className="w-44" autoComplete="off" /><Button variant="outline" onClick={() => setActivePatientId(patientId)} disabled={!patientId}>عرض</Button></div>
            </CardHeader>
            <CardContent>
              {patientSchedule.isLoading ? <p className="py-10 text-center text-sm text-muted-foreground">يجري تحميل الجدول…</p> : null}
              {!patientSchedule.isLoading && activePatientId && schedule.length === 0 ? <EmptyState title="لا توجد جرعات مجدولة" description="أنشئ جدولاً من نسخة معتمدة أو تحقق من معرّف سجل الطفل." /> : null}
              {!activePatientId ? <EmptyState title="لم يُحدد سجل طفل بعد" description="استخدم الرقم الصحي لإنشاء جدول أو اكتب معرّف السجل لعرضه." /> : null}
              {schedule.length > 0 ? <div className="relative space-y-0 before:absolute before:bottom-5 before:right-5 before:top-5 before:w-px before:bg-border">{schedule.map((item) => <ScheduleRow key={item.id} item={item} canSchedule={canSchedule} canAdminister={canAdminister} onAppointment={() => { setAppointmentTarget(item); setAppointmentAt(toLocalDateTimeInput(new Date())); }} onAdminister={() => { setAdministrationTarget(item); setAdministrationAt(toLocalDateTimeInput(new Date())); }} onReminder={() => queueReminder.mutate(item.id)} isReminderPending={queueReminder.isPending} />)}</div> : null}
            </CardContent>
          </Card>
        </div>

        <aside className="space-y-5 xl:sticky xl:top-6 xl:self-start">
          <Card className="border-amber-100 bg-amber-50/40 shadow-sm">
            <CardContent className="p-5"><AlertTriangle className="h-5 w-5 text-amber-800" aria-hidden="true" /><h2 className="mt-3 font-semibold text-amber-950">الجرعات المتأخرة</h2><p className="mt-1 text-sm text-amber-900/75">تتحول الحالة إلى متأخرة وفق تاريخ الاستحقاق. التذكير هنا يُوضع في طابور الإشعارات ولا يُرسل رقماً أو عنواناً من هذه الواجهة.</p><div className="mt-4 space-y-2">{(overdue.data ?? []).slice(0, 5).map((item) => <div key={item.id} className="rounded-lg border border-amber-200 bg-white/80 p-3"><div className="flex items-center justify-between gap-2"><span className="font-medium text-sm">{item.vaccine}</span><Badge variant="warning">متأخرة</Badge></div><p className="mt-1 text-xs text-muted-foreground">الاستحقاق: {formatDate(item.due_date)}</p></div>)}{!overdue.isLoading && overdue.data?.length === 0 ? <p className="rounded-lg border border-dashed border-amber-200 bg-white/70 p-3 text-sm text-amber-900/70">لا توجد جرعات متأخرة ظاهرة للمنشأة.</p> : null}</div></CardContent>
                    </Card>

          <Card className="border-slate-200 bg-slate-50/70 shadow-sm">
            <CardHeader><CardTitle className="text-base">مهام المتابعة</CardTitle><p className="text-sm text-muted-foreground">قائمة عمل داخلية للجرعات التي تحتاج متابعة؛ لا تعرض أرقام هواتف أو عناوين.</p></CardHeader>
            <CardContent className="space-y-2">
              {(followUpTasks.data ?? []).slice(0, 6).map((task) => (
                <div key={task.id} className="rounded-lg border bg-background p-3">
                  <div className="flex items-center justify-between gap-2"><span className="text-sm font-medium">{task.vaccine}</span><Badge variant={task.priority === "high" || task.priority === "urgent" ? "warning" : "default"}>{task.priority === "urgent" ? "عاجلة" : task.priority === "high" ? "أولوية عالية" : "للمتابعة"}</Badge></div>
                  <p className="mt-1 text-xs text-muted-foreground">الاستحقاق: {formatDate(task.due_date)} · السبب: {task.reason || "متابعة"}</p>
                  <div className="mt-2 flex justify-end"><Button size="sm" variant="outline" disabled={completeFollowUp.isPending} onClick={() => completeFollowUp.mutate({ taskId: task.id, status: "completed" })}>إغلاق المهمة</Button></div>
                </div>
              ))}
              {!followUpTasks.isLoading && followUpTasks.data?.length === 0 ? <p className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">لا توجد مهام متابعة مفتوحة.</p> : null}
            </CardContent>
          </Card>

          {canViewReports ? <Card className="shadow-sm"><CardHeader><CardTitle className="text-base">مؤشرات الشهر</CardTitle><Input aria-label="شهر الإحصاءات" type="month" value={selectedMonth} onChange={(event) => setSelectedMonth(event.target.value)} /></CardHeader><CardContent className="space-y-3">{monthlyStats.isLoading ? <p className="text-sm text-muted-foreground">يجري تحميل المؤشرات…</p> : <><StatLine label="الجرعات المجدولة" value={monthlyStats.data?.scheduled_doses ?? 0} /><StatLine label="الجرعات الموثقة" value={monthlyStats.data?.administered_doses ?? 0} /><StatLine label="المتأخرة" value={monthlyStats.data?.overdue_doses ?? 0} emphasis="amber" /><div className="border-t pt-3"><p className="text-xs text-muted-foreground">معدل التنفيذ من الجرعات المجدولة</p><p className="mt-1 text-2xl font-semibold">{monthlyStats.data?.delivery_rate_pct ?? 0}%</p></div></>}</CardContent></Card> : null}

          <Card className="shadow-sm"><CardContent className="p-5"><ShieldCheck className="h-5 w-5 text-emerald-700" aria-hidden="true" /><h2 className="mt-3 font-semibold">ضبط الجودة</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">لا يُتاح جدول جرعات افتراضي في الكود. يجب أن يوافق مسؤول مخول على نسخة الجدول ومصدرها قبل إنشاء جداول المرضى.</p></CardContent></Card>
        </aside>
      </div>

      <Dialog open={Boolean(appointmentTarget)} onClose={() => setAppointmentTarget(null)} title="تحديد موعد الجرعة" description={appointmentTarget ? `${appointmentTarget.vaccine} — الجرعة ${appointmentTarget.dose_number}` : undefined} footer={<><Button variant="outline" onClick={() => setAppointmentTarget(null)}>إلغاء</Button><Button disabled={!appointmentTarget} loading={setAppointment.isPending} onClick={() => appointmentTarget && setAppointment.mutate({ scheduleId: appointmentTarget.id, scheduledDate: appointmentAt })}>حفظ الموعد</Button></>}>
        <ProgrammeField label="التاريخ والوقت" required htmlFor="appointment_at"><Input id="appointment_at" type="datetime-local" value={appointmentAt} onChange={(event) => setAppointmentAt(event.target.value)} required /></ProgrammeField>
      </Dialog>

      <Dialog open={Boolean(administrationTarget)} onClose={() => setAdministrationTarget(null)} title="توثيق إعطاء الجرعة" description="راجع الموافقة والدفعة قبل الحفظ." footer={<><Button variant="outline" onClick={() => setAdministrationTarget(null)}>إلغاء</Button><Button disabled={!administrationTarget || !consentObtained} loading={administerVaccine.isPending} onClick={() => administrationTarget && administerVaccine.mutate({ scheduleId: administrationTarget.id, administeredAt: administrationAt })} className="bg-emerald-700 hover:bg-emerald-800">تأكيد الإعطاء</Button></>}>
        <div className="space-y-4"><ProgrammeField label="تاريخ ووقت الإعطاء" required htmlFor="administration_at"><Input id="administration_at" type="datetime-local" value={administrationAt} onChange={(event) => setAdministrationAt(event.target.value)} required /></ProgrammeField><ProgrammeField label="رقم التشغيلة" htmlFor="batch_number"><Input id="batch_number" value={batchNumber} onChange={(event) => setBatchNumber(event.target.value)} maxLength={100} autoComplete="off" /></ProgrammeField><ProgrammeField label="رقم اللوت" htmlFor="lot_number"><Input id="lot_number" value={lotNumber} onChange={(event) => setLotNumber(event.target.value)} maxLength={100} autoComplete="off" /></ProgrammeField><ProgrammeField label="الشركة المصنعة" htmlFor="manufacturer"><Input id="manufacturer" value={manufacturer} onChange={(event) => setManufacturer(event.target.value)} maxLength={200} autoComplete="off" /></ProgrammeField><label className="flex items-start gap-3 rounded-lg border p-3 text-sm"><input type="checkbox" checked={consentObtained} onChange={(event) => setConsentObtained(event.target.checked)} className="mt-1 h-4 w-4" /><span>تم التحقق من الموافقة المطلوبة قبل إعطاء الجرعة.</span></label></div>
      </Dialog>
    </div>
  );
}

function Metric({ icon: Icon, label, value, hint, tone }: { icon: typeof Syringe; label: string; value: string; hint: string; tone: "sky" | "emerald" | "amber" }) {
  const tones = { sky: "border-sky-100 bg-sky-50/50 text-sky-800", emerald: "border-emerald-100 bg-emerald-50/50 text-emerald-800", amber: "border-amber-100 bg-amber-50/50 text-amber-800" };
  return <Card className={`shadow-sm ${tones[tone]}`}><CardContent className="flex items-center gap-3 p-5"><div className="rounded-xl bg-white/80 p-2 shadow-sm"><Icon className="h-5 w-5" aria-hidden="true" /></div><div><p className="text-sm font-medium">{label}</p><p className="mt-1 text-2xl font-semibold">{value}</p><p className="text-xs opacity-75">{hint}</p></div></CardContent></Card>;
}

function ScheduleRow({ item, canSchedule, canAdminister, onAppointment, onAdminister, onReminder, isReminderPending }: { item: ScheduleItem; canSchedule: boolean; canAdminister: boolean; onAppointment: () => void; onAdminister: () => void; onReminder: () => void; isReminderPending: boolean }) {
  const canAdministerDose = canAdminister && !["complete", "administered", "refused", "contraindicated"].includes(item.status);
  const canRemind = ["scheduled", "overdue"].includes(item.status);
  return <article className="relative mr-10 border-b py-5 last:border-b-0"><span className={`absolute -right-[2.88rem] top-7 h-3 w-3 rounded-full ring-4 ring-background ${item.status === "overdue" ? "bg-amber-500" : item.status === "complete" || item.status === "administered" ? "bg-emerald-600" : "bg-sky-600"}`} aria-hidden="true" /><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold">{item.vaccine}</h3><Badge variant={statusVariant[item.status]}>{statusLabel[item.status]}</Badge><span className="text-xs text-muted-foreground">جرعة {item.dose_number}/{item.total_doses}</span></div><p className="mt-1 text-sm text-muted-foreground">الاستحقاق: {formatDate(item.due_date)}{item.scheduled_date ? ` · الموعد: ${formatDate(item.scheduled_date)}` : ""}</p></div><div className="flex flex-wrap gap-2">{canSchedule && canAdministerDose ? <Button size="sm" variant="outline" onClick={onAppointment}><CalendarClock className="ms-1 h-4 w-4" />موعد</Button> : null}{canAdministerDose ? <Button size="sm" onClick={onAdminister} className="bg-emerald-700 hover:bg-emerald-800"><Syringe className="ms-1 h-4 w-4" />توثيق الإعطاء</Button> : null}{canSchedule && canRemind ? <Button size="sm" variant="ghost" disabled={isReminderPending} onClick={onReminder} aria-label={`وضع تذكير لجرعة ${item.vaccine} في الطابور`}><BellRing className="h-4 w-4" /></Button> : null}</div></div></article>;
}

function ProgrammeField({ label, required = false, htmlFor, children }: { label: string; required?: boolean; htmlFor: string; children: ReactNode }) {
  return <label htmlFor={htmlFor} className="grid gap-2 text-sm font-medium">{label}{required ? <span className="me-1 text-destructive" aria-hidden="true">*</span> : null}{children}</label>;
}

function StatLine({ label, value, emphasis }: { label: string; value: number; emphasis?: "amber" }) {
  return <div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">{label}</span><span className={emphasis ? "font-semibold text-amber-700" : "font-semibold"}>{value}</span></div>;
}
