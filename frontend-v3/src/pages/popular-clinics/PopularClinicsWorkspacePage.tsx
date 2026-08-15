import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, BookOpen, CreditCard, FileBarChart2, HeartPulse, RefreshCw, Search, ShieldCheck, Users } from "lucide-react";
import { popularClinicsApi } from "@/api/endpoints";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { PageHeader } from "@/components/shared/PageComponents";
import type {
  PopularClinicBookletMonth,
  PopularClinicPatient,
  PopularClinicPatientCard,
  PopularClinicTicket,
} from "@/types";

function money(value: string | number | null | undefined): string {
  return `${Number(value ?? 0).toLocaleString("ar-IQ")} د.ع`;
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "تعذر تحميل البيانات من الخادم.";
}

function Metric({ label, value, icon: Icon }: { label: string; value: string | number; icon: typeof Activity }) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-3 p-5">
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="mt-1 text-xl font-bold text-foreground">{value}</p>
        </div>
        <Icon className="h-5 w-5 text-[#0D9488]" aria-hidden="true" />
      </CardContent>
    </Card>
  );
}

function LoadState({ loading, error, onRetry }: { loading: boolean; error?: unknown; onRetry?: () => void }) {
  if (loading) return <p className="rounded-xl bg-muted/60 p-4 text-sm text-muted-foreground" role="status">جارٍ تحميل البيانات الحكومية من الخادم…</p>;
  if (!error) return null;
  return (
    <div className="flex items-start justify-between gap-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-900 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-100" role="alert">
      <p>{errorText(error)}</p>
      {onRetry && <Button variant="outline" size="sm" onClick={onRetry}><RefreshCw aria-hidden="true" />إعادة المحاولة</Button>}
    </div>
  );
}

function Booklet({ months }: { months: PopularClinicBookletMonth[] }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3" aria-label="دفتر الصرف الشهري">
      {months.map((item) => (
        <article key={item.month} className="rounded-xl border bg-card p-3">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold">الشهر {item.month}</h3>
            <Badge variant={item.dispensation ? "success" : "outline"}>{item.dispensation ? "تم الصرف" : "لم يُصرف"}</Badge>
          </div>
          {item.dispensation ? (
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              {item.dispensation.medication_name} · {item.dispensation.quantity} وحدة · {item.dispensation.dosage}
            </p>
          ) : (
            <p className="mt-2 text-xs text-muted-foreground">لا توجد حصة مسجلة لهذا الشهر.</p>
          )}
        </article>
      ))}
    </div>
  );
}

function PatientCard({ card, booklet }: { card?: PopularClinicPatientCard; booklet?: { months: PopularClinicBookletMonth[] } }) {
  if (!card) return <p className="text-sm text-muted-foreground">اختر مريضاً لعرض البطاقة والدفتر.</p>;
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div><span className="text-xs text-muted-foreground">المريض</span><p className="font-bold">{card.patient.full_name}</p></div>
        <div><span className="text-xs text-muted-foreground">رقم الهاتف</span><p className="font-semibold">{card.patient.phone || "غير مسجل"}</p></div>
        <div><span className="text-xs text-muted-foreground">المعرّف الصحي</span><p className="font-semibold">{card.patient.health_id || "غير مسجل"}</p></div>
        <div><span className="text-xs text-muted-foreground">الأمراض المزمنة</span><p className="font-semibold">{card.conditions.length ? card.conditions.join("، ") : "لا توجد بيانات"}</p></div>
      </div>
      <div className="rounded-xl bg-teal-50/70 p-4 dark:bg-teal-950/20">
        <p className="text-xs font-semibold text-teal-800 dark:text-teal-200">الخطة العلاجية الحالية</p>
        <p className="mt-1 text-sm">{card.treatment_plan ? `${card.treatment_plan.medication_name} · ${card.treatment_plan.quantity} وحدة · ${card.treatment_plan.dosage}` : "لا توجد وصفة فعالة"}</p>
      </div>
      {booklet && <Booklet months={booklet.months} />}
    </div>
  );
}

