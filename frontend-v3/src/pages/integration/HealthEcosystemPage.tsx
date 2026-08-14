import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Database,
  ExternalLink,
  FileCheck2,
  FlaskConical,
  HeartPulse,
  Layers3,
  Network,
  ScanLine,
  Search,
  ShieldCheck,
  Smartphone,
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

type Category = "الكل" | "FHIR" | "التكامل" | "المختبر" | "التصوير" | "الموبايل" | "الصحة العامة";
type LicenseClass = "MIT / Apache / BSD" | "MPL-2.0" | "GPL / AGPL" | "مراجعة مطلوبة";

type HealthCapability = {
  id: string;
  name: string;
  category: Exclude<Category, "الكل">;
  icon: typeof Activity;
  purpose: string;
  originalImplementation: string;
  standards: string[];
  licenseClass: LicenseClass;
  sourceUrl: string;
  readiness: "جاهز للتصميم" | "قيد التحقق" | "مرجع معماري";
};

const capabilities: HealthCapability[] = [
  {
    id: "fhir-core",
    name: "نواة البيانات الصحية المعيارية",
    category: "FHIR",
    icon: Database,
    purpose: "توحيد المرضى والزيارات والملاحظات والنتائج في نموذج قابل للتبادل.",
    originalImplementation: "GULA Health Resource Layer: نماذج داخلية وواجهات تحويل مستقلة تعتمد FHIR كمعيار، لا كودًا من مشروع خارجي.",
    standards: ["FHIR R4", "REST", "OAuth2"],
    licenseClass: "MIT / Apache / BSD",
    sourceUrl: "https://github.com/hapifhir/hapi-fhir",
    readiness: "جاهز للتصميم",
  },
  {
    id: "interoperability",
    name: "بوابة HL7 إلى FHIR",
    category: "التكامل",
    icon: Network,
    purpose: "استقبال الرسائل القديمة وتحويلها إلى موارد موحدة داخل GULA.",
    originalImplementation: "GULA Interop Gateway: محول رسائل مستقل مع سجل تدقيق وقواعد تحويل قابلة للاختبار.",
    standards: ["HL7 v2", "FHIR R4", "Queue"],
    licenseClass: "MIT / Apache / BSD",
    sourceUrl: "https://github.com/LinuxForHealth/hl7v2-fhir-converter",
    readiness: "جاهز للتصميم",
  },
  {
    id: "laboratory",
    name: "سير عمل المختبر",
    category: "المختبر",
    icon: FlaskConical,
    purpose: "ربط طلب التحليل والعينة والنتيجة بالمريض والزيارة.",
    originalImplementation: "GULA Laboratory Workflow: دورة عينة أصلية مع adapters لـFHIR وواجهات LIS، دون نسخ OpenELIS.",
    standards: ["ServiceRequest", "Specimen", "Observation"],
    licenseClass: "MPL-2.0",
    sourceUrl: "https://github.com/DIGI-UW/OpenELIS-Global-2",
    readiness: "جاهز للتصميم",
  },
  {
    id: "imaging",
    name: "التصوير الطبي",
    category: "التصوير",
    icon: ScanLine,
    purpose: "عرض حالة فحوص التصوير وربطها بالسجل دون تخزين الملفات الكبيرة في الواجهة.",
    originalImplementation: "GULA Imaging Gateway: روابط وصول مؤقتة وmetadata للفحص، مع DICOMweb adapter مستقل.",
    standards: ["DICOMweb", "Study", "Series"],
    licenseClass: "MIT / Apache / BSD",
    sourceUrl: "https://github.com/microsoft/dicom-server",
    readiness: "قيد التحقق",
  },
  {
    id: "public-health",
    name: "مؤشرات الصحة العامة",
    category: "الصحة العامة",
    icon: HeartPulse,
    purpose: "تجميع المؤشرات والمناطق والتغطية والتقارير دون خلطها بالملف السريري الفردي.",
    originalImplementation: "GULA Public Health Analytics: قاموس مؤشرات ومقاييس ومصادر بيانات مع provenance واضح.",
    standards: ["Indicator", "Measure", "Geography"],
    licenseClass: "MIT / Apache / BSD",
    sourceUrl: "https://github.com/dhis2/dhis2-core",
    readiness: "قيد التحقق",
  },
  {
    id: "mobile-field",
    name: "تطبيق الميدان والمريض",
    category: "الموبايل",
    icon: Smartphone,
    purpose: "دعم جمع البيانات والعمل غير المتصل مع مزامنة آمنة لاحقًا.",
    originalImplementation: "GULA Mobile Sync Contract: طابور أحداث محلي وتعارضات قابلة للمراجعة، مستلهم من احتياج FHIR للموبايل لا من كود SDK.",
    standards: ["Offline-first", "FHIR", "Conflict log"],
    licenseClass: "MIT / Apache / BSD",
    sourceUrl: "https://github.com/ohs-foundation/android-fhir",
    readiness: "مرجع معماري",
  },
];

