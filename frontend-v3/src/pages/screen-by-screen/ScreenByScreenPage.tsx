import { useState, type ReactNode } from "react";
import {
  Activity,
  Ambulance,
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  FileCheck2,
  FlaskConical,
  HeartPulse,
  Home,
  Hospital,
  KeyRound,
  LayoutDashboard,
  LockKeyhole,
  Mail,
  Menu,
  Microscope,
  Monitor,
  Pill,
  Search,
  ShieldCheck,
  Siren,
  Stethoscope,
  UserCircle,
  Users,
  type LucideIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ClinicalStatePanel, ClinicalStatusBadge, CriticalAlertBanner, ClinicalTimeline, PatientContextCard } from "@/components/clinical";


type RoleKey = "entry" | "citizen" | "doctor" | "nurse" | "lab" | "pharmacy" | "hospital" | "emergency" | "admin" | "web";
type ScreenKey =
  | "welcome"
  | "login"
  | "otp"
  | "new-device"
  | "identity-journey"
  | "citizen-home"
  | "health-timeline"
  | "lab-result"
  | "appointments"
  | "sharing"
  | "security"
  | "doctor-dashboard"
  | "patient-context"
  | "encounter"
  | "nurse-dashboard"
  | "nurse-patient"
  | "lab-dashboard"
  | "lab-worklist"
  | "pharmacy-dashboard"
  | "pharmacy-verification"
  | "hospital-dashboard"
  | "bed-management"
  | "emergency-dashboard"
  | "ambulance-app"
  | "icu-dashboard"
  | "admin-dashboard"
  | "audit-viewer"
  | "web-portal"
  | "desktop-workspace";

type ScreenDefinition = { id: ScreenKey; label: string; description: string; icon: LucideIcon };
type RoleDefinition = { id: RoleKey; label: string; shortLabel: string; icon: LucideIcon; screens: ScreenDefinition[] };

const ROLE_DEFINITIONS: RoleDefinition[] = [
  { id: "entry", label: "البداية والوصول", shortLabel: "الوصول", icon: KeyRound, screens: [
    { id: "welcome", label: "الترحيب", description: "اختيار الدخول أو طلب الحساب", icon: Home },
    { id: "login", label: "تسجيل الدخول", description: "مواطن أو مؤسسة", icon: LockKeyhole },
    { id: "otp", label: "رمز التحقق", description: "OTP دون تنفيذ حي في المعرض", icon: Mail },
    { id: "new-device", label: "جهاز جديد", description: "خطوة تحقق إضافية", icon: ShieldCheck },
    { id: "identity-journey", label: "رحلة الهوية", description: "OCR/NFC/Selfie كحالات محكومة", icon: UserCircle },
  ] },
  { id: "citizen", label: "المواطن", shortLabel: "مواطن", icon: UserCircle, screens: [
    { id: "citizen-home", label: "الرئيسية الصحية", description: "ملخص، موعد، نتائج، أدوية", icon: LayoutDashboard },
    { id: "health-timeline", label: "صحتي والتسلسل", description: "Timeline مصفّى", icon: Activity },
    { id: "lab-result", label: "النتيجة المختبرية", description: "قيمة ووحدة وتنبيه", icon: FlaskConical },
    { id: "appointments", label: "المواعيد", description: "موعد قادم ومسار الحجز", icon: CalendarDays },
    { id: "sharing", label: "مشاركة البيانات", description: "غرض ونطاق ومدة", icon: Users },
    { id: "security", label: "الأمان والجلسات", description: "MFA وأجهزة وجلسات", icon: ShieldCheck },
  ] },
  { id: "doctor", label: "الطبيب", shortLabel: "طبيب", icon: Stethoscope, screens: [
    { id: "doctor-dashboard", label: "لوحة الطبيب", description: "مرضى ومهام ونتائج", icon: LayoutDashboard },
    { id: "patient-context", label: "سياق المريض", description: "ملخص محدود وحساسيات", icon: UserCircle },
    { id: "encounter", label: "مساحة Encounter", description: "عرض مراحل لا كتابة محلية", icon: Stethoscope },
  ] },
  { id: "nurse", label: "الممرض", shortLabel: "ممرض", icon: HeartPulse, screens: [
    { id: "nurse-dashboard", label: "لوحة الممرض", description: "جناح ومهام وتنبيهات", icon: LayoutDashboard },
    { id: "nurse-patient", label: "مريض التمريض", description: "Vitals وMedication وHandover", icon: HeartPulse },
  ] },
  { id: "lab", label: "المختبر", shortLabel: "مختبر", icon: Microscope, screens: [
    { id: "lab-dashboard", label: "لوحة المختبر", description: "Orders وQC وAnalyzer", icon: LayoutDashboard },
    { id: "lab-worklist", label: "Worklist", description: "Specimen وPriority وStatus", icon: ClipboardList },
  ] },
  { id: "pharmacy", label: "الصيدلية", shortLabel: "صيدلية", icon: Pill, screens: [
    { id: "pharmacy-dashboard", label: "لوحة الصيدلية", description: "وصفات ومخزون وتنبيهات", icon: LayoutDashboard },
    { id: "pharmacy-verification", label: "التحقق والصرف", description: "فصل Verification عن Dispensing", icon: Pill },
  ] },
  { id: "hospital", label: "المستشفى", shortLabel: "مستشفى", icon: Hospital, screens: [
    { id: "hospital-dashboard", label: "لوحة المستشفى", description: "طوارئ وأسرة وICU وOR", icon: LayoutDashboard },
    { id: "bed-management", label: "إدارة الأسرة", description: "Occupancy وBed Detail", icon: Hospital },
  ] },
  { id: "emergency", label: "الطوارئ والإسعاف", shortLabel: "طوارئ", icon: Siren, screens: [
    { id: "emergency-dashboard", label: "لوحة الطوارئ", description: "Critical وWaiting وResus", icon: Siren },
    { id: "ambulance-app", label: "تطبيق الإسعاف", description: "Incident بأقل عدد من اللمسات", icon: Ambulance },
    { id: "icu-dashboard", label: "لوحة ICU", description: "أسرة واتجاهات محكومة", icon: HeartPulse },
  ] },
  { id: "admin", label: "الإدارة والحوكمة", shortLabel: "إدارة", icon: ShieldCheck, screens: [
    { id: "admin-dashboard", label: "لوحة الإدارة", description: "مؤسسة وقدرات وجودة وأمان", icon: LayoutDashboard },
    { id: "audit-viewer", label: "سجل التدقيق", description: "أحداث مصفّاة ومقيدة", icon: FileCheck2 },
  ] },
  { id: "web", label: "البوابة وDesktop", shortLabel: "بوابة", icon: Monitor, screens: [
    { id: "web-portal", label: "Web Portal", description: "خدمات وأطباء ومؤسسات", icon: Search },
    { id: "desktop-workspace", label: "Desktop Workspace", description: "Master / Detail للبيانات الكبيرة", icon: Menu },
  ] },
];