function TicketTable({ tickets }: { tickets: PopularClinicTicket[] }) {
  if (!tickets.length) return <p className="text-sm text-muted-foreground">لا توجد تذاكر مسجلة ضمن نطاق العيادة.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-right text-sm">
        <caption className="sr-only">آخر تذاكر العيادة الشعبية</caption>
        <thead><tr className="border-b text-xs text-muted-foreground"><th className="p-3">رقم التذكرة</th><th className="p-3">الخدمة</th><th className="p-3">طريقة الدفع</th><th className="p-3">المبلغ</th><th className="p-3">الحالة</th></tr></thead>
        <tbody>{tickets.slice(0, 20).map((ticket) => <tr key={ticket.id} className="border-b last:border-0"><td className="p-3 font-semibold">#{ticket.id}</td><td className="p-3">{ticket.service_code}</td><td className="p-3">{ticket.payment_method === "cash" ? "نقدي" : "إلكتروني"}</td><td className="p-3">{money(ticket.amount)}</td><td className="p-3"><Badge variant={ticket.status === "paid" ? "success" : ticket.status === "cancelled" ? "destructive" : "warning"}>{ticket.status === "paid" ? "مدفوعة" : ticket.status === "cancelled" ? "ملغاة" : "معلقة"}</Badge></td></tr>)}</tbody>
      </table>
    </div>
  );
}

export function PopularClinicsWorkspacePage() {
  const [clinicId, setClinicId] = useState<number>();
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<PopularClinicPatient>();
  const [reportDate] = useState(() => new Date().toISOString().slice(0, 10));
  const clinicsQuery = useQuery({ queryKey: ["popular-clinics", "list"], queryFn: popularClinicsApi.list });
  const clinics = clinicsQuery.data ?? [];

  useEffect(() => {
    if (!clinicId && clinics[0]) setClinicId(clinics[0].id);
  }, [clinicId, clinics]);

  const selectedClinic = useMemo(() => clinics.find((clinic) => clinic.id === clinicId), [clinics, clinicId]);
  const summaryQuery = useQuery({ queryKey: ["popular-clinics", clinicId, "summary"], queryFn: () => popularClinicsApi.summary(clinicId!), enabled: Boolean(clinicId) });
  const patientsQuery = useQuery({ queryKey: ["popular-clinics", clinicId, "patients", patientSearch], queryFn: () => popularClinicsApi.patients(clinicId!, patientSearch || undefined), enabled: Boolean(clinicId) });
  const ticketsQuery = useQuery({ queryKey: ["popular-clinics", clinicId, "tickets"], queryFn: () => popularClinicsApi.tickets(clinicId!), enabled: Boolean(clinicId) });
  const dailyQuery = useQuery({ queryKey: ["popular-clinics", clinicId, "daily", reportDate], queryFn: () => popularClinicsApi.dailyReport(clinicId!, reportDate), enabled: Boolean(clinicId) });
  const monthlyQuery = useQuery({ queryKey: ["popular-clinics", clinicId, "monthly"], queryFn: () => popularClinicsApi.monthlyReport(clinicId!), enabled: Boolean(clinicId) });
  const cardQuery = useQuery({ queryKey: ["popular-clinics", clinicId, "patient-card", selectedPatient?.id], queryFn: () => popularClinicsApi.patientCard(clinicId!, selectedPatient!.id), enabled: Boolean(clinicId && selectedPatient) });
  const bookletQuery = useQuery({ queryKey: ["popular-clinics", clinicId, "booklet", selectedPatient?.id], queryFn: () => popularClinicsApi.booklet(clinicId!, selectedPatient!.id), enabled: Boolean(clinicId && selectedPatient) });
  const firstError = [clinicsQuery, summaryQuery, patientsQuery, ticketsQuery, dailyQuery, monthlyQuery].find((query) => query.isError)?.error;

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="العيادات الطبية الشعبية" description="مساحة العمل الحكومية للأمراض المزمنة، التذاكر، التحصيل والتقارير — البيانات مصدرها الخادم ومقيدة بالصلاحيات." />
      <div className="flex flex-col gap-3 rounded-2xl border bg-card p-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0 flex-1"><label htmlFor="popular-clinic-select" className="text-xs font-semibold text-muted-foreground">العيادة والوحدة الإدارية</label><select id="popular-clinic-select" value={clinicId ?? ""} onChange={(event) => { setClinicId(Number(event.target.value)); setSelectedPatient(undefined); }} className="mt-2 h-10 w-full rounded-xl border bg-background px-3 text-sm gula-focus-ring" disabled={!clinics.length} aria-describedby="popular-clinic-scope"><option value="">اختر العيادة</option>{clinics.map((clinic) => <option key={clinic.id} value={clinic.id}>{clinic.name} · {clinic.administrative_unit_code}</option>)}</select><p id="popular-clinic-scope" className="mt-2 text-xs text-muted-foreground">يُعرض فقط نطاق العيادة المسموح به لحسابك.</p></div>
        <Button variant="outline" onClick={() => void clinicsQuery.refetch()} loading={clinicsQuery.isFetching}><RefreshCw aria-hidden="true" />تحديث البيانات</Button>
      </div>
      <LoadState loading={clinicsQuery.isLoading} error={firstError} onRetry={() => void clinicsQuery.refetch()} />
      {!clinicsQuery.isLoading && !clinics.length && !firstError && <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-100" role="status">لا توجد عيادة شعبية متاحة ضمن نطاق حسابك.</div>}
      {selectedClinic && (
        <>
          <section aria-label="مؤشرات العيادة" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="المرضى المسجلون" value={monthlyQuery.data?.enrolled_patients ?? 0} icon={Users} />
            <Metric label="نسبة الاستلام الشهري" value={`${monthlyQuery.data?.dispensing_rate ?? 0}%`} icon={HeartPulse} />
            <Metric label="التحصيل النقدي اليوم" value={money(dailyQuery.data?.cash_total)} icon={CreditCard} />
            <Metric label="التحصيل الإلكتروني اليوم" value={money(dailyQuery.data?.electronic_total)} icon={FileBarChart2} />
          </section>
          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Users className="h-5 w-5 text-[#0D9488]" aria-hidden="true" />مرضى الأمراض المزمنة</CardTitle></CardHeader><CardContent className="space-y-4"><label htmlFor="popular-patient-search" className="sr-only">ابحث باسم المريض أو رقمه</label><div className="relative"><Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" /><input id="popular-patient-search" value={patientSearch} onChange={(event) => setPatientSearch(event.target.value)} placeholder="ابحث باسم المريض أو الرقم الصحي" className="h-10 w-full rounded-xl border bg-background px-10 text-sm gula-focus-ring" /></div><LoadState loading={patientsQuery.isLoading} error={patientsQuery.error} onRetry={() => void patientsQuery.refetch()} /><div className="max-h-72 space-y-2 overflow-y-auto" role="list" aria-label="قائمة مرضى العيادة">{(patientsQuery.data ?? []).map((patient) => <button type="button" key={patient.id} onClick={() => setSelectedPatient(patient)} className={`gula-focus-ring flex w-full items-center justify-between rounded-xl border p-3 text-right text-sm transition-colors hover:border-teal-300 hover:bg-teal-50/50 ${selectedPatient?.id === patient.id ? "border-teal-500 bg-teal-50/70 dark:bg-teal-950/30" : ""}`} role="listitem"><span><strong className="block">{patient.full_name}</strong><span className="text-xs text-muted-foreground">{patient.health_id || patient.phone}</span></span><span className="text-xs text-muted-foreground">عرض البطاقة</span></button>)}{patientsQuery.data?.length === 0 && <p className="text-sm text-muted-foreground">لا توجد نتائج.</p>}</div></CardContent></Card>
            <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><BookOpen className="h-5 w-5 text-[#0D9488]" aria-hidden="true" />بطاقة المريض ودفتر 12 شهراً</CardTitle></CardHeader><CardContent><LoadState loading={cardQuery.isLoading || bookletQuery.isLoading} error={cardQuery.error ?? bookletQuery.error} />{selectedPatient && !cardQuery.isLoading && !bookletQuery.isLoading && <PatientCard card={cardQuery.data} booklet={bookletQuery.data} />}</CardContent></Card>
          </div>
          <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
            <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><CreditCard className="h-5 w-5 text-[#0D9488]" aria-hidden="true" />تذاكر العيادة والتحصيل</CardTitle></CardHeader><CardContent><LoadState loading={ticketsQuery.isLoading} error={ticketsQuery.error} onRetry={() => void ticketsQuery.refetch()} /><TicketTable tickets={ticketsQuery.data ?? []} /></CardContent></Card>
            <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileBarChart2 className="h-5 w-5 text-[#0D9488]" aria-hidden="true" />التقرير الشهري للأمراض المزمنة</CardTitle></CardHeader><CardContent><div className="grid gap-3 sm:grid-cols-2"><Metric label="المستلمون" value={monthlyQuery.data?.dispensed_patients ?? 0} icon={Activity} /><Metric label="المتخلفون" value={monthlyQuery.data?.missed_patients ?? 0} icon={ShieldCheck} /></div><div className="mt-4 space-y-2 text-sm"><p className="font-semibold">الأدوية الأكثر طلباً</p>{(monthlyQuery.data?.most_requested_medications ?? []).slice(0, 5).map((medication) => <div key={medication.medication_name} className="flex justify-between gap-3 rounded-lg bg-muted/50 p-2"><span>{medication.medication_name}</span><span className="font-semibold">{medication.quantity}</span></div>)}</div></CardContent></Card>
          </div>
          <p className="rounded-xl border border-teal-200 bg-teal-50/60 p-4 text-xs leading-6 text-teal-950 dark:border-teal-900/50 dark:bg-teal-950/20 dark:text-teal-100">تظل صلاحيات إصدار التذاكر والتحصيل والتأكيد الإلكتروني منفصلة. هذه الشاشة لا تتجاوز بوابة الخادم ولا تحفظ بيانات صحية حساسة في المتصفح خارج استجابة الاستعلام المؤقتة.</p>
        </>
      )}
    </div>
  );
}

export default PopularClinicsWorkspacePage;
