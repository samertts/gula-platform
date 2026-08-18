import { useEffect, useMemo, useState } from "react";
import {
  Accessibility,
  AlertTriangle,
  CheckCircle2,
  Eye,
  Headphones,
  HeartPulse,
  Keyboard,
  Languages,
  LockKeyhole,
  MousePointer2,
  Palette,
  RotateCcw,
  Save,
  Shield,
  SlidersHorizontal,
  Sparkles,
  Volume2,
  type LucideIcon,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { userPreferencesApi } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { useAccessibility } from "@/contexts/AccessibilityContext";
import type { AccessibilityPreferences, HealthPreferencesPayload, HealthPreferencesResponse } from "@/types";

function ToggleRow({
  checked,
  label,
  description,
  onChange,
}: {
  checked: boolean;
  label: string;
  description: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-start justify-between gap-4 rounded-2xl border border-slate-200/80 bg-white/70 p-4 transition-colors hover:border-teal-200 hover:bg-teal-50/30 dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-teal-900/70">
      <span className="min-w-0">
        <span className="block text-sm font-bold text-[#0F172A] dark:text-white">{label}</span>
        <span className="mt-1 block text-xs leading-5 text-muted-foreground">{description}</span>
      </span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-1 h-5 w-5 shrink-0 accent-teal-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600"
      />
    </label>
  );
}

function SectionCard({
  icon: Icon,
  title,
  description,
  children,
}: {
  icon: typeof Accessibility;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="border-slate-200/80 bg-white/95 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.5)] dark:border-white/10 dark:bg-slate-900/75">
      <CardContent className="space-y-4 p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-[#0D9488] dark:bg-teal-950/40 dark:text-teal-300">
            <Icon className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-base font-bold text-[#0F172A] dark:text-white">{title}</h2>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p>
          </div>
        </div>
        {children}
      </CardContent>
    </Card>
  );
}

export function HealthPreferencesPanel() {
  const { isAuthenticated, isLoading: authLoading, demoMode } = useAuth();
  const [health, setHealth] = useState<HealthPreferencesResponse>({ status: "empty", consent_granted: false });
  const [draft, setDraft] = useState<HealthPreferencesPayload>({
    allergies: [],
    chronic_conditions: [],
    communication_needs: null,
    emergency_assistance_preferences: null,
    other_health_considerations: null,
  });
  const [allergiesText, setAllergiesText] = useState("");
  const [conditionsText, setConditionsText] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!isAuthenticated || demoMode) return;
    try {
      const response = await userPreferencesApi.getHealth();
      setHealth(response);
      if (response.preferences) {
        setDraft(response.preferences);
        setAllergiesText(response.preferences.allergies.join(", "));
        setConditionsText(response.preferences.chronic_conditions.join(", "));
      }
    } catch {
      setError("تعذر تحميل تفضيلات الاحتياجات الصحية. لم يتم تغيير أي بيانات.");
    }
  };

  useEffect(() => {
    if (!authLoading) void load();
  }, [authLoading, demoMode, isAuthenticated]);

  const save = async () => {
    if (!consent) {
      setError("يجب تأكيد الموافقة الصريحة قبل حفظ الاحتياجات الصحية.");
      return;
    }
    setBusy(true);
    setMessage(null);
    setError(null);
    const next: HealthPreferencesPayload = {
      ...draft,
      allergies: allergiesText.split(",").map((item) => item.trim()).filter(Boolean),
      chronic_conditions: conditionsText.split(",").map((item) => item.trim()).filter(Boolean),
    };
    try {
      const response = await userPreferencesApi.updateHealth({
        preferences: next,
        consent: true,
        consent_version: "health-preferences-v1",
        ...(health.version ? { version: health.version } : {}),
      });
      setHealth(response);
      setDraft(next);
      setConsent(false);
      setMessage("تم حفظ البيانات الصحية الحساسة مشفّرة وبموافقتك فقط.");
    } catch {
      setError("تعذر الحفظ. قد تكون البيانات تغيّرت؛ أعد التحميل ثم حاول مرة أخرى.");
    } finally {
      setBusy(false);
    }
  };

  const revoke = async () => {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const response = await userPreferencesApi.revokeHealth();
      setHealth(response);
      setDraft({ allergies: [], chronic_conditions: [], communication_needs: null, emergency_assistance_preferences: null, other_health_considerations: null });
      setAllergiesText("");
      setConditionsText("");
      setMessage("تم سحب الموافقة وحذف المحتوى الصحي المشفّر.");
    } catch {
      setError("تعذر سحب الموافقة. لم يتم تغيير البيانات.");
    } finally {
      setBusy(false);
    }
  };

  if (demoMode) {
    return (
      <SectionCard icon={HeartPulse} title="الاحتياجات الصحية الشخصية" description="هذه المنطقة لا تعمل في الوضع التجريبي ولا تستخدم بيانات صحية وهمية.">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-100">البيانات الصحية الحساسة متاحة فقط في جلسة حقيقية موثّقة.</div>
      </SectionCard>
    );
  }

  return (
    <SectionCard icon={HeartPulse} title="الاحتياجات الصحية الشخصية" description="اختيارات اختيارية يحددها المستخدم بنفسه؛ لا تمثل تشخيصًا ولا تمنح صلاحيات ولا تُشارك تلقائيًا.">
      <div className="flex items-start gap-3 rounded-2xl border border-rose-100 bg-rose-50/70 p-4 text-sm leading-6 text-rose-950 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-100">
        <LockKeyhole className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
        <p>لا تُحفظ هذه البيانات إلا بعد موافقة صريحة، وتُخزّن مشفّرة، ولا تظهر للمختبر أو الطبيب أو أي مستخدم آخر تلقائيًا.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white">
          <span>الحساسيات — افصل بين العناصر بفواصل</span>
          <input value={allergiesText} onChange={(event) => setAllergiesText(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none ring-teal-500 focus:ring-2 dark:border-white/10 dark:bg-slate-950" placeholder="اختياري" />
        </label>
        <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white">
          <span>الحالات المزمنة — يحددها المستخدم فقط</span>
          <input value={conditionsText} onChange={(event) => setConditionsText(event.target.value)} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none ring-teal-500 focus:ring-2 dark:border-white/10 dark:bg-slate-950" placeholder="اختياري" />
        </label>
      </div>
      <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white">
        <span>احتياجات التواصل</span>
        <textarea value={draft.communication_needs ?? ""} onChange={(event) => setDraft((current) => ({ ...current, communication_needs: event.target.value || null }))} className="min-h-24 w-full rounded-xl border border-slate-200 bg-white p-3 text-sm outline-none ring-teal-500 focus:ring-2 dark:border-white/10 dark:bg-slate-950" placeholder="اختياري" />
      </label>
      <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white">
        <span>قد أحتاج إلى مساعدة إضافية</span>
        <textarea value={draft.emergency_assistance_preferences ?? ""} onChange={(event) => setDraft((current) => ({ ...current, emergency_assistance_preferences: event.target.value || null }))} className="min-h-24 w-full rounded-xl border border-slate-200 bg-white p-3 text-sm outline-none ring-teal-500 focus:ring-2 dark:border-white/10 dark:bg-slate-950" placeholder="أنواع المساعدة التي تختار حفظها لنفسك، اختياري" />
      </label>
      <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white">
        <span>اعتبارات صحية أخرى</span>
        <textarea value={draft.other_health_considerations ?? ""} onChange={(event) => setDraft((current) => ({ ...current, other_health_considerations: event.target.value || null }))} className="min-h-24 w-full rounded-xl border border-slate-200 bg-white p-3 text-sm outline-none ring-teal-500 focus:ring-2 dark:border-white/10 dark:bg-slate-950" placeholder="اختياري" />
      </label>
      <label className="flex items-start gap-3 rounded-2xl border border-slate-200 p-4 text-sm leading-6 dark:border-white/10">
        <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} className="mt-1 h-5 w-5 accent-teal-600" />
        <span>أوافق صراحة على حفظ هذه المعلومات الصحية الحساسة لهذا الحساب، وأفهم أنني أستطيع سحب الموافقة وحذفها لاحقًا.</span>
      </label>
      <div className="flex flex-wrap items-center gap-3">
        <Button type="button" onClick={() => void save()} loading={busy}><Save aria-hidden="true" /> حفظ بموافقة</Button>
        <Button type="button" variant="outline" onClick={() => void revoke()} disabled={busy || !health.consent_granted}><RotateCcw aria-hidden="true" /> سحب الموافقة والحذف</Button>
        {health.consent_granted && <Badge>Consent Granted · {health.consent_version}</Badge>}
      </div>
      {message && <p className="text-sm font-semibold text-emerald-700 dark:text-emerald-300" role="status">{message}</p>}
      {error && <p className="text-sm font-semibold text-rose-700 dark:text-rose-300" role="alert">{error}</p>}
    </SectionCard>
  );
}