export default function ScreenByScreenPage() {
  const [roleId, setRoleId] = useState<RoleKey>("entry");
  const [screenId, setScreenId] = useState<ScreenKey>("welcome");
  const role = ROLE_DEFINITIONS.find((item) => item.id === roleId) ?? ROLE_DEFINITIONS[0]!;
  const screen = role.screens.find((item) => item.id === screenId) ?? role.screens[0]!;
  const selectRole = (nextRole: RoleKey) => {
    const next = ROLE_DEFINITIONS.find((item) => item.id === nextRole) ?? ROLE_DEFINITIONS[0]!;
    setRoleId(nextRole);
    setScreenId(next.screens[0]!.id);
  };

  return (
    <div className="mx-auto max-w-[90rem] space-y-6" dir="rtl">
      <header className="gula-interactive-surface overflow-hidden bg-gradient-to-l from-slate-950 via-[#12344b] to-[#0d9488] text-white">
        <div className="relative grid gap-8 p-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-end lg:p-9">
          <div className="absolute -left-24 -top-32 h-72 w-72 rounded-full bg-cyan-300/10 blur-3xl" aria-hidden="true" />
          <div className="relative space-y-4">
            <div className="flex flex-wrap items-center gap-2"><Badge className="border-white/20 bg-white/10 text-white"><ShieldCheck className="ml-1 h-3.5 w-3.5" />Screen-by-Screen Preview</Badge><Badge className="border-amber-200/20 bg-amber-200/10 text-amber-100">Demo فقط · قراءة فقط</Badge></div>
            <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">مخطط الواجهات الفعلية في شاشة واحدة</h1>
            <p className="max-w-3xl text-sm leading-7 text-slate-200">معرض تفاعلي لمعاينة شاشات GULA حسب الدور والجهاز. البيانات اصطناعية، والعمليات التي تحتاج عقوداً سريرية تظهر كـgated state بدلاً من زر وهمي.</p>
          </div>
          <div className="relative grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2"><PreviewMetric label="الأدوار" value="10" /><PreviewMetric label="الشاشات" value="30" /><PreviewMetric label="RTL / LTR" value="✓" /><PreviewMetric label="Live writes" value="0" /></div>
        </div>
      </header>

      <nav className="gula-interactive-surface overflow-x-auto" aria-label="أدوار المعرض"><div className="flex min-w-max gap-2 p-2">{ROLE_DEFINITIONS.map(({ id, label, shortLabel, icon: Icon }) => <button key={id} type="button" aria-pressed={roleId === id} onClick={() => selectRole(id)} className={`gula-focus-ring flex min-h-11 items-center gap-2 rounded-xl px-3 text-sm font-semibold transition ${roleId === id ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}><Icon className="h-4 w-4" /><span className="hidden sm:inline">{label}</span><span className="sm:hidden">{shortLabel}</span></button>)}</div></nav>

      <div className="grid gap-6 xl:grid-cols-[18rem_minmax(0,1fr)]">
        <aside className="gula-interactive-surface h-fit p-3 xl:sticky xl:top-24" aria-label={`شاشات ${role.label}`}><div className="mb-3 flex items-center gap-2 px-2"><role.icon className="h-4 w-4 text-primary" /><div><p className="gula-section-label">{role.label}</p><p className="text-xs text-muted-foreground">اختر شاشة للمعاينة</p></div></div><div className="space-y-1">{role.screens.map(({ id, label, description, icon: Icon }) => <button key={id} type="button" aria-current={screenId === id ? "page" : undefined} onClick={() => setScreenId(id)} className={`gula-focus-ring flex w-full items-start gap-3 rounded-xl p-3 text-right transition ${screenId === id ? "bg-primary-light text-primary dark:bg-primary/20 dark:text-teal-200" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}><Icon className="mt-0.5 h-4 w-4 shrink-0" /><span className="min-w-0"><span className="block text-sm font-semibold">{label}</span><span className="mt-1 block text-[11px] leading-5 opacity-75">{description}</span></span></button>)}</div></aside>
        <main className="min-w-0 space-y-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="gula-section-label">{role.label}</p><h2 className="mt-1 font-display text-2xl font-bold">{screen.label}</h2><p className="mt-1 text-sm text-muted-foreground">{screen.description}</p></div><div className="flex items-center gap-2"><ClinicalStatusBadge status="partial" label="معاينة اصطناعية" /><Badge variant="outline">{screen.id}</Badge></div></div><ScreenStage screenId={screen.id} onNavigate={setScreenId} /></main>
      </div>

      <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20"><CardContent className="flex items-start gap-3 p-5 text-sm leading-7 text-amber-950 dark:text-amber-100"><LockKeyhole className="mt-1 h-5 w-5 shrink-0" /><p><strong>حدود المعرض:</strong> هذه الشاشات مصممة للمشاهدة والاختبار البصري والوظيفي الآمن. لا تنشئ حساباً أو دوراً أو Workspace أو Encounter أو وصفة أو نتيجة أو حجزاً، ولا تتصل ببيانات حقيقية أو خدمات حكومية أو أجهزة أو HIS/LIS/RIS/PACS.</p></CardContent></Card>
    </div>
  );
}

function ScreenStage({ screenId, onNavigate }: { screenId: ScreenKey; onNavigate: (screen: ScreenKey) => void }) {
  switch (screenId) {
    case "welcome": return <WelcomeScreen onNavigate={onNavigate} />;
    case "login": return <LoginScreen onNavigate={onNavigate} />;
    case "otp": return <OtpScreen onNavigate={onNavigate} />;
    case "new-device": return <NewDeviceScreen onNavigate={onNavigate} />;
    case "identity-journey": return <IdentityJourneyScreen />;
    case "citizen-home": return <CitizenHomeScreen onNavigate={onNavigate} />;
    case "health-timeline": return <HealthTimelineScreen />;
    case "lab-result": return <LabResultScreen />;
    case "appointments": return <AppointmentsScreen />;
    case "sharing": return <SharingScreen />;
    case "security": return <SecurityScreen />;
    case "doctor-dashboard": return <DoctorDashboardScreen onNavigate={onNavigate} />;
    case "patient-context": return <PatientContextScreen />;
    case "encounter": return <EncounterScreen />;
    case "nurse-dashboard": return <NurseDashboardScreen />;
    case "nurse-patient": return <NursePatientScreen />;
    case "lab-dashboard": return <LabDashboardScreen />;
    case "lab-worklist": return <LabWorklistScreen />;
    case "pharmacy-dashboard": return <PharmacyDashboardScreen />;
    case "pharmacy-verification": return <PharmacyVerificationScreen />;
    case "hospital-dashboard": return <HospitalDashboardScreen />;
    case "bed-management": return <BedManagementScreen />;
    case "emergency-dashboard": return <EmergencyDashboardScreen />;
    case "ambulance-app": return <AmbulanceAppScreen />;
    case "icu-dashboard": return <IcuDashboardScreen />;
    case "admin-dashboard": return <AdminDashboardScreen />;
    case "audit-viewer": return <AuditViewerScreen />;
    case "web-portal": return <WebPortalScreen onNavigate={onNavigate} />;
    case "desktop-workspace": return <DesktopWorkspaceScreen />;
  }
}

function WelcomeScreen({ onNavigate }: { onNavigate: (screen: ScreenKey) => void }) {
  return <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]"><Card className="overflow-hidden bg-gradient-to-br from-primary to-slate-950 text-white"><CardContent className="p-7 sm:p-10"><Badge className="border-white/20 bg-white/10 text-white">GULA Health Platform</Badge><h3 className="mt-6 text-4xl font-bold leading-tight">صحتك في مكان واحد</h3><p className="mt-4 max-w-xl text-sm leading-7 text-slate-200">هوية واحدة ومساحات عمل متعددة ورحلة صحية موحدة، مع وضوح دائم لما هو متاح وما يحتاج عقداً خادمياً.</p><div className="mt-7 flex flex-wrap gap-3"><Button type="button" onClick={() => onNavigate("login")}>تسجيل الدخول <ArrowLeft className="ms-2 h-4 w-4" /></Button><Button type="button" variant="outline" className="border-white/30 bg-white/10 text-white hover:bg-white/20" onClick={() => onNavigate("identity-journey")}>طلب إنشاء حساب</Button></div></CardContent></Card><PreviewPanel title="ابدأ بأمان" icon={ShieldCheck}><FeatureLine label="مواطن" value="صحتي · مواعيدي · مشاركة" /><FeatureLine label="مؤسسة" value="مساحات وصلاحيات معادة من الخادم" /><FeatureLine label="Demo" value="اصطناعي · معزول · قراءة فقط" /><ClinicalStatePanel state="partial" title="التكاملات المستقبلية" description="OCR وNFC والتحقق الحيوي تظهر كحالات محكومة ولا تدّعي أنها مفعلة." /></PreviewPanel></div>;
}

