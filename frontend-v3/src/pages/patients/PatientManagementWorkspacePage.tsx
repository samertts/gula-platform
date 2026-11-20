import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Clock3,
  LockKeyhole,
  FilePlus2,
  HeartPulse,
  ListChecks,
  MapPin,
  MessageSquareText,
  Search,
  ShieldCheck,
  UserPlus,
  UsersRound,
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageComponents";
import { useAuth } from "@/contexts/AuthContext";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type WorkspaceTab = "patients" | "registration" | "appointments" | "queue";
type Gender = "ذكر" | "أنثى";
type PatientStatus = "نشط" | "متابعة" | "جديد";

type PatientRecord = {
  id: number;
  healthId: string;
  name: string;
  phone: string;
  birthDate: string;
  gender: Gender;
  city: string;
  status: PatientStatus;
  lastVisit: string;
  carePath: string;
};

type Appointment = {
  id: number;
  patientId: number;
  patientName: string;
  service: string;
  clinician: string;
  time: string;
  status: "مؤكد" | "بانتظار التأكيد" | "مكتمل";
  location: string;
};

type QueueEntry = {
  id: number;
  patientName: string;
  service: string;
  arrival: string;
  priority: "عادي" | "أولوية";
  state: "بانتظار النداء" | "قيد الخدمة";
};

const INITIAL_PATIENTS: PatientRecord[] = [
  { id: 101, healthId: "GULA-240184", name: "سارة عبد الرحمن", phone: "+964 770 240 1840", birthDate: "1992-04-16", gender: "أنثى", city: "بغداد", status: "متابعة", lastVisit: "2026-08-12", carePath: "متابعة السكري" },
  { id: 102, healthId: "GULA-240219", name: "علي كريم حسن", phone: "+964 771 240 2190", birthDate: "1987-11-03", gender: "ذكر", city: "البصرة", status: "نشط", lastVisit: "2026-08-13", carePath: "طب الأسرة" },
  { id: 103, healthId: "GULA-240287", name: "مريم فاضل", phone: "+964 772 240 2870", birthDate: "2001-06-22", gender: "أنثى", city: "أربيل", status: "جديد", lastVisit: "2026-08-14", carePath: "استشارة عامة" },
  { id: 104, healthId: "GULA-240311", name: "حسن نوري", phone: "+964 773 240 3110", birthDate: "1974-02-09", gender: "ذكر", city: "النجف", status: "متابعة", lastVisit: "2026-08-10", carePath: "أمراض القلب" },
];

const INITIAL_APPOINTMENTS: Appointment[] = [
  { id: 1, patientId: 101, patientName: "سارة عبد الرحمن", service: "متابعة السكري", clinician: "د. نور الهدى", time: "09:30", status: "مؤكد", location: "عيادة الأسرة 2" },
  { id: 2, patientId: 102, patientName: "علي كريم حسن", service: "طب الأسرة", clinician: "د. عمر سالم", time: "10:15", status: "بانتظار التأكيد", location: "عيادة الأسرة 1" },
  { id: 3, patientId: 104, patientName: "حسن نوري", service: "أمراض القلب", clinician: "د. رائد حسن", time: "11:00", status: "مؤكد", location: "العيادة التخصصية" },
  { id: 4, patientId: 103, patientName: "مريم فاضل", service: "استشارة عامة", clinician: "د. ليان محمود", time: "12:30", status: "مكتمل", location: "الاستقبال الصحي" },
];

const INITIAL_QUEUE: QueueEntry[] = [
  { id: 1, patientName: "سارة عبد الرحمن", service: "سحب عينة", arrival: "08:45", priority: "أولوية", state: "قيد الخدمة" },
  { id: 2, patientName: "علي كريم حسن", service: "طب الأسرة", arrival: "09:02", priority: "عادي", state: "بانتظار النداء" },
  { id: 3, patientName: "مريم فاضل", service: "التسجيل الأولي", arrival: "09:18", priority: "عادي", state: "بانتظار النداء" },
];

const tabs: Array<{ id: WorkspaceTab; label: string; icon: typeof UsersRound }> = [
  { id: "patients", label: "دليل المرضى", icon: UsersRound },
  { id: "registration", label: "تسجيل مريض", icon: UserPlus },
  { id: "appointments", label: "المواعيد", icon: CalendarDays },
  { id: "queue", label: "قائمة الانتظار", icon: ListChecks },
];

const statusVariant = (status: PatientStatus | Appointment["status"] | QueueEntry["state"]): "success" | "warning" | "default" | "outline" => {
  if (status === "نشط" || status === "مؤكد" || status === "قيد الخدمة") return "success";
  if (status === "متابعة" || status === "بانتظار التأكيد" || status === "بانتظار النداء") return "warning";
  if (status === "جديد" || status === "مكتمل") return "outline";
  return "default";
};