export function SettingsPage() {
  const { preferences, update, isSaving, saveError, version } = useAccessibility();
  const [draft, setDraft] = useState<AccessibilityPreferences>(preferences);
  const [saved, setSaved] = useState(false);

  useEffect(() => setDraft(preferences), [preferences]);

  const set = <K extends keyof AccessibilityPreferences>(key: K, value: AccessibilityPreferences[K]) => {
    setSaved(false);
    setDraft((current) => ({ ...current, [key]: value }));
  };

  const saveAccessibility = async () => {
    try {
      await update(draft);
      setSaved(true);
    } catch {
      setSaved(false);
    }
  };

  const grouped = useMemo(() => ({
    visual: [
      ["high_contrast", "تباين عالٍ", "يحافظ على وضوح النصوص والحدود."],
      ["screen_reader_optimized", "تحسين قارئ الشاشة", "يعزز التسميات الدلالية وترتيب التركيز."],
      ["reduced_color_dependence", "تقليل الاعتماد على اللون", "تظهر الحالات مع نص وأيقونة وشكل، لا باللون وحده."],
      ["dyslexia_friendly", "وضع القراءة الميسر", "يزيد قابلية القراءة دون افتراض حالة صحية."],
    ] as const,
    hearing: [
      ["captions", "التسميات النصية", "يعرض بدائل نصية للمحتوى المسموع."],
      ["visual_alerts", "تنبيهات مرئية", "لا تعتمد على الصوت وحده."],
      ["transcripts", "النصوص المفرغة", "يوفر نصًا قابلًا للقراءة عند توفر المحتوى."],
      ["mute_safe_notifications", "إشعارات آمنة عند الكتم", "يحافظ على التنبيهات المهمة بصريًا."],
    ] as const,
    motor: [
      ["larger_touch_targets", "أهداف لمس أكبر", "يرفع مساحة التفاعل إلى حجم أسهل للمس."],
      ["reduced_interaction_complexity", "تقليل تعقيد التفاعل", "يبسط المسارات غير السريرية."],
      ["longer_timeout", "مهلة أطول", "يطلب من الوظائف المدعومة احترام مهلة أطول."],
      ["keyboard_navigation", "تنقل بلوحة المفاتيح", "يحافظ على ترتيب تركيز واضح."],
    ] as const,
    cognitive: [
      ["simplified_interface", "واجهة مبسطة", "يقلل الكثافة البصرية دون حذف ضوابط السلامة."],
      ["reduced_visual_density", "كثافة بصرية أقل", "يضيف مسافات ووضوحًا أكبر."],
      ["clear_language", "لغة واضحة", "يفضل الجمل المباشرة والتعليمات المحددة."],
      ["step_by_step_workflows", "مسارات خطوة بخطوة", "يعرض التقدم بوضوح في الإجراءات المدعومة."],
    ] as const,
  }), []);

  const summaryCards: Array<[LucideIcon, string, string]> = [
    [Languages, "اللغة", "العربية العراقية"],
    [Palette, "المظهر", preferences.high_contrast ? "تباين عالٍ" : "Clinical Clarity"],
    [Sparkles, "الحركة", preferences.reduced_motion ? "مخفضة" : "قياسية"],
    [LockKeyhole, "الخصوصية", "حالتك الصحية خاصة"],
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="flex flex-col gap-4 rounded-[1.5rem] border border-slate-200/80 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-white/10 dark:bg-slate-900/70 sm:flex-row sm:items-end sm:justify-between sm:p-6">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-bold text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"><SlidersHorizontal className="h-3.5 w-3.5 text-[#0D9488]" /> تفضيلات المنصة</div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">Accessibility & Personal Needs</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">خصص العرض والتفاعل وفق احتياجاتك. هذه الإعدادات لا تشخّص حالة صحية ولا تمنح Permission ولا تغيّر صلاحيات الحساب.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-2xl border border-emerald-100 bg-emerald-50 px-3.5 py-2.5 text-xs text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-200"><Shield className="h-4 w-4" /> Backend authorization enforced</div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryCards.map(([Icon, label, value]) => (
          <Card key={String(label)} className="border-slate-200/80 dark:border-white/10"><CardContent className="flex items-center gap-3 p-4"><Icon className="h-5 w-5 text-[#0D9488]" aria-hidden="true" /><div><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-sm font-bold text-[#0F172A] dark:text-white">{value}</p></div></CardContent></Card>
        ))}
      </div>

      <SectionCard icon={Accessibility} title="Accessibility Profile" description="إعدادات عرض وتفاعل منخفضة الحساسية، يحددها المستخدم وتُطبّق محليًا بعد تحميلها من backend.">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white"><span>اللغة</span><select value={draft.language} onChange={(event) => set("language", event.target.value as AccessibilityPreferences["language"])} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 dark:border-white/10 dark:bg-slate-950"><option value="ar">العربية</option><option value="en">English</option><option value="ku">Kurdish</option><option value="tk">Turkmen</option><option value="syr">Assyrian</option></select></label>
          <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white"><span>حجم النص</span><select value={draft.font_size} onChange={(event) => set("font_size", event.target.value as AccessibilityPreferences["font_size"])} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 dark:border-white/10 dark:bg-slate-950"><option value="small">صغير</option><option value="medium">متوسط</option><option value="large">كبير</option><option value="x-large">كبير جدًا</option></select></label>
          <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white"><span>تدرج حجم النص: {draft.text_scale.toFixed(2)}×</span><input type="range" min="0.85" max="2" step="0.05" value={draft.text_scale} onChange={(event) => set("text_scale", Number(event.target.value))} className="w-full accent-teal-600" /></label>
          <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white"><span>نمط عمى الألوان</span><select value={draft.color_blind_mode} onChange={(event) => set("color_blind_mode", event.target.value as AccessibilityPreferences["color_blind_mode"])} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 dark:border-white/10 dark:bg-slate-950"><option value="none">بدون نمط خاص</option><option value="protanopia">Protanopia-safe</option><option value="deuteranopia">Deuteranopia-safe</option><option value="tritanopia">Tritanopia-safe</option><option value="monochrome">Monochrome</option></select></label>
        </div>
      </SectionCard>

      <div className="grid gap-6 lg:grid-cols-2">
        {([
          [Eye, "Visual", grouped.visual],
          [Headphones, "Hearing", grouped.hearing],
          [MousePointer2, "Motor", grouped.motor],
          [Keyboard, "Cognitive / Reading", grouped.cognitive],
        ] as const).map(([Icon, title, items]) => (
          <SectionCard key={title} icon={Icon} title={title} description="خيار اختياري يغير العرض أو التفاعل فقط.">
            <div className="space-y-3">{items.map(([key, label, description]) => <ToggleRow key={key} checked={Boolean(draft[key])} label={label} description={description} onChange={(checked) => set(key, checked)} />)}</div>
          </SectionCard>
        ))}
      </div>

      <SectionCard icon={Volume2} title="Photosensitivity & Notifications" description="لا توجد تأثيرات وامضة مقصودة؛ هذه الخيارات تعزز البدائل الثابتة وتقلل الحركة والتنبيهات غير الضرورية.">
        <div className="grid gap-3 sm:grid-cols-2"><ToggleRow checked={draft.reduced_motion} label="تقليل الحركة" description="يوقف الحركة غير الضرورية." onChange={(value) => set("reduced_motion", value)} /><ToggleRow checked={draft.disable_flashing} label="تعطيل الوميض" description="يبقي التأثيرات غير الومّاضة فقط." onChange={(value) => set("disable_flashing", value)} /><ToggleRow checked={draft.static_alternatives} label="بدائل ثابتة" description="يستخدم نسخة ثابتة عندما تكون متاحة." onChange={(value) => set("static_alternatives", value)} /><ToggleRow checked={draft.reduced_notifications} label="تقليل الإشعارات" description="يقلل غير الضروري دون إسقاط التنبيهات الحرجة." onChange={(value) => set("reduced_notifications", value)} /></div>
      </SectionCard>

      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-teal-100 bg-teal-50/60 p-4 dark:border-teal-900/50 dark:bg-teal-950/20"><Button type="button" onClick={() => void saveAccessibility()} loading={isSaving}><Save aria-hidden="true" /> حفظ Accessibility</Button><Button type="button" variant="outline" onClick={() => setDraft(preferences)} disabled={isSaving}><RotateCcw aria-hidden="true" /> إلغاء التغييرات</Button><span className="text-xs text-teal-900/70 dark:text-teal-100/70">Version: {version || "local default"}</span>{saved && <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-700 dark:text-emerald-300" role="status"><CheckCircle2 className="h-4 w-4" /> Saved</span>}{saveError && <span className="inline-flex items-center gap-1 text-sm font-semibold text-rose-700 dark:text-rose-300" role="alert"><AlertTriangle className="h-4 w-4" /> {saveError}</span>}</div>

      <HealthPreferencesPanel />

      <div className="flex items-start gap-3 rounded-2xl border border-sky-100 bg-sky-50/70 p-4 dark:border-sky-900/50 dark:bg-sky-950/20"><Shield className="mt-0.5 h-5 w-5 shrink-0 text-sky-600 dark:text-sky-300" aria-hidden="true" /><div><p className="text-sm font-semibold text-sky-950 dark:text-sky-100">حماية غير قابلة للتجاوز</p><p className="mt-1 text-xs leading-5 text-sky-900/70 dark:text-sky-100/70">الواجهة لا تقرر الوصول إلى البيانات السريرية. كل وصول حساس يمر عبر Backend Authorization وScope وAudit، ولا تستخدم هذه الخيارات لتغيير Role أو Permission.</p></div></div>
    </div>
  );
}