function LoginScreen({ onNavigate }: { onNavigate: (screen: ScreenKey) => void }) {
  return <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]"><div className="rounded-2xl bg-slate-950 p-7 text-white sm:p-10"><p className="gula-section-label text-teal-300">Secure access</p><h3 className="mt-4 text-3xl font-bold">اختر طريق الدخول</h3><p className="mt-3 text-sm leading-7 text-slate-300">المواطن والمؤسسة لهما تجربة واضحة، لكن تسجيل الدخول لا يمنح دوراً أو وصولاً سريرياً.</p><div className="mt-8 space-y-3"><FeatureLine label="دخول المواطن" value="هوية وحساب صحي" inverse /><FeatureLine label="دخول المؤسسة" value="Workspace عضوي معاد من الخادم" inverse /><FeatureLine label="Demo" value="لا بيانات حقيقية" inverse /></div></div><Card><CardHeader><CardTitle>تسجيل الدخول</CardTitle><p className="text-xs text-muted-foreground">شاشة معاينة؛ الزر لا يرسل بيانات في المعرض.</p></CardHeader><CardContent className="space-y-4"><label className="block text-sm font-semibold" htmlFor="preview-login">الهاتف أو البريد</label><Input id="preview-login" placeholder="+964 7XX XXX XXXX" disabled /><label className="block text-sm font-semibold" htmlFor="preview-password">كلمة المرور</label><Input id="preview-password" type="password" placeholder="••••••••" disabled /><Button type="button" className="w-full" onClick={() => onNavigate("otp")}>متابعة إلى OTP <ArrowLeft className="ms-2 h-4 w-4" /></Button><Button type="button" variant="outline" className="w-full" onClick={() => onNavigate("citizen-home")}>مشاهدة المواطن Demo</Button><ClinicalStatePanel state="maintenance" title="طرق الدخول الأخرى" description="المزودات الخارجية وWebAuthn وMFA الفعلي تحتاج عقداً خادمياً مفوضاً." /></CardContent></Card></div>;
}

function OtpScreen({ onNavigate }: { onNavigate: (screen: ScreenKey) => void }) {
  return <CenteredAuthScreen icon={KeyRound} title="أرسلنا رمز التحقق" description="••••••••1234 · هذا العرض لا يرسل OTP ولا يتحقق من هاتف حقيقي."><div className="grid grid-cols-6 gap-2">{[1, 2, 3, 4, 5, 6].map((digit) => <Input key={digit} aria-label={`خانة ${digit}`} className="h-12 px-0 text-center text-lg" disabled />)}</div><div className="flex items-center justify-between gap-3 text-xs text-muted-foreground"><span>إعادة الإرسال بعد 30 ثانية</span><Badge variant="outline">Preview</Badge></div><Button type="button" className="w-full" onClick={() => onNavigate("new-device")}>متابعة المعاينة</Button></CenteredAuthScreen>;
}

function NewDeviceScreen({ onNavigate }: { onNavigate: (screen: ScreenKey) => void }) {
  return <CenteredAuthScreen icon={ShieldCheck} title="تم اكتشاف جهاز جديد" description="لأمان حسابك يحتاج الجهاز غير المعروف إلى تحقق إضافي من الخادم."><ClinicalStatePanel state="partial" title="التحقق الإضافي غير موصول في المعرض" description="لا نعرض طريقة تحقق أو نجاحاً وهمياً. عند توفر العقد، سيظهر السبب ومدة الصلاحية وسجل التدقيق." /><Button type="button" className="w-full" onClick={() => onNavigate("identity-journey")}>مشاهدة رحلة الهوية</Button></CenteredAuthScreen>;
}