const initialForm = { name: "", phone: "", birthDate: "", gender: "أنثى" as Gender, city: "بغداد", carePath: "استشارة عامة" };

export function PatientManagementWorkspacePage() {
  const { demoMode } = useAuth();
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("patients");
  const [patients, setPatients] = useState<PatientRecord[]>(INITIAL_PATIENTS);
  const [appointments] = useState<Appointment[]>(INITIAL_APPOINTMENTS);
  const [queue] = useState<QueueEntry[]>(INITIAL_QUEUE);
  const [selectedPatientId, setSelectedPatientId] = useState(INITIAL_PATIENTS[0]?.id ?? 101);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(initialForm);
  const [message, setMessage] = useState("");

  const filteredPatients = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("ar");
    if (!term) return patients;
    return patients.filter((patient) => `${patient.name} ${patient.healthId} ${patient.phone} ${patient.city} ${patient.carePath}`.toLocaleLowerCase("ar").includes(term));
  }, [patients, search]);

  const selectedPatient = patients.find((patient) => patient.id === selectedPatientId) ?? patients[0];

  if (!demoMode) return <LiveDataBoundary />;

  const submitRegistration = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.name.trim() || !form.phone.trim() || !form.birthDate) {
      setMessage("يرجى إكمال الاسم ورقم الهاتف وتاريخ الميلاد.");
      return;
    }
    const nextId = Math.max(...patients.map((patient) => patient.id), 100) + 1;
    const newPatient: PatientRecord = {
      id: nextId,
      healthId: `GULA-${String(nextId).padStart(6, "0")}`,
      name: form.name.trim(),
      phone: form.phone.trim(),
      birthDate: form.birthDate,
      gender: form.gender,
      city: form.city,
      status: "جديد",
      lastVisit: "اليوم",
      carePath: form.carePath,
    };
    setPatients((current) => [newPatient, ...current]);
    setSelectedPatientId(newPatient.id);
    setForm(initialForm);
    setMessage(`تم إنشاء ملف تجريبي للمريض ${newPatient.name}.`);
    setActiveTab("patients");
  };

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="إدارة المرضى" description="مساحة GULA الأصلية للتسجيل والبحث والمواعيد وقوائم الانتظار، مبنية حول عقود صحية قابلة للتكامل." />

      <Card className="overflow-hidden border-emerald-200 bg-gradient-to-l from-emerald-50 via-white to-indigo-50 dark:border-emerald-900/50 dark:from-emerald-950/30 dark:via-background dark:to-indigo-950/30">
        <CardContent className="p-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-3xl space-y-3">
              <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300"><HeartPulse className="h-5 w-5" /><span className="text-sm font-semibold">Patient Management Core</span></div>
              <h2 className="text-2xl font-bold tracking-tight">مسار مريض واضح من التسجيل إلى المتابعة</h2>
              <p className="text-sm leading-7 text-muted-foreground">تجمع هذه المساحة الوظائف التي ظهرت في OpenMRS وOttehr وOpenEMR — التسجيل، البحث، المواعيد، قائمة الانتظار، وسجل المريض — في تجربة GULA أصلية. البيانات المعروضة اصطناعية ولا تُرسل إلى أي خدمة خارجية.</p>
              <div className="flex flex-wrap gap-2"><Badge variant="success"><ShieldCheck className="ml-1 h-3.5 w-3.5" />وضع تجريبي معزول</Badge><Badge variant="outline"><Activity className="ml-1 h-3.5 w-3.5" />FHIR-ready</Badge><Badge variant="outline"><ClipboardList className="ml-1 h-3.5 w-3.5" />لا نسخ للكود</Badge></div>
            </div>
            <div className="grid min-w-[250px] grid-cols-2 gap-3">
              <Metric label="ملفات المرضى" value={patients.length} icon={UsersRound} />
              <Metric label="مواعيد اليوم" value={appointments.length} icon={CalendarDays} />
              <Metric label="في الانتظار" value={queue.length} icon={Clock3} />
              <Metric label="خدمات الرعاية" value={new Set(patients.map((patient) => patient.carePath)).size} icon={HeartPulse} />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <div className="flex flex-wrap border-b">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return <button key={tab.id} type="button" onClick={() => { setActiveTab(tab.id); setMessage(""); }} className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-emerald-600 text-emerald-700 dark:text-emerald-300" : "text-muted-foreground hover:text-foreground"}`}><Icon className="h-4 w-4" />{tab.label}</button>;
            })}
          </div>
        </CardContent>
      </Card>

      {message && <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300" role="status"><CheckCircle2 className="ml-2 inline h-4 w-4" />{message}</div>}

      {activeTab === "patients" && <PatientsDirectory patients={filteredPatients} selectedPatient={selectedPatient} search={search} onSearch={setSearch} onSelect={setSelectedPatientId} />}
      {activeTab === "registration" && <RegistrationForm form={form} onChange={setForm} onSubmit={submitRegistration} />}
      {activeTab === "appointments" && <AppointmentsBoard appointments={appointments} />}
      {activeTab === "queue" && <QueueBoard queue={queue} />}

      <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><ShieldCheck className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حدود الإصدار الحالي:</strong> عمليات التسجيل والتحديد محلية داخل العرض التجريبي فقط. عند ربطها ببيانات حقيقية، يجب تمريرها عبر عقد خادمي، وصلاحيات workspace، وسجل تدقيق، وموارد FHIR مثل Patient وAppointment وEncounter وTask.</p></CardContent></Card>
    </div>
  );
}