const licenseVariant = (license: LicenseClass): "success" | "warning" | "destructive" | "outline" => {
  if (license === "MIT / Apache / BSD") return "success";
  if (license === "MPL-2.0") return "warning";
  if (license === "GPL / AGPL") return "destructive";
  return "outline";
};

const readinessVariant = (readiness: HealthCapability["readiness"]): "success" | "warning" | "outline" => {
  if (readiness === "جاهز للتصميم") return "success";
  if (readiness === "قيد التحقق") return "warning";
  return "outline";
};

export function HealthEcosystemPage() {
  const [category, setCategory] = useState<Category>("الكل");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string[]>(["fhir-core", "interoperability", "laboratory"]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("ar");
    return capabilities.filter((item) => {
      const matchesCategory = category === "الكل" || item.category === category;
      const haystack = `${item.name} ${item.purpose} ${item.originalImplementation} ${item.standards.join(" ")}`.toLocaleLowerCase("ar");
      return matchesCategory && (!normalized || haystack.includes(normalized));
    });
  }, [category, query]);

  const toggleSelected = (id: string) => {
    setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  };

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader
        title="منظومة القدرات الصحية"
        description="تنفيذات GULA الأصلية للوظائف المفيدة في الأنظمة الصحية العالمية، مع فصل واضح بين المعيار والكود والترخيص."
      />

      <Card className="overflow-hidden border-indigo-200 bg-gradient-to-l from-indigo-50 via-white to-cyan-50 dark:border-indigo-900/50 dark:from-indigo-950/40 dark:via-background dark:to-cyan-950/30">
        <CardContent className="p-6">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-3xl space-y-3">
              <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300">
                <Layers3 className="h-5 w-5" />
                <span className="text-sm font-semibold">نطاق الإصدار الأصلي</span>
              </div>
              <h2 className="text-2xl font-bold tracking-tight">طبقة تكامل واحدة، لا نسخ لأنظمة متعددة</h2>
              <p className="text-sm leading-7 text-muted-foreground">
                هذه الصفحة تحول الوظائف العامة المفيدة إلى عقود وقدرات داخلية في GULA. لا تُنسخ ملفات أو شيفرات أو منطق خاص؛ بل تُبنى adapters مستقلة حول FHIR وHL7 وDICOM، مع إبقاء الخدمات الثقيلة خارج واجهة Vercel.
              </p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="success"><ShieldCheck className="ml-1 h-3.5 w-3.5" />تنفيذ مستقل</Badge>
                <Badge variant="outline"><FileCheck2 className="ml-1 h-3.5 w-3.5" />تدقيق ترخيص</Badge>
                <Badge variant="outline"><CheckCircle2 className="ml-1 h-3.5 w-3.5" />بيانات تجريبية فقط</Badge>
              </div>
            </div>
            <div className="grid min-w-[240px] grid-cols-2 gap-3">
              <div className="rounded-xl bg-background/80 p-4 shadow-sm"><p className="text-xs text-muted-foreground">القدرات</p><p className="mt-1 text-2xl font-bold">{capabilities.length}</p></div>
              <div className="rounded-xl bg-background/80 p-4 shadow-sm"><p className="text-xs text-muted-foreground">في خطة التنفيذ</p><p className="mt-1 text-2xl font-bold">{selected.length}</p></div>
              <div className="rounded-xl bg-background/80 p-4 shadow-sm"><p className="text-xs text-muted-foreground">المعايير</p><p className="mt-1 text-2xl font-bold">{new Set(capabilities.flatMap((item) => item.standards)).size}</p></div>
              <div className="rounded-xl bg-background/80 p-4 shadow-sm"><p className="text-xs text-muted-foreground">نشر الواجهة</p><p className="mt-1 text-sm font-bold text-emerald-700 dark:text-emerald-400">Vercel فقط</p></div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardContent className="p-5"><div className="flex items-center justify-between"><div><p className="text-sm text-muted-foreground">1. المعايير</p><p className="mt-1 font-semibold">FHIR / HL7 / DICOM</p></div><Network className="h-8 w-8 text-indigo-600" /></div></CardContent></Card>
        <Card><CardContent className="p-5"><div className="flex items-center justify-between"><div><p className="text-sm text-muted-foreground">2. العقود</p><p className="mt-1 font-semibold">API وAdapter مستقل</p></div><FileCheck2 className="h-8 w-8 text-cyan-600" /></div></CardContent></Card>
        <Card><CardContent className="p-5"><div className="flex items-center justify-between"><div><p className="text-sm text-muted-foreground">3. التشغيل</p><p className="mt-1 font-semibold">خدمات خلفية منفصلة</p></div><Activity className="h-8 w-8 text-emerald-600" /></div></CardContent></Card>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="relative min-w-0 flex-1">
              <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="ابحث في القدرات أو المعايير..." className="h-10 w-full rounded-md border border-input bg-background pr-9 pl-3 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring" />
            </div>
            <div className="flex flex-wrap gap-2">
              {(["الكل", "FHIR", "التكامل", "المختبر", "التصوير", "الموبايل", "الصحة العامة"] as Category[]).map((item) => (
                <Button key={item} type="button" size="sm" variant={category === item ? "default" : "outline"} onClick={() => setCategory(item)}>{item}</Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        {filtered.map((item) => {
          const Icon = item.icon;
          const isSelected = selected.includes(item.id);
          return (
            <Card key={item.id} className={isSelected ? "border-indigo-300 shadow-md dark:border-indigo-800" : ""}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-xl bg-indigo-100 p-3 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300"><Icon className="h-5 w-5" /></div>
                    <div><CardTitle className="text-base">{item.name}</CardTitle><p className="mt-1 text-xs text-muted-foreground">{item.category}</p></div>
                  </div>
                  <Badge variant={readinessVariant(item.readiness)}>{item.readiness}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm leading-6 text-muted-foreground">{item.purpose}</p>
                <div className="rounded-lg bg-muted/50 p-3 text-sm leading-6"><span className="font-semibold">تنفيذ GULA الأصلي: </span>{item.originalImplementation}</div>
                <div className="flex flex-wrap gap-2">{item.standards.map((standard) => <Badge key={standard} variant="secondary">{standard}</Badge>)}<Badge variant={licenseVariant(item.licenseClass)}>{item.licenseClass}</Badge></div>
                <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-3">
                  <div className="flex items-center gap-2"><Button type="button" size="sm" variant={isSelected ? "default" : "outline"} onClick={() => toggleSelected(item.id)}>{isSelected ? "ضمن خطة التنفيذ" : "إضافة للخطة"}</Button><a href={item.sourceUrl} target="_blank" rel="noreferrer" className="inline-flex h-8 items-center gap-1 rounded-md px-3 text-xs text-muted-foreground hover:bg-accent hover:text-foreground">المصدر <ExternalLink className="h-3.5 w-3.5" /></a></div>
                  <Link to="/integration" className="inline-flex items-center gap-1 text-xs font-medium text-indigo-700 hover:underline dark:text-indigo-300">إدارة التكامل <ArrowUpRight className="h-3.5 w-3.5" /></Link>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filtered.length === 0 && <Card><CardContent className="p-10 text-center text-sm text-muted-foreground">لا توجد قدرة مطابقة للبحث الحالي.</CardContent></Card>}

      <Card className="border-amber-200 bg-amber-50/60 dark:border-amber-900/50 dark:bg-amber-950/20">
        <CardContent className="flex items-start gap-3 p-5 text-sm leading-7"><ShieldCheck className="mt-1 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-400" /><p><strong>حاجز الامتثال:</strong> هذه الصفحة تسجل القدرات والخطة فقط. لا يوجد فيها اتصال مباشر ببيانات مرضى أو كتابة تشغيلية. أي ربط لاحق يجب أن يمر عبر عقد خادمي معتمد، تدقيق صلاحيات، سجل أثر، وبيانات اصطناعية في بيئة الاختبار.</p></CardContent>
      </Card>
    </div>
  );
}

export default HealthEcosystemPage;