function IdentityJourneyScreen() {
  const steps = ["Phone", "OTP", "Identity Verification", "OCR", "NFC / Reader", "Selfie / Liveness", "Identity Resolution", "Account", "Health Record"];
  return <div className="space-y-4"><PreviewPanel title="إنشاء حساب المواطن · رحلة محكومة" icon={UserCircle}><div className="grid gap-3 md:grid-cols-3">{steps.map((step, index) => <div key={step} className="flex items-center gap-3 rounded-xl border p-3"><span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${index < 2 ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-200"}`}>{index + 1}</span><div><p className="text-sm font-semibold">{step}</p><p className="mt-1 text-[11px] text-muted-foreground">{index < 2 ? "حالة عرض" : "يتطلب عقداً"}</p></div></div>)}</div></PreviewPanel><div className="grid gap-4 md:grid-cols-3"><ClinicalStatePanel state="maintenance" title="OCR" description="لا قراءة بطاقة أو استخراج بيانات في Demo." /><ClinicalStatePanel state="maintenance" title="NFC / Liveness" description="لا قارئ خارجي أو biometrics مفعلة." /><ClinicalStatePanel state="forbidden" title="Identity Resolution" description="لا دمج تلقائي ولا إنشاء Health Record من الواجهة." /></div></div>;
}

function CitizenHomeScreen({ onNavigate }: { onNavigate: (screen: ScreenKey) => void }) {
  return <div className="space-y-4"><div className="rounded-2xl bg-gradient-to-l from-teal-700 to-slate-950 p-6 text-white"><p className="text-sm text-teal-100">مرحباً، سامر</p><h3 className="mt-2 text-3xl font-bold">ملخصك الصحي</h3><p className="mt-2 text-sm text-slate-300">هذا ملخص اصطناعي لا يمثل ملفاً صحياً حقيقياً.</p></div><div className="grid gap-4 md:grid-cols-3"><SummaryCard title="موعد قادم" value="اليوم · 10:30" detail="د. X · طب القلب" icon={CalendarDays} onClick={() => onNavigate("appointments")} /><SummaryCard title="آخر النتائج" value="CBC · HbA1c" detail="عرض مقيد حسب العقد" icon={FlaskConical} onClick={() => onNavigate("lab-result")} /><SummaryCard title="إجراء مطلوب" value="مراجعة مشاركة" detail="الغرض والمدة واضحان" icon={Users} onClick={() => onNavigate("sharing")} /></div><PreviewPanel title="علي رضا · مرشد محلي" icon={Stethoscope}><p className="text-sm leading-7 text-muted-foreground">يمكنه شرح معنى Pending والتنقل إلى شاشة مناسبة، لكنه لا يقرأ قاعدة البيانات مباشرة ولا يطلق تشخيصاً أو قراراً طبياً.</p></PreviewPanel></div>;
}

function HealthTimelineScreen() {
  return <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]"><ClinicalTimeline events={[{ id: "e1", date: "25 Aug 2026", label: "Hospital · Discharge", description: "حدث اصطناعي ضمن المعرض.", status: "loaded" }, { id: "e2", date: "23 Aug 2026", label: "Laboratory · CBC", description: "نتيجة محكومة بالسياق.", status: "partial" }, { id: "e3", date: "20 Aug 2026", label: "Clinic Visit · Cardiology", status: "loaded" }, { id: "e4", date: "18 Aug 2026", label: "Prescription", description: "لا يعني العرض إمكانية صرف أو إعطاء.", status: "restricted" }]} /><PreviewPanel title="مرشحات التسلسل" icon={Activity}><div className="flex flex-wrap gap-2">{["الكل", "الزيارات", "المختبر", "الأشعة", "الأدوية", "الإجراءات", "الإدخال", "الإحالات"].map((filter) => <Badge key={filter} variant={filter === "الكل" ? "default" : "outline"}>{filter}</Badge>)}</div></PreviewPanel></div>;
}

function LabResultScreen() {
  return <div className="space-y-4"><CriticalAlertBanner title="نتيجة تحتاج إلى انتباه طبي" description="هذا تنبيه اصطناعي؛ راجع الطبيب المعالج ولا تستخدم الشاشة لتشخيص نفسك." /><PreviewPanel title="CBC · 25 Aug 2026" icon={FlaskConical}><div className="grid gap-3 sm:grid-cols-3"><ValueCard label="Hemoglobin" value="13.5" unit="g/dL" /><ValueCard label="WBC" value="7.2" unit="×10⁹/L" /><ValueCard label="Platelets" value="250" unit="×10⁹/L" /></div><div className="mt-4 flex flex-wrap gap-2"><Badge variant="outline">Value + Unit</Badge><Badge variant="outline">Reference Range</Badge><Badge variant="outline">Timestamp</Badge><Badge variant="outline">Source</Badge></div></PreviewPanel></div>;
}

function AppointmentsScreen() {
  return <PreviewPanel title="المواعيد" icon={CalendarDays}><div className="space-y-3"><ScheduleRow date="اليوم · 10:30" doctor="د. X" service="Cardiology" status="مؤكد" /><ScheduleRow date="غداً · 12:00" doctor="د. Y" service="Dermatology" status="بانتظار التأكيد" /></div><div className="mt-5 rounded-xl border border-indigo-200 bg-indigo-50/60 p-4 text-sm leading-6 text-indigo-950 dark:border-indigo-900/50 dark:bg-indigo-950/20 dark:text-indigo-200"><strong>الحجز:</strong> خدمة ← طبيب ← مؤسسة ← تاريخ ← وقت ← تأمين ← دفع إن وجد ← تأكيد. لا يوجد حجز حي في المعرض.</div></PreviewPanel>;
}

function SharingScreen() {
  return <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]"><PreviewPanel title="مشاركة بياناتي" icon={Users}><AccessRow name="Dr. X" scope="Lab + Imaging" expiry="Until 28 Aug" /><AccessRow name="عيادة اصطناعية" scope="ملخص الزيارة" expiry="48 ساعة" /><Button type="button" variant="outline" disabled>+ مشاركة جديدة · تتطلب Consent Contract</Button></PreviewPanel><ClinicalStatePanel state="forbidden" title="الإلغاء ليس محلياً" description="سحب المشاركة يجب أن يمر عبر عقد consent خادمي وسجل تدقيق غير قابل للتغيير." /></div>;
}

function SecurityScreen() {
  return <div className="grid gap-4 md:grid-cols-3"><MetricPanel title="MFA" value="Enabled" icon={ShieldCheck} tone="success" /><MetricPanel title="الأجهزة" value="2 Active" icon={KeyRound} tone="info" /><MetricPanel title="الجلسات" value="3 Active" icon={Activity} tone="warning" /><PreviewPanel title="مركز الأمان" icon={LockKeyhole}><FeatureLine label="الأجهزة" value="إدارة الأجهزة · محجوبة في المعرض" /><FeatureLine label="الجلسات" value="إنهاء جلسة · عقد خادمي مطلوب" /><FeatureLine label="سجل الوصول" value="Minimum disclosure + audit" /></PreviewPanel></div>;
}

function DoctorDashboardScreen({ onNavigate }: { onNavigate: (screen: ScreenKey) => void }) {
  return <div className="space-y-4"><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><MetricPanel title="Patients" value="18" icon={Users} tone="info" /><MetricPanel title="Waiting" value="4" icon={CalendarDays} tone="warning" /><MetricPanel title="Critical" value="1" icon={Siren} tone="critical" /><MetricPanel title="Follow-ups" value="6" icon={Activity} tone="success" /></div><div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]"><PreviewPanel title="My Patients" icon={Users}><PatientRow name="Patient A · اصطناعي" state="Encounter Active" onClick={() => onNavigate("patient-context")} /><PatientRow name="Patient B · اصطناعي" state="Follow-up" onClick={() => onNavigate("patient-context")} /><PatientRow name="Patient C · اصطناعي" state="Result Pending" onClick={() => onNavigate("patient-context")} /></PreviewPanel><PreviewPanel title="My Tasks" icon={ClipboardList}><FeatureLine label="3 Pending" value="لا إغلاق أو توقيع محلي" /><FeatureLine label="Results" value="5 New · 1 Critical" /><ClinicalStatePanel state="partial" title="Appointments" description="تحتاج Appointment Contract قبل العرض الحي." /></PreviewPanel></div></div>;
}

