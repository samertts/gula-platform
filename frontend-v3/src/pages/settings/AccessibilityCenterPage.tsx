import { useEffect, useMemo, useState } from "react";
import {
  Accessibility,
  CheckCircle2,
  Eye,
  Headphones,
  Keyboard,
  MessageSquareText,
  MousePointer2,
  Palette,
  RotateCcw,
  Save,
  ShieldCheck,
  Sparkles,
  Volume2,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { useAccessibility } from "@/contexts/AccessibilityContext";
import { localeOptions } from "@/i18n/locales";
import type { AccessibilityPreferences } from "@/types";
import {
  AccessibleStatusLegend,
  AdaptivePreview,
  AdaptiveStateBadge,
  AdaptiveStatus,
  type AdaptiveState,
} from "@/components/accessibility/AdaptiveComponents";

type PreferenceKey = keyof AccessibilityPreferences;

type ToggleDefinition = {
  key: PreferenceKey;
  label: string;
  description: string;
};

const toggleGroups: Array<{
  id: string;
  title: string;
  description: string;
  icon: typeof Accessibility;
  items: ToggleDefinition[];
}> = [
  {
    id: "visual",
    title: "Visual",
    description: "الوضوح والتباين وحجم النص والبدائل غير اللونية.",
    icon: Eye,
    items: [
      { key: "high_contrast", label: "تباين عالٍ", description: "يزيد وضوح النصوص والحدود دون تغيير صلاحيات الحساب." },
      { key: "reduced_color_dependence", label: "تقليل الاعتماد على اللون", description: "يضيف نصًا وأيقونة وشكلًا لكل حالة." },
      { key: "dyslexia_friendly", label: "قراءة ميسرة", description: "يحسن المسافات وقابلية قراءة النصوص." },
    ],
  },
  {
    id: "hearing",
    title: "Hearing",
    description: "بدائل نصية ومرئية للمحتوى أو التنبيهات الصوتية.",
    icon: Headphones,
    items: [
      { key: "captions", label: "التسميات النصية", description: "يعرض النص عند توفر محتوى مسموع." },
      { key: "visual_alerts", label: "تنبيهات مرئية", description: "لا يعتمد على الصوت وحده في التنبيه." },
      { key: "transcripts", label: "النصوص المفرغة", description: "يوفر نسخة قابلة للقراءة من المحتوى المدعوم." },
      { key: "mute_safe_notifications", label: "إشعارات آمنة عند الكتم", description: "يبقي التنبيهات المهمة مرئية حتى عند كتم الصوت." },
    ],
  },
  {
    id: "motor",
    title: "Motor",
    description: "مساحات لمس أكبر وتفاعل أقل تعقيدًا ومسارات لوحة المفاتيح.",
    icon: MousePointer2,
    items: [
      { key: "larger_touch_targets", label: "أهداف لمس أكبر", description: "يرفع مساحة التفاعل إلى حجم أسهل للمس." },
      { key: "reduced_interaction_complexity", label: "تقليل تعقيد التفاعل", description: "يبسط المسارات غير السريرية فقط." },
      { key: "longer_timeout", label: "مهلة أطول", description: "يطلب من الوظائف المدعومة احترام مهلة أطول." },
      { key: "keyboard_navigation", label: "تنقل بلوحة المفاتيح", description: "يحافظ على ترتيب تركيز واضح وقابل للتوقع." },
    ],
  },
  {
    id: "cognitive",
    title: "Cognitive / Reading",
    description: "لغة مباشرة وكثافة أقل وخطوات واضحة دون حذف ضوابط السلامة.",
    icon: Keyboard,
    items: [
      { key: "simplified_interface", label: "واجهة مبسطة", description: "يقلل الكثافة دون إزالة وظائف السلامة." },
      { key: "reduced_visual_density", label: "كثافة بصرية أقل", description: "يضيف مسافات ووضوحًا أكبر بين العناصر." },
      { key: "clear_language", label: "لغة واضحة", description: "يفضل الجمل المباشرة والتعليمات المحددة." },
      { key: "step_by_step_workflows", label: "مسارات خطوة بخطوة", description: "يعرض التقدم بوضوح في الإجراءات المدعومة." },
    ],
  },
  {
    id: "photosensitivity",
    title: "Photosensitivity",
    description: "تقليل الحركة والوميض والتنبيهات غير الضرورية مع بدائل ثابتة.",
    icon: Sparkles,
    items: [
      { key: "reduced_motion", label: "تقليل الحركة", description: "يوقف الحركة غير الضرورية." },
      { key: "disable_flashing", label: "تعطيل الوميض", description: "يبقي التأثيرات غير الومّاضة فقط." },
      { key: "static_alternatives", label: "بدائل ثابتة", description: "يستخدم نسخة ثابتة عندما تكون متاحة." },
      { key: "reduced_notifications", label: "تقليل الإشعارات", description: "يقلل غير الضروري دون إسقاط التنبيهات الحرجة." },
    ],
  },
  {
    id: "communication",
    title: "Communication",
    description: "خيارات مساعدة للتواصل والنصوص والقراءة الصوتية.",
    icon: MessageSquareText,
    items: [
      { key: "text_alternatives", label: "بدائل نصية", description: "يفضل النص عند توفره بدل الوسائط وحدها." },
      { key: "voice_interaction", label: "التفاعل الصوتي", description: "يعرض نقاط تكامل التفاعل الصوتي حيث تكون مدعومة." },
      { key: "screen_reader_optimized", label: "تحسين قارئ الشاشة", description: "يحسن التسميات وترتيب التركيز الدلالي." },
    ],
  },
];

function ToggleRow({ checked, item, onChange }: { checked: boolean; item: ToggleDefinition; onChange: (value: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-start justify-between gap-4 rounded-2xl border border-slate-200/80 bg-white/80 p-4 transition-colors hover:border-teal-200 hover:bg-teal-50/30 dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-teal-900/70">
      <span className="min-w-0">
        <span className="block text-sm font-bold text-[#0F172A] dark:text-white">{item.label}</span>
        <span className="mt-1 block text-xs leading-5 text-muted-foreground">{item.description}</span>
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

function statusFor({ previewActive, isSaving, saveError, saved }: { previewActive: boolean; isSaving: boolean; saveError: string | null; saved: boolean }): AdaptiveState {
  if (isSaving) return "saving";
  if (saveError) return "failed";
  if (previewActive) return "preview";
  if (saved) return "saved";
  return "enabled";
}

export function AccessibilityCenterPage() {
  const { preferences, update, preview, clearPreview, isSaving, saveError, version } = useAccessibility();
  const [draft, setDraft] = useState<AccessibilityPreferences>(preferences);
  const [previewActive, setPreviewActive] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setDraft(preferences);
  }, [preferences]);

  const status = statusFor({ previewActive, isSaving, saveError, saved });
  const enabledCount = useMemo(() => Object.values(draft).filter((value) => value === true).length, [draft]);

  const setPreference = <K extends PreferenceKey>(key: K, value: AccessibilityPreferences[K]) => {
    const next = { ...draft, [key]: value };
    setDraft(next);
    setSaved(false);
    preview(next);
    setPreviewActive(true);
  };

  const applyPreview = () => {
    preview(draft);
    setPreviewActive(true);
  };

  const cancelPreview = () => {
    setDraft(preferences);
    clearPreview();
    setPreviewActive(false);
    setSaved(false);
  };

  const save = async () => {
    try {
      await update(draft);
      setPreviewActive(false);
      setSaved(true);
    } catch {
      setSaved(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="rounded-[1.75rem] border border-slate-200/80 bg-white p-5 shadow-[0_18px_44px_-36px_rgba(15,23,42,0.48)] dark:border-white/10 dark:bg-slate-900/70 sm:p-7">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-teal-100 bg-teal-50 px-3 py-1.5 text-xs font-bold text-teal-800 dark:border-teal-900/60 dark:bg-teal-950/30 dark:text-teal-200">
              <Accessibility className="h-4 w-4" aria-hidden="true" />
              Universal Accessibility Center
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[#0F172A] dark:text-white sm:text-3xl">تجربة متكيفة وآمنة</h1>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">
              خصص العرض والتفاعل وفق احتياجاتك. التغييرات تعرض مباشرة في Preview، ولا تغيّر Role أو Permission ولا تُستخدم لتشخيص حالة صحية.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <AdaptiveStateBadge state={status} />
            <span className="rounded-full border border-slate-200 px-3 py-1 text-xs text-muted-foreground dark:border-white/10">{enabledCount} إعدادات مفعّلة</span>
          </div>
        </div>
      </header>

      <Card className="border-sky-100 bg-sky-50/60 dark:border-sky-900/50 dark:bg-sky-950/20">
        <CardContent className="space-y-4 p-5 sm:p-6">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-sky-700 dark:text-sky-300" aria-hidden="true" />
            <div>
              <h2 className="text-sm font-bold text-sky-950 dark:text-sky-100">حدود الحماية</h2>
              <p className="mt-1 text-sm leading-6 text-sky-900/75 dark:text-sky-100/75">تُحفظ إعدادات Accessibility عبر العقد الحالي وبنسخة قابلة للتدقيق. لا توجد بيانات صحية في هذه الصفحة، ولا يمكن لأي خيار هنا تجاوز تفويض Backend أو عزل المختبر.</p>
            </div>
          </div>
          <AdaptiveStatus state={previewActive ? "preview" : "saved"} label={previewActive ? "Preview غير محفوظ" : "التفضيلات المحفوظة فعالة"} description={previewActive ? "راجع المظهر والتفاعل ثم اضغط حفظ أو إلغاء. لا تُكتب التغييرات الحساسة في جهازك كبيانات صحية." : `Version: ${version || "local default"}`} />
        </CardContent>
      </Card>

      <section aria-labelledby="live-preview-heading">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h2 id="live-preview-heading" className="text-lg font-bold text-[#0F172A] dark:text-white">Live Preview</h2>
            <p className="mt-1 text-sm text-muted-foreground">مثال موحد يثبت أن الحالة لا تعتمد على اللون فقط.</p>
          </div>
          <Button type="button" variant="outline" onClick={applyPreview} disabled={isSaving}><Eye className="h-4 w-4" aria-hidden="true" /> Preview الآن</Button>
        </div>
        <AdaptivePreview active={previewActive}>
          <div className="grid gap-3 sm:grid-cols-3">
            <AdaptiveStatus state="enabled" label="Verified result" description="نص + أيقونة + شكل ✓" />
            <AdaptiveStatus state="consent_required" label="Consent required" description="البيانات الحساسة لا تظهر قبل الموافقة." />
            <AdaptiveStatus state={preferences.reduced_motion ? "disabled" : "preview"} label="Motion policy" description={preferences.reduced_motion ? "Reduced motion active" : "Preview uses standard motion"} />
          </div>
        </AdaptivePreview>
      </section>

      <section className="grid gap-6 lg:grid-cols-2" aria-label="Accessibility settings">
        <div id="display-profile" className="scroll-mt-6">
          <Card className="border-slate-200/80 dark:border-white/10">
            <CardContent className="space-y-4 p-5 sm:p-6">
              <div className="flex items-start gap-3"><Palette className="mt-0.5 h-5 w-5 text-teal-700 dark:text-teal-300" aria-hidden="true" /><div><h2 className="text-base font-bold text-[#0F172A] dark:text-white">Display profile</h2><p className="mt-1 text-sm text-muted-foreground">اللغة وحجم النص ونمط الألوان.</p></div></div>
            <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white"><span>اللغة</span><select value={draft.language} onChange={(event) => setPreference("language", event.target.value as AccessibilityPreferences["language"])} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 dark:border-white/10 dark:bg-slate-950">{localeOptions.map((option) => <option key={option.code} value={option.code}>{option.nativeName} · {option.code}</option>)}</select></label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white"><span>حجم النص</span><select value={draft.font_size} onChange={(event) => setPreference("font_size", event.target.value as AccessibilityPreferences["font_size"])} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 dark:border-white/10 dark:bg-slate-950"><option value="small">صغير</option><option value="medium">متوسط</option><option value="large">كبير</option><option value="x-large">كبير جدًا</option></select></label>
              <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white"><span>مقياس النص: {draft.text_scale.toFixed(2)}×</span><input type="range" min="0.85" max="2" step="0.05" value={draft.text_scale} onChange={(event) => setPreference("text_scale", Number(event.target.value))} className="mt-3 w-full accent-teal-600" /></label>
            </div>
              <label className="space-y-2 text-sm font-semibold text-[#0F172A] dark:text-white"><span>نمط عمى الألوان</span><select value={draft.color_blind_mode} onChange={(event) => setPreference("color_blind_mode", event.target.value as AccessibilityPreferences["color_blind_mode"])} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3 dark:border-white/10 dark:bg-slate-950"><option value="none">بدون نمط خاص</option><option value="protanopia">Protanopia-safe</option><option value="deuteranopia">Deuteranopia-safe</option><option value="tritanopia">Tritanopia-safe</option><option value="monochrome">Monochrome</option></select></label>
            </CardContent>
          </Card>
        </div>

        {toggleGroups.map((group) => {
          const Icon = group.icon;
          return (
            <Card key={group.id} className="border-slate-200/80 dark:border-white/10">
              <CardContent className="space-y-4 p-5 sm:p-6">
                <div className="flex items-start gap-3"><Icon className="mt-0.5 h-5 w-5 text-teal-700 dark:text-teal-300" aria-hidden="true" /><div><h2 className="text-base font-bold text-[#0F172A] dark:text-white">{group.title}</h2><p className="mt-1 text-sm leading-6 text-muted-foreground">{group.description}</p></div></div>
                <div className="space-y-3">{group.items.map((item) => <ToggleRow key={String(item.key)} item={item} checked={Boolean(draft[item.key])} onChange={(value) => setPreference(item.key, value)} />)}</div>
              </CardContent>
            </Card>
          );
        })}
      </section>

      <Card className="border-slate-200/80 dark:border-white/10">
        <CardContent className="space-y-4 p-5 sm:p-6">
          <div className="flex items-start gap-3"><Volume2 className="mt-0.5 h-5 w-5 text-teal-700 dark:text-teal-300" aria-hidden="true" /><div><h2 className="text-base font-bold text-[#0F172A] dark:text-white">Status language and shape</h2><p className="mt-1 text-sm leading-6 text-muted-foreground">كل الحالات الحرجة يجب أن تبقى مفهومة بالنص والأيقونة والشكل، حتى مع نمط عمى الألوان أو قارئ الشاشة.</p></div></div>
          <AccessibleStatusLegend />
        </CardContent>
      </Card>

      <div className="sticky bottom-3 z-10 flex flex-wrap items-center gap-3 rounded-2xl border border-teal-100 bg-white/95 p-4 shadow-lg backdrop-blur dark:border-teal-900/50 dark:bg-slate-900/95">
        <Button type="button" onClick={() => void save()} loading={isSaving}><Save className="h-4 w-4" aria-hidden="true" /> حفظ التفضيلات</Button>
        <Button type="button" variant="outline" onClick={cancelPreview} disabled={isSaving}><RotateCcw className="h-4 w-4" aria-hidden="true" /> إلغاء Preview</Button>
        <span className="text-xs text-muted-foreground">لا يتم حفظ أي بيانات صحية من هذه الصفحة.</span>
        {saved && <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-700 dark:text-emerald-300" role="status"><CheckCircle2 className="h-4 w-4" /> تم الحفظ</span>}
        {saveError && <span className="text-sm font-semibold text-rose-700 dark:text-rose-300" role="alert">تعذر الحفظ: {saveError}</span>}
      </div>
    </div>
  );
}
