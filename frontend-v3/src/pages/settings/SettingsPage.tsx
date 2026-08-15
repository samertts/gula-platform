import { useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Accessibility,
  Bell,
  BriefcaseBusiness,
  CircleHelp,
  Cog,
  FileKey2,
  HeartPulse,
  Languages,
  LockKeyhole,
  MonitorSmartphone,
  Palette,
  ShieldCheck,
  UserRound,
  UsersRound,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui";
import { useAccessibility } from "@/contexts/AccessibilityContext";
import { useLocale } from "@/contexts/LocaleContext";
import { localeOptions, type Locale } from "@/i18n/locales";
import { AdaptiveStateBadge, AdaptiveStatus, type AdaptiveState } from "@/components/accessibility/AdaptiveComponents";
import { HealthPreferencesPanel } from "./SettingsPageLegacy";

type SettingsSection = {
  id: string;
  title: string;
  english: string;
  description: string;
  icon: LucideIcon;
  state: AdaptiveState;
  path?: string;
  note?: string;
};

const settingsSections: SettingsSection[] = [
  { id: "account", title: "الحساب", english: "Account", description: "الاسم والبريد ونقطة البداية لحسابك.", icon: UserRound, state: "enabled", path: "/profile" },
  { id: "identity", title: "الهوية", english: "Identity", description: "الملف المؤسسي والهوية المرتبطة بالجلسة الحالية.", icon: FileKey2, state: "enabled", path: "/profile" },
  { id: "language", title: "اللغة", english: "Language", description: "لغة الواجهة واتجاه القراءة، مع بيان تغطية الترجمة.", icon: Languages, state: "enabled" },
  { id: "appearance", title: "المظهر", english: "Appearance", description: "Clinical Clarity والتباين والحركة وحجم النص.", icon: Palette, state: "enabled", path: "/settings/accessibility#display-profile" },
  { id: "accessibility", title: "إمكانية الوصول", english: "Accessibility", description: "مركز موحد للعرض والسمع والحركة والقراءة والتواصل.", icon: Accessibility, state: "enabled", path: "/settings/accessibility" },
  { id: "health", title: "التفضيلات الصحية", english: "Health Preferences", description: "بيانات اختيارية حساسة، خلف موافقة صريحة وتشفير وتدقيق.", icon: HeartPulse, state: "consent_required", path: "#health-preferences" },
  { id: "privacy", title: "الخصوصية", english: "Privacy", description: "شرح سياسة الخصوصية والحدود المعتمدة للمنصة.", icon: LockKeyhole, state: "enabled", path: "/privacy-policy" },
  { id: "security", title: "الأمان", english: "Security", description: "الضوابط الأمنية الموجودة؛ بعض أدوات الإدارة مقيدة بالدور.", icon: ShieldCheck, state: "enabled", path: "/security", note: "RoleGuard يفرض الصلاحية من Backend." },
  { id: "notifications", title: "الإشعارات", english: "Notifications", description: "قواعد الإشعارات التفصيلية تحتاج عقدًا خلفيًا موحدًا.", icon: Bell, state: "unavailable", note: "BACKEND_DEPENDENCY: لا توجد واجهة API موحدة حاليًا." },
  { id: "devices", title: "الأجهزة والجلسات", english: "Devices / Sessions", description: "إدارة الجلسات النشطة والأجهزة الموثوقة.", icon: MonitorSmartphone, state: "unavailable", note: "BACKEND_DEPENDENCY: لا يتم اختراع endpoint لإدارة الجلسات." },
  { id: "workspaces", title: "مساحات العمل", english: "Workspaces", description: "اختيار نطاق العمل والفرق المرتبطة بالمستخدم.", icon: BriefcaseBusiness, state: "unavailable", note: "BACKEND_DEPENDENCY: يعرض الوضع الآمن بدل بيانات وهمية." },
  { id: "memberships", title: "العضويات", english: "Memberships", description: "العضويات والدعوات والصلاحيات المؤسسية.", icon: UsersRound, state: "unavailable", note: "BACKEND_DEPENDENCY: إدارة العضوية تبقى عبر IAM الحالي." },
  { id: "services", title: "الخدمات", english: "Services", description: "التكاملات والخدمات المتصلة بالمنصة.", icon: Wrench, state: "unavailable", note: "BACKEND_DEPENDENCY: لا توجد تكاملات جديدة دون مراجعة أمنية." },
  { id: "help", title: "المساعدة", english: "Help", description: "الدعم والتوثيق وسياسة الإبلاغ عن المشكلات.", icon: CircleHelp, state: "unavailable", note: "BACKEND_DEPENDENCY: مسار الدعم الموحد غير متاح في هذا الإصدار." },
];

function SectionCard({ section }: { section: SettingsSection }) {
  const Icon = section.icon;
  const content = (
    <CardContent className="flex h-full flex-col gap-4 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-[#0D9488] dark:bg-teal-950/40 dark:text-teal-300">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
        <AdaptiveStateBadge state={section.state} />
      </div>
      <div>
        <div className="flex flex-wrap items-baseline gap-2"><h2 className="text-base font-bold text-[#0F172A] dark:text-white">{section.title}</h2><span className="text-xs font-semibold text-muted-foreground">{section.english}</span></div>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{section.description}</p>
      </div>
      {section.note && <p className="mt-auto rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300">{section.note}</p>}
      {section.path && section.state === "enabled" && <span className="mt-auto text-sm font-bold text-teal-700 dark:text-teal-300">فتح القسم ←</span>}
    </CardContent>
  );

  if (section.path && section.state === "enabled") {
    return <Link to={section.path} className="block h-full rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-teal-600"><Card className="h-full border-slate-200/80 transition-transform hover:-translate-y-0.5 hover:border-teal-200 dark:border-white/10 dark:hover:border-teal-900/70">{content}</Card></Link>;
  }
  return <Card className="h-full border-slate-200/80 dark:border-white/10">{content}</Card>;
}

export function SettingsPage() {
  const { preferences } = useAccessibility();
  const { locale, setLocale } = useLocale();
  const readyCount = useMemo(() => settingsSections.filter((section) => section.state === "enabled").length, []);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="rounded-[1.75rem] border border-slate-200/80 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-white/10 dark:bg-slate-900/70 sm:p-7">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-bold text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"><Cog className="h-4 w-4 text-[#0D9488]" aria-hidden="true" /> Unified Settings & Personalization</div>
            <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">مركز الإعدادات والتخصيص</h1>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">إدارة الحساب واللغة والمظهر وإمكانية الوصول والاحتياجات الصحية من مكان واحد. كل قسم يعلن بوضوح إن كان جاهزًا أو يحتاج عقدًا خلفيًا، ولا يتم اختراع بيانات أو صلاحيات غير موجودة.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2"><AdaptiveStateBadge state="enabled" /><span className="rounded-full border border-slate-200 px-3 py-1 text-xs text-muted-foreground dark:border-white/10">{readyCount}/{settingsSections.length} أقسام جاهزة</span></div>
        </div>
      </header>

      <Card className="border-teal-100 bg-teal-50/50 dark:border-teal-900/50 dark:bg-teal-950/20">
        <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
          <div className="flex items-start gap-3"><Languages className="mt-0.5 h-5 w-5 shrink-0 text-teal-700 dark:text-teal-300" aria-hidden="true" /><div><h2 className="text-base font-bold text-teal-950 dark:text-teal-100">اللغة واتجاه القراءة</h2><p className="mt-1 text-sm leading-6 text-teal-900/75 dark:text-teal-100/75">يدعم النظام اللغات الخمس المعتمدة: العربية والإنجليزية والكردية والتركمانية والسريانية، مع تطبيق اتجاه القراءة وفق اللغة المختارة.</p></div></div>
          <label className="flex min-w-56 flex-col gap-2 text-sm font-bold text-[#0F172A] dark:text-white"><span>اللغة الحالية: {locale}</span><select value={locale} onChange={(event) => setLocale(event.target.value as Locale)} className="min-h-11 rounded-xl border border-teal-200 bg-white px-3 dark:border-teal-900/60 dark:bg-slate-950">{localeOptions.map((option) => <option key={option.code} value={option.code}>{option.nativeName} · {option.code}</option>)}</select></label>
        </CardContent>
      </Card>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Settings categories">
        {settingsSections.map((section) => <SectionCard key={section.id} section={section} />)}
      </section>

      <div id="health-preferences" className="scroll-mt-6">
        <AdaptiveStatus state="consent_required" label="Health Preferences protected" description="يتم عرض القسم الحالي أدناه. لا يُحفظ أي محتوى صحي دون موافقة صريحة، ولا يُستخدم للتشخيص أو لتغيير صلاحيات الوصول." />
        <div className="mt-4"><HealthPreferencesPanel /></div>
      </div>

      <Card className="border-sky-100 bg-sky-50/50 dark:border-sky-900/50 dark:bg-sky-950/20">
        <CardContent className="flex items-start gap-3 p-5 sm:p-6"><Palette className="mt-0.5 h-5 w-5 shrink-0 text-sky-700 dark:text-sky-300" aria-hidden="true" /><div><h2 className="text-sm font-bold text-sky-950 dark:text-sky-100">Clinical Clarity guardrail</h2><p className="mt-1 text-sm leading-6 text-sky-900/75 dark:text-sky-100/75">المظهر وإمكانية الوصول يغيران طريقة العرض والتفاعل فقط. لا يتم تخزين البيانات الصحية محليًا، ولا تستطيع الواجهة تجاوز RoleGuard أو workspace-scoped authorization.</p><p className="mt-2 text-xs text-sky-900/65 dark:text-sky-100/65">Saved accessibility profile: {preferences.language} · text scale {preferences.text_scale.toFixed(2)}×</p></div></CardContent>
      </Card>
    </div>
  );
}