function PatientContextScreen() {
  return <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]"><PatientContextCard name="مريض اصطناعي · سارة عبد الرحمن" healthId="Health ID · DEMO-101" ageSex="34 سنة · أنثى" allergies={["Penicillin · مثال اصطناعي"]} criticalAlert="نتيجة اصطناعية تحتاج مراجعة الفريق." /><PreviewPanel title="Recent Encounters" icon={Activity}><FeatureLine label="Clinic Visit" value="20 Aug · Cardiology" /><FeatureLine label="Laboratory" value="23 Aug · CBC" /><FeatureLine label="Admission" value="محجوب في المعرض" /></PreviewPanel></div>;
}

function EncounterScreen() {
  return <div className="space-y-4"><PatientContextCard name="مريض Encounter اصطناعي" healthId="DEMO-ENCOUNTER-01" ageSex="سياق محدود" /><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{["Chief Complaint", "History", "Vitals", "Examination", "Assessment", "Plan"].map((step, index) => <div key={step} className="rounded-xl border p-4"><div className="flex items-center justify-between gap-2"><p className="font-semibold">{step}</p><ClinicalStatusBadge status={index < 2 ? "loaded" : "restricted"} label={index < 2 ? "معاينة" : "محجوب"} /></div><p className="mt-2 text-xs leading-5 text-muted-foreground">Section {index + 1} · لا كتابة محلية</p></div>)}</div><ClinicalStatePanel state="forbidden" title="بدء Encounter والتوقيع محجوبان" description="لا إنشاء أو تعديل أو Sign & Complete قبل Encounter Contract وauthorization وversion وaudit." /></div>;
}

function NurseDashboardScreen() {
  return <div className="space-y-4"><div className="rounded-2xl bg-slate-950 p-6 text-white"><p className="text-sm text-teal-200">Ward 3 · مساحة اصطناعية</p><h3 className="mt-2 text-3xl font-bold">لوحة الممرض</h3></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><MetricPanel title="Patients" value="24" icon={Users} tone="info" /><MetricPanel title="Tasks" value="9" icon={ClipboardList} tone="warning" /><MetricPanel title="Medications" value="6" icon={Pill} tone="critical" /><MetricPanel title="Alerts" value="1" icon={Siren} tone="critical" /></div><PreviewPanel title="Next" icon={CalendarDays}><ScheduleRow date="08:30" doctor="Medication" service="Verification required" status="محجوب" /><ScheduleRow date="08:45" doctor="Vitals" service="Versioned write" status="محجوب" /><ScheduleRow date="09:00" doctor="Handover" service="Receiving team" status="محجوب" /></PreviewPanel></div>;
}

function NursePatientScreen() {
  return <div className="space-y-4"><PatientContextCard name="مريض تمريض اصطناعي" healthId="DEMO-NURSE-02" ageSex="سياق جناح محدود" /><div className="grid gap-4 md:grid-cols-2"><PreviewPanel title="Vitals" icon={HeartPulse}><ValueCard label="Blood Pressure" value="120/80" unit="mmHg" /><ValueCard label="Pulse" value="72" unit="bpm" /><ValueCard label="SpO₂" value="98" unit="%" /></PreviewPanel><PreviewPanel title="Medication Administration" icon={Pill}><ClinicalStatePanel state="forbidden" title="Verify / Administer محجوب" description="تحتاج العملية Patient + Drug + Dose + Route + Time + two-step authorization + audit." /></PreviewPanel></div></div>;
}

function LabDashboardScreen() {
  return <div className="space-y-4"><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"><MetricPanel title="Orders" value="182" icon={ClipboardList} tone="info" /><MetricPanel title="Pending" value="34" icon={Activity} tone="warning" /><MetricPanel title="Processing" value="51" icon={Microscope} tone="info" /><MetricPanel title="Validation" value="12" icon={FileCheck2} tone="warning" /><MetricPanel title="Critical" value="2" icon={Siren} tone="critical" /></div><div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]"><PreviewPanel title="Analyzer Status" icon={Microscope}><FeatureLine label="CBC" value="جاهز · اصطناعي" /><FeatureLine label="Chemistry" value="جاهز · اصطناعي" /><FeatureLine label="Analyzer 3" value="تحذير · Demo" /></PreviewPanel><ClinicalStatePanel state="partial" title="QC وValidation" description="العقد الحالي لا يفتح اعتماد نتيجة أو تشغيل محلل من الواجهة." /></div></div>;
}