function Metric({ label, value, icon: Icon }: { label: string; value: number; icon: typeof UsersRound }) {
  return <div className="rounded-xl bg-background/80 p-4 shadow-sm"><div className="flex items-center justify-between gap-2"><p className="text-xs text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-emerald-600" /></div><p className="mt-1 text-2xl font-bold">{value}</p></div>;
}

function PatientsDirectory({ patients, selectedPatient, search, onSearch, onSelect }: { patients: PatientRecord[]; selectedPatient?: PatientRecord; search: string; onSearch: (value: string) => void; onSelect: (id: number) => void }) {
  return <div className="grid gap-4 xl:grid-cols-[minmax(0,1.45fr)_minmax(300px,0.75fr)]">
    <Card><CardHeader className="pb-3"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><CardTitle className="text-base">دليل المرضى</CardTitle><div className="relative w-full sm:w-80"><Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="ابحث بالاسم أو رقم GULA..." className="pr-9" /></div></div></CardHeader><CardContent className="space-y-2">
      {patients.map((patient) => <button key={patient.id} type="button" onClick={() => onSelect(patient.id)} className={`w-full rounded-lg border p-4 text-right transition hover:border-emerald-300 hover:bg-emerald-50/40 dark:hover:bg-emerald-950/20 ${selectedPatient?.id === patient.id ? "border-emerald-400 bg-emerald-50/60 dark:border-emerald-700 dark:bg-emerald-950/30" : "border-border"}`}><div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{patient.name}</p><p className="mt-1 text-xs text-muted-foreground">{patient.healthId} · {patient.phone}</p></div><Badge variant={statusVariant(patient.status)}>{patient.status}</Badge></div><div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground"><span>{patient.city}</span><span>{patient.carePath}</span><span>آخر زيارة: {patient.lastVisit}</span></div></button>)}
      {patients.length === 0 && <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">لا يوجد مريض مطابق للبحث الحالي.</div>}
    </CardContent></Card>
    <PatientProfile patient={selectedPatient} />
  </div>;
}

function PatientProfile({ patient }: { patient?: PatientRecord }) {
  if (!patient) return <Card><CardContent className="p-8 text-center text-sm text-muted-foreground">اختر مريضًا لعرض ملخصه.</CardContent></Card>;
  return <Card><CardHeader className="pb-3"><div className="flex items-start justify-between gap-3"><div><CardTitle className="text-base">ملخص المريض</CardTitle><p className="mt-1 text-sm text-muted-foreground">{patient.healthId}</p></div><div className="rounded-full bg-emerald-100 p-3 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"><HeartPulse className="h-5 w-5" /></div></div></CardHeader><CardContent className="space-y-4"><div><p className="text-lg font-bold">{patient.name}</p><p className="mt-1 text-sm text-muted-foreground">{patient.gender} · {patient.city}</p></div><div className="grid grid-cols-2 gap-3 text-sm"><Info label="الهاتف" value={patient.phone} /><Info label="الميلاد" value={patient.birthDate} /><Info label="المسار" value={patient.carePath} /><Info label="الحالة" value={patient.status} /></div><div className="rounded-lg bg-muted/50 p-3 text-sm leading-6"><p className="font-semibold">خط زمني مختصر</p><p className="mt-1 text-muted-foreground">آخر زيارة في {patient.lastVisit}. لا توجد تغييرات تشغيلية في العرض التجريبي.</p></div><Link to="/patient-card" className="inline-flex items-center gap-2 text-sm font-medium text-emerald-700 hover:underline dark:text-emerald-300">فتح بطاقة المريض الحالية <ArrowLeft className="h-4 w-4" /></Link></CardContent></Card>;
}

function Info({ label, value }: { label: string; value: string }) { return <div className="rounded-lg border p-3"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-medium">{value}</p></div>; }

function RegistrationForm({ form, onChange, onSubmit }: { form: typeof initialForm; onChange: (value: typeof initialForm) => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  const update = (key: keyof typeof initialForm, value: string) => onChange({ ...form, [key]: value });
  return <Card><CardHeader><div className="flex items-center gap-3"><div className="rounded-xl bg-indigo-100 p-3 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300"><FilePlus2 className="h-5 w-5" /></div><div><CardTitle className="text-base">تسجيل مريض جديد</CardTitle><p className="mt-1 text-sm text-muted-foreground">نموذج GULA أصلي قابل للتحويل لاحقًا إلى مورد Patient.</p></div></div></CardHeader><CardContent><form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2"><Field label="الاسم الكامل" required><Input value={form.name} onChange={(event) => update("name", event.target.value)} placeholder="مثال: أحمد علي" /></Field><Field label="رقم الهاتف" required><Input value={form.phone} onChange={(event) => update("phone", event.target.value)} placeholder="+964 7XX XXX XXXX" /></Field><Field label="تاريخ الميلاد" required><Input type="date" value={form.birthDate} onChange={(event) => update("birthDate", event.target.value)} /></Field><Field label="الجنس"><select value={form.gender} onChange={(event) => update("gender", event.target.value)} className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"><option>أنثى</option><option>ذكر</option></select></Field><Field label="المحافظة"><Input value={form.city} onChange={(event) => update("city", event.target.value)} /></Field><Field label="مسار الرعاية"><select value={form.carePath} onChange={(event) => update("carePath", event.target.value)} className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"><option>استشارة عامة</option><option>طب الأسرة</option><option>متابعة السكري</option><option>أمراض القلب</option></select></Field><div className="flex items-center justify-between gap-3 border-t pt-4 md:col-span-2"><p className="text-xs text-muted-foreground">سيُنشأ السجل محليًا في العرض التجريبي فقط.</p><Button type="submit"><UserPlus className="h-4 w-4" />إنشاء ملف تجريبي</Button></div></form></CardContent></Card>;
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) { return <label className="space-y-1.5 text-sm"><span className="font-medium">{label}{required && <span className="mr-1 text-destructive">*</span>}</span>{children}</label>; }

function AppointmentsBoard({ appointments }: { appointments: Appointment[] }) {
  return <Card><CardHeader><CardTitle className="text-base">مواعيد اليوم</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-2">{appointments.map((appointment) => <div key={appointment.id} className="rounded-xl border p-4"><div className="flex items-center justify-between gap-3"><div><p className="font-semibold">{appointment.time} · {appointment.patientName}</p><p className="mt-1 text-sm text-muted-foreground">{appointment.service} · {appointment.clinician}</p></div><Badge variant={statusVariant(appointment.status)}>{appointment.status}</Badge></div><div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground"><span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{appointment.location}</span><span className="inline-flex items-center gap-1"><MessageSquareText className="h-3.5 w-3.5" />إشعار محلي</span></div></div>)}</CardContent></Card>;
}

function QueueBoard({ queue }: { queue: QueueEntry[] }) {
  return <Card><CardHeader><div className="flex items-center justify-between gap-3"><CardTitle className="text-base">قائمة الانتظار</CardTitle><Badge variant="outline">تحديث تجريبي</Badge></div></CardHeader><CardContent className="space-y-3">{queue.map((entry, index) => <div key={entry.id} className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">{index + 1}</span><div><p className="font-semibold">{entry.patientName}</p><p className="mt-1 text-sm text-muted-foreground">{entry.service} · الوصول {entry.arrival}</p></div></div><div className="flex items-center gap-2"><Badge variant={entry.priority === "أولوية" ? "warning" : "outline"}>{entry.priority}</Badge><Badge variant={statusVariant(entry.state)}>{entry.state}</Badge></div></div>)}</CardContent></Card>;
}

function LiveDataBoundary() {
  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="إدارة المرضى" description="مساحة العمل السريرية لا تُعرض قبل اعتماد عقد القراءة المؤسسية." />
      <Card className="border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20">
        <CardContent className="p-6">
          <div className="flex items-start gap-3" role="status" aria-live="polite">
            <LockKeyhole className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" aria-hidden="true" />
            <div className="space-y-2">
              <h2 className="font-semibold text-amber-950 dark:text-amber-200">القراءة المؤسسية معلّقة بأمان</h2>
              <p className="text-sm leading-7 text-amber-900/80 dark:text-amber-100/75">هذه الصفحة تحتوي حالياً على بيانات اصطناعية وتسجيل محلي للعرض التجريبي فقط. لن نعرضها في الجلسة الحية حتى يكتمل عقد الخادم والتفويض والعزل وسجل التدقيق.</p>
              <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm font-semibold text-amber-900 underline-offset-4 hover:underline dark:text-amber-200">العودة إلى لوحة العمل الآمنة <ArrowLeft className="h-4 w-4" aria-hidden="true" /></Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default PatientManagementWorkspacePage;