function LabWorklistScreen() {
  return <PreviewPanel title="Lab Worklist" icon={ClipboardList}><div className="hidden overflow-x-auto md:block"><table className="w-full text-right text-sm"><thead><tr className="border-b text-xs text-muted-foreground"><th className="p-3">Specimen</th><th className="p-3">Patient</th><th className="p-3">Test</th><th className="p-3">Priority</th><th className="p-3">Status</th></tr></thead><tbody>{[["SYN-001", "Patient A", "CBC", "STAT", "Processing"], ["SYN-002", "Patient B", "HbA1c", "Routine", "Pending"], ["SYN-003", "TEMP-000123", "Chemistry", "Urgent", "Received"]].map((row) => <tr key={row[0]} className="border-b last:border-0">{row.map((cell) => <td key={cell} className="p-3">{cell}</td>)}</tr>)}</tbody></table></div><div className="space-y-2 md:hidden">{["SYN-001 · CBC · STAT", "SYN-002 · HbA1c · Routine", "SYN-003 · Chemistry · Urgent"].map((row) => <div key={row} className="rounded-xl border p-3 text-sm">{row}</div>)}</div><ClinicalStatePanel state="forbidden" title="Result Validation محجوب" description="لا Validate أو Notify أو Document قبل specimen verification وsenior authorization وaudit." /></PreviewPanel>;
}

function PharmacyDashboardScreen() {
  return <div className="space-y-4"><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"><MetricPanel title="New Orders" value="31" icon={ClipboardList} tone="info" /><MetricPanel title="Verification" value="12" icon={ShieldCheck} tone="warning" /><MetricPanel title="Ready" value="18" icon={CheckCircle2} tone="success" /><MetricPanel title="Inventory Alerts" value="4" icon={Pill} tone="critical" /><MetricPanel title="Expiry Alerts" value="3" icon={Activity} tone="warning" /></div><PreviewPanel title="Pharmacy workflow" icon={Pill}><FeatureLine label="Prescription" value="Received → Verified → Ready" /><FeatureLine label="Dispensing" value="محجوب في Live الحالي" /><FeatureLine label="Administration" value="مسار سريري مختلف" /></PreviewPanel></div>;
}

function PharmacyVerificationScreen() {
  return <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]"><PreviewPanel title="Prescription Verification" icon={ShieldCheck}><FeatureLine label="Patient" value="مريض اصطناعي ضمن السياق" /><FeatureLine label="Medication" value="Drug Y · Demo" /><FeatureLine label="Dose / Route" value="Z · Oral" /><FeatureLine label="Interactions" value="Review required" /><FeatureLine label="Allergy" value="Check required" /></PreviewPanel><ClinicalStatePanel state="forbidden" title="Approve / Reject / Dispense محجوب" description="تحتاج الوصفة للتحقق، والتكرار، والحساسية، والمخزون، والدفعة، والصلاحية، والتدقيق قبل أي كتابة." /></div>;
}

function HospitalDashboardScreen() {
  return <div className="space-y-4"><div className="rounded-2xl bg-slate-950 p-6 text-white"><p className="text-sm text-teal-200">Hospital X · Synthetic</p><h3 className="mt-2 text-3xl font-bold">لوحة تشغيل المستشفى</h3></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"><MetricPanel title="Emergency" value="3 critical" icon={Siren} tone="critical" /><MetricPanel title="Waiting" value="17" icon={Users} tone="warning" /><MetricPanel title="Beds" value="42" icon={Hospital} tone="success" /><MetricPanel title="ICU" value="2" icon={HeartPulse} tone="warning" /><MetricPanel title="Blood Bank" value="2 alerts" icon={Activity} tone="critical" /></div><ClinicalStatePanel state="partial" title="التشغيل الحي محدود" description="patients/orders فقط بعد workspace context؛ الإدخال والأسرة وOR وICU والدم والخروج محجوبة." /></div>;
}

function BedManagementScreen() {
  return <div className="grid gap-4 md:grid-cols-3"><OccupancyCard label="Ward A" value="80%" /><OccupancyCard label="Ward B" value="65%" /><OccupancyCard label="ICU" value="90%" critical /><PreviewPanel title="Bed Detail · A-12" icon={Hospital}><FeatureLine label="Status" value="Occupied · اصطناعي" /><FeatureLine label="Patient" value="سياق محجوب" /><FeatureLine label="Isolation" value="Policy required" /><ClinicalStatePanel state="forbidden" title="Assign / Transfer محجوب" description="Bed allocation يحتاج ward scope وIf-Match وIdempotency-Key وaudit." /></PreviewPanel></div>;
}

function EmergencyDashboardScreen() {
  return <div className="space-y-4"><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><MetricPanel title="Critical" value="3" icon={Siren} tone="critical" /><MetricPanel title="Very Urgent" value="5" icon={Activity} tone="warning" /><MetricPanel title="Urgent" value="8" icon={HeartPulse} tone="warning" /><MetricPanel title="Waiting" value="17" icon={Users} tone="info" /></div><div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]"><PreviewPanel title="Emergency Patient Card" icon={Siren}><PatientRow name="Patient X · اصطناعي" state="Immediate · Arrival 12:15" /><ClinicalStatusBadge status="critical" label="Critical Alert" /><ClinicalStatePanel state="forbidden" title="Open Encounter محجوب" description="الفرز لا يساوي التشخيص، وفتح Encounter أو Break-Glass يحتاج خادماً وسياقاً وتدقيقاً." /></PreviewPanel><PreviewPanel title="Resus / Observation" icon={HeartPulse}><FeatureLine label="Resus" value="1" /><FeatureLine label="Observation" value="7" /><FeatureLine label="Handover" value="Acceptance required" /></PreviewPanel></div></div>;
}

function AmbulanceAppScreen() {
  return <div className="rounded-3xl bg-slate-950 p-6 text-white sm:p-9"><div className="flex items-center justify-between gap-3"><Badge className="border-rose-300/30 bg-rose-500/15 text-rose-100"><Siren className="ml-1 h-3.5 w-3.5" />ACTIVE INCIDENT · SYN</Badge><Badge className="border-white/15 bg-white/10 text-white">Demo</Badge></div><h3 className="mt-8 text-3xl font-bold">حادث اصطناعي · Patient Unknown</h3><p className="mt-2 text-sm text-slate-300">Location غير حقيقي · Priority Critical · أقل عدد من اللمسات أثناء الحركة.</p><div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{["Arrived", "Assess", "Vitals", "Interventions", "Hospital", "Handover"].map((action) => <button key={action} type="button" className="gula-touch-target rounded-2xl border border-white/15 bg-white/[0.07] p-4 text-right text-sm font-semibold text-white/90 transition hover:bg-white/[0.12]"><span className="block">{action}</span><span className="mt-1 block text-xs text-slate-400">معاينة فقط · لا يحفظ</span></button>)}</div><div className="mt-6 rounded-2xl border border-amber-200/20 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100"><LockKeyhole className="ml-2 inline h-4 w-4" />لا GPS أو Dispatch أو ePCR أو Vital write في المعرض.</div></div>;
}

function IcuDashboardScreen() {
  return <div className="space-y-4"><PreviewPanel title="ICU Dashboard" icon={HeartPulse}><div className="grid gap-3 md:grid-cols-3"><IcuBed bed="Bed 01" patient="Patient X" status="critical" /><IcuBed bed="Bed 02" patient="Patient Y" status="safe" /><IcuBed bed="Bed 03" patient="Available" status="empty" /></div></PreviewPanel><div className="grid gap-4 md:grid-cols-2"><PreviewPanel title="SpO₂ Trend · اصطناعي" icon={Activity}><div className="flex h-32 items-end gap-2 rounded-xl border bg-slate-50 p-4 dark:bg-white/5">{[42, 58, 52, 68, 61, 78, 72, 84, 75, 88].map((height, index) => <span key={index} className="flex-1 rounded-t bg-teal-500/70" style={{ height: `${height}%` }} />)}</div><p className="mt-2 text-xs text-muted-foreground">الرسم لا يعتمد على اللون وحده؛ القيم والوحدة والوقت والمصدر مطلوبة.</p></PreviewPanel><ClinicalStatePanel state="forbidden" title="Ventilation / Infusions / Telemetry محجوبة" description="لا Device Gateway أو ICU flowsheet raw reads بلا عقد مخصص ونطاق منشأة." /></div></div>;
}

function AdminDashboardScreen() {
  return <div className="space-y-4"><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><MetricPanel title="Facilities" value="12" icon={Hospital} tone="info" /><MetricPanel title="Capacity" value="78%" icon={Activity} tone="success" /><MetricPanel title="Quality" value="94%" icon={CheckCircle2} tone="success" /><MetricPanel title="Security" value="2 alerts" icon={ShieldCheck} tone="critical" /></div><div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]"><PreviewPanel title="Operational Dashboard" icon={LayoutDashboard}><FeatureLine label="Organization" value="12 منشأة اصطناعية" /><FeatureLine label="Services" value="مفصولة عن National Analytics" /><FeatureLine label="Policies" value="Server authority" /></PreviewPanel><ClinicalStatePanel state="forbidden" title="Audit وUser Management محجوبان" description="لا تعيين دور أو دعوة أو تغيير سياسة أو قراءة Audit شامل من المعرض." /></div></div>;
}

function AuditViewerScreen() {
  return <PreviewPanel title="Audit Viewer" icon={FileCheck2}><div className="hidden overflow-x-auto md:block"><table className="w-full text-right text-sm"><thead><tr className="border-b text-xs text-muted-foreground"><th className="p-3">User</th><th className="p-3">Action</th><th className="p-3">Resource</th><th className="p-3">Timestamp</th><th className="p-3">Result</th></tr></thead><tbody>{[["Doctor A", "Viewed Lab Result", "SYN-RESULT-01", "12:31", "Allowed"], ["Nurse B", "Updated Vitals", "SYN-VITAL-02", "12:45", "Pending review"], ["System", "Access denied", "SYN-PATIENT-03", "12:47", "Rejected"]].map((row) => <tr key={row[2]} className="border-b last:border-0">{row.map((cell) => <td key={cell} className="p-3">{cell}</td>)}</tr>)}</tbody></table></div><ClinicalStatePanel state="forbidden" title="تفاصيل Audit الحية محجوبة" description="السجل الحقيقي يحتاج endpoint purpose-limited وpagination وminimum disclosure وauthorization." /></PreviewPanel>;
}

function WebPortalScreen({ onNavigate }: { onNavigate: (screen: ScreenKey) => void }) {
  return <div className="space-y-4"><div className="rounded-2xl bg-gradient-to-l from-teal-700 to-slate-950 p-7 text-white"><p className="text-sm text-teal-100">GULA</p><h3 className="mt-2 text-3xl font-bold">صحة رقمية موحدة</h3><p className="mt-2 text-sm text-slate-300">بوابة الويب ليست نسخة من التطبيق؛ تكتشف الخدمات وتوصل المستخدم إلى المسار المناسب.</p><div className="mt-5 flex flex-col gap-2 sm:flex-row"><div className="flex flex-1 items-center gap-2 rounded-xl bg-white/10 px-3"><Search className="h-4 w-4" /><span className="text-sm text-slate-300">طبيب / مستشفى / مختبر / صيدلية / خدمة</span></div><Button type="button" onClick={() => onNavigate("login")}>تسجيل الدخول</Button></div></div><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{["الأطباء", "العيادات", "المستشفيات", "المختبرات", "الصيدليات", "الأشعة", "الطوارئ", "التأمين"].map((service) => <div key={service} className="gula-interactive-surface p-4"><p className="font-semibold">{service}</p><p className="mt-1 text-xs text-muted-foreground">يظهر عند توفر capability</p></div>)}</div></div>;
}

function DesktopWorkspaceScreen() {
  return <div className="grid gap-4 lg:grid-cols-[16rem_minmax(0,1fr)]"><PreviewPanel title="Sidebar" icon={Menu}><FeatureLine label="Dashboard" value="ثابت" /><FeatureLine label="Patients" value="ضمن الصلاحية" /><FeatureLine label="Orders" value="Server pagination" /><FeatureLine label="Results" value="Scoped" /></PreviewPanel><PreviewPanel title="Main Workspace · Master / Detail" icon={LayoutDashboard}><div className="grid gap-3 md:grid-cols-2"><div className="space-y-2"><p className="text-xs font-bold text-muted-foreground">Master · 100,000+ records</p>{["Order SYN-001", "Order SYN-002", "Order SYN-003"].map((item) => <div key={item} className="rounded-xl border p-3 text-sm">{item}</div>)}<Badge variant="outline">Server-side pagination</Badge></div><div><p className="text-xs font-bold text-muted-foreground">Detail · restricted context</p><ClinicalStatePanel state="partial" title="اختر عنصراً ضمن النطاق" description="لا نحمّل السجل الصحي كاملاً ولا نعرض raw data في الـDOM." /></div></div></PreviewPanel></div>;
}

function CenteredAuthScreen({ icon: Icon, title, description, children }: { icon: LucideIcon; title: string; description: string; children: ReactNode }) {
  return <div className="mx-auto max-w-xl"><Card><CardContent className="space-y-5 p-7 text-center sm:p-10"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Icon className="h-7 w-7" /></span><h3 className="text-2xl font-bold">{title}</h3><p className="text-sm leading-7 text-muted-foreground">{description}</p>{children}</CardContent></Card></div>;
}

function PreviewPanel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: ReactNode }) {
  return <Card className="gula-interactive-surface"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Icon className="h-5 w-5 text-primary" />{title}</CardTitle></CardHeader><CardContent className="space-y-3">{children}</CardContent></Card>;
}

function PreviewMetric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-white/10 bg-white/[0.08] p-3"><p className="text-xs text-slate-300">{label}</p><p className="mt-1 text-2xl font-bold">{value}</p></div>;
}

function SummaryCard({ title, value, detail, icon: Icon, onClick }: { title: string; value: string; detail: string; icon: LucideIcon; onClick: () => void }) {
  return <button type="button" onClick={onClick} className="gula-interactive-surface gula-focus-ring p-5 text-right"><Icon className="h-5 w-5 text-primary" /><p className="mt-4 text-sm text-muted-foreground">{title}</p><p className="mt-1 font-bold">{value}</p><p className="mt-1 text-xs text-muted-foreground">{detail}</p></button>;
}

function MetricPanel({ title, value, icon: Icon, tone }: { title: string; value: string; icon: LucideIcon; tone: "critical" | "warning" | "success" | "info" }) {
  const classes = { critical: "border-rose-200 bg-rose-50/70 dark:border-rose-900/50 dark:bg-rose-950/20", warning: "border-amber-200 bg-amber-50/70 dark:border-amber-900/50 dark:bg-amber-950/20", success: "border-emerald-200 bg-emerald-50/70 dark:border-emerald-900/50 dark:bg-emerald-950/20", info: "border-sky-200 bg-sky-50/70 dark:border-sky-900/50 dark:bg-sky-950/20" };
  return <div className={`rounded-2xl border p-5 ${classes[tone]}`}><Icon className="h-5 w-5" /><p className="mt-4 text-sm text-muted-foreground">{title}</p><p className="mt-1 text-2xl font-bold">{value}</p></div>;
}

function FeatureLine({ label, value, inverse = false }: { label: string; value: string; inverse?: boolean }) {
  return <div className={`flex items-center justify-between gap-3 rounded-xl border p-3 text-sm ${inverse ? "border-white/10 bg-white/[0.06]" : ""}`}><span className={inverse ? "text-white/75" : "text-muted-foreground"}>{label}</span><span className={`text-left font-semibold ${inverse ? "text-white" : ""}`}>{value}</span></div>;
}

function ValueCard({ label, value, unit }: { label: string; value: string; unit: string }) {
  return <div className="rounded-xl border bg-muted/20 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-2 text-2xl font-bold">{value}</p><p className="mt-1 text-xs font-semibold text-primary">{unit}</p></div>;
}

function ScheduleRow({ date, doctor, service, status }: { date: string; doctor: string; service: string; status: string }) {
  return <div className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">{date} · {doctor}</p><p className="mt-1 text-xs text-muted-foreground">{service}</p></div><ClinicalStatusBadge status={status === "مؤكد" ? "safe" : status === "محجوب" ? "restricted" : "partial"} label={status} /></div>;
}

function AccessRow({ name, scope, expiry }: { name: string; scope: string; expiry: string }) {
  return <div className="flex items-center justify-between gap-3 rounded-xl border p-4"><div><p className="font-semibold">{name}</p><p className="mt-1 text-xs text-muted-foreground">{scope}</p></div><div className="text-left"><p className="text-xs text-muted-foreground">{expiry}</p><Badge variant="outline">مشاركة</Badge></div></div>;
}

function PatientRow({ name, state, onClick }: { name: string; state: string; onClick?: () => void }) {
  return <button type="button" onClick={onClick} className="gula-focus-ring flex w-full items-center justify-between gap-3 rounded-xl border p-4 text-right transition hover:border-primary/40 hover:bg-primary/5"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary"><UserCircle className="h-4 w-4" /></span><div><p className="font-semibold">{name}</p><p className="mt-1 text-xs text-muted-foreground">{state}</p></div></div><ArrowLeft className="h-4 w-4 text-muted-foreground" /></button>;
}

function OccupancyCard({ label, value, critical = false }: { label: string; value: string; critical?: boolean }) {
  return <div className={`rounded-2xl border p-5 ${critical ? "border-rose-200 bg-rose-50/70 dark:border-rose-900/50 dark:bg-rose-950/20" : "gula-interactive-surface"}`}><div className="flex items-center justify-between gap-2"><p className="font-semibold">{label}</p><ClinicalStatusBadge status={critical ? "critical" : "safe"} label={critical ? "مرتفع" : "مستقر"} /></div><p className="mt-5 text-3xl font-bold">{value}</p><div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-white/10"><div className={`h-full rounded-full ${critical ? "bg-rose-500" : "bg-teal-500"}`} style={{ width: value }} /></div></div>;
}

function IcuBed({ bed, patient, status }: { bed: string; patient: string; status: "critical" | "safe" | "empty" }) {
  return <div className="rounded-xl border p-4"><div className="flex items-center justify-between gap-2"><p className="font-bold">{bed}</p><ClinicalStatusBadge status={status === "critical" ? "critical" : status === "safe" ? "safe" : "empty"} label={status === "critical" ? "حرج" : status === "safe" ? "مستقر" : "متاح"} /></div><p className="mt-4 text-sm text-muted-foreground">{patient}</p></div>;
}

export { ROLE_DEFINITIONS };
