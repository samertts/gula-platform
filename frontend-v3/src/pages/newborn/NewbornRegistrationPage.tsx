/**
 * تصميم الصفحة: واجهة سريرية عربية هادئة، ذات تسلسل خطوة-بخطوة وخلفية فاتحة،
 * تبرز خصوصية أرقام الوالدين وتعرض حالة التسجيل بدلاً من الاحتفاظ ببيانات حساسة.
 */
import { type ChangeEvent, type FormEvent, type ReactNode, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { toast } from "@/hooks/useToast";
import { Baby, CheckCircle2, ClipboardCheck, LockKeyhole, ShieldCheck } from "lucide-react";

type NewbornForm = {
  birth_certificate_number: string;
  mother_national_id: string;
  father_national_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: "male" | "female" | "unknown";
  birth_weight_grams: string;
  hospital_registration_number: string;
  birth_place: string;
  birth_place_type: string;
  delivery_method: string;
  notes: string;
};

type NewbornReceipt = {
  citizen_id: string;
  newborn_id?: string;
  health_number: string;
  is_temporary: boolean;
};

const initialForm: NewbornForm = {
  birth_certificate_number: "",
  mother_national_id: "",
  father_national_id: "",
  first_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "unknown",
  birth_weight_grams: "",
  hospital_registration_number: "",
  birth_place: "",
  birth_place_type: "hospital",
  delivery_method: "",
  notes: "",
};

export function NewbornRegistrationPage() {
  const [form, setForm] = useState<NewbornForm>(initialForm);
  const [receipt, setReceipt] = useState<NewbornReceipt | null>(null);

  const registerNewborn = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.post("/identity/newborn", payload).then((response) => response.data as NewbornReceipt),
    onSuccess: (result) => {
      setReceipt(result);
      setForm(initialForm);
      toast({ variant: "success", title: "تم إنشاء السجل الصحي المؤقت", description: "تم مسح أرقام الهوية من النموذج بعد الإرسال." });
    },
    onError: () => {
      toast({ variant: "destructive", title: "تعذر إتمام التسجيل", description: "تحقق من رقم شهادة الولادة وسجلي الوالدين الموثقين ثم أعد المحاولة." });
    },
  });

  const update = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setReceipt(null);
    registerNewborn.mutate({
      ...form,
      birth_weight_grams: form.birth_weight_grams ? Number(form.birth_weight_grams) : undefined,
      hospital_registration_number: form.hospital_registration_number || undefined,
      birth_place: form.birth_place || undefined,
      birth_place_type: form.birth_place_type || undefined,
      delivery_method: form.delivery_method || undefined,
      notes: form.notes || undefined,
    });
  };

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader
        title="تسجيل حديثي الولادة"
        description="إنشاء سجل صحي مؤقت مرتبط بسجلي الأب والأم لحين إصدار البطاقة الوطنية للطفل."
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <form onSubmit={submit} className="space-y-5" noValidate>
          <Card className="border-emerald-100 bg-gradient-to-bl from-emerald-50/70 to-background shadow-sm">
            <CardHeader className="flex-row items-start gap-3 space-y-0">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-700 text-white shadow-sm">
                <Baby className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle className="text-lg">بيانات الطفل وشهادة الولادة</CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">تُراجع شهادة الولادة مرة واحدة لتجنب إنشاء سجلات مكررة.</p>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <Field label="رقم شهادة الولادة" required htmlFor="birth_certificate_number">
                <Input id="birth_certificate_number" name="birth_certificate_number" value={form.birth_certificate_number} onChange={update} required maxLength={50} autoComplete="off" />
              </Field>
              <Field label="تاريخ الولادة" required htmlFor="date_of_birth">
                <Input id="date_of_birth" name="date_of_birth" type="date" value={form.date_of_birth} onChange={update} required />
              </Field>
              <Field label="اسم الطفل" htmlFor="first_name">
                <Input id="first_name" name="first_name" value={form.first_name} onChange={update} maxLength={100} autoComplete="off" />
              </Field>
              <Field label="اللقب" htmlFor="last_name">
                <Input id="last_name" name="last_name" value={form.last_name} onChange={update} maxLength={100} autoComplete="off" />
              </Field>
              <Field label="الجنس" htmlFor="gender">
                <select id="gender" name="gender" value={form.gender} onChange={update} className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-ring">
                  <option value="unknown">غير محدد</option>
                  <option value="male">ذكر</option>
                  <option value="female">أنثى</option>
                </select>
              </Field>
              <Field label="وزن الولادة بالغم" htmlFor="birth_weight_grams">
                <Input id="birth_weight_grams" name="birth_weight_grams" type="number" min="200" max="10000" value={form.birth_weight_grams} onChange={update} inputMode="numeric" />
              </Field>
            </CardContent>
          </Card>

          <Card className="border-sky-100 shadow-sm">
            <CardHeader className="flex-row items-start gap-3 space-y-0">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-sky-700 text-white shadow-sm">
                <ShieldCheck className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle className="text-lg">التحقق من الوالدين</CardTitle>
                <p id="parent-id-hint" className="mt-1 text-sm text-muted-foreground">تُستخدم الأرقام الوطنية للتحقق المطابق مع السجل الوطني فقط، ولا تُحفظ في سجل الطفل أو في هذه الواجهة.</p>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <Field label="الرقم الوطني للأم" required htmlFor="mother_national_id">
                <Input id="mother_national_id" name="mother_national_id" value={form.mother_national_id} onChange={update} required pattern="[0-9]{4,16}" minLength={4} maxLength={16} inputMode="numeric" autoComplete="off" aria-describedby="parent-id-hint" />
              </Field>
              <Field label="الرقم الوطني للأب" required htmlFor="father_national_id">
                <Input id="father_national_id" name="father_national_id" value={form.father_national_id} onChange={update} required pattern="[0-9]{4,16}" minLength={4} maxLength={16} inputMode="numeric" autoComplete="off" aria-describedby="parent-id-hint" />
              </Field>
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">تفاصيل منشأة الولادة</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <Field label="رقم تسجيل المنشأة" htmlFor="hospital_registration_number">
                <Input id="hospital_registration_number" name="hospital_registration_number" value={form.hospital_registration_number} onChange={update} maxLength={50} autoComplete="off" />
              </Field>
              <Field label="مكان الولادة" htmlFor="birth_place">
                <Input id="birth_place" name="birth_place" value={form.birth_place} onChange={update} maxLength={200} autoComplete="off" />
              </Field>
              <Field label="نوع المكان" htmlFor="birth_place_type">
                <select id="birth_place_type" name="birth_place_type" value={form.birth_place_type} onChange={update} className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-ring">
                  <option value="hospital">مستشفى</option>
                  <option value="clinic">مركز صحي</option>
                  <option value="home">منزل</option>
                  <option value="other">أخرى</option>
                </select>
              </Field>
              <Field label="طريقة الولادة" htmlFor="delivery_method">
                <Input id="delivery_method" name="delivery_method" value={form.delivery_method} onChange={update} maxLength={50} autoComplete="off" placeholder="طبيعية، قيصرية…" />
              </Field>
              <div className="md:col-span-2">
                <Field label="ملاحظات سريرية مختصرة" htmlFor="notes">
                  <textarea id="notes" name="notes" value={form.notes} onChange={update} maxLength={2000} className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" />
                </Field>
              </div>
            </CardContent>
          </Card>

          <div className="flex flex-wrap justify-end gap-3">
            <Button type="button" variant="outline" onClick={() => { setForm(initialForm); setReceipt(null); }} disabled={registerNewborn.isPending}>مسح النموذج</Button>
            <Button type="submit" loading={registerNewborn.isPending} className="min-w-44 bg-emerald-700 hover:bg-emerald-800">
              <ClipboardCheck className="ms-2 h-4 w-4" aria-hidden="true" />
              إنشاء السجل الصحي المؤقت
            </Button>
          </div>
        </form>

        <aside className="space-y-5 xl:sticky xl:top-6 xl:self-start">
          <Card className="border-amber-100 bg-amber-50/45 shadow-sm">
            <CardContent className="p-5">
              <LockKeyhole className="h-5 w-5 text-amber-800" aria-hidden="true" />
              <h2 className="mt-3 font-semibold text-amber-950">حماية بيانات الهوية</h2>
              <p className="mt-2 text-sm leading-6 text-amber-900/80">لا تُنسخ أرقام الهوية إلى الملاحظات أو التقارير. يتحقق النظام من ارتباطها بسجلين موجودين ثم يحتفظ بمعرّفات السجلات فقط.</p>
            </CardContent>
          </Card>

          {receipt ? (
            <Card className="border-emerald-200 bg-emerald-50 shadow-sm" aria-live="polite">
              <CardContent className="p-5">
                <CheckCircle2 className="h-6 w-6 text-emerald-700" aria-hidden="true" />
                <h2 className="mt-3 font-semibold text-emerald-950">اكتمل التسجيل</h2>
                <p className="mt-1 text-sm text-emerald-900/75">الرقم الصحي التالي مؤقت، ويُستبدل ضمن مسار موثق عند إصدار البطاقة الوطنية.</p>
                <div className="mt-4 rounded-lg border border-emerald-200 bg-white px-3 py-3 font-mono text-base font-semibold tracking-wide text-emerald-900" dir="ltr">{receipt.health_number}</div>
                <div className="mt-3 flex flex-wrap gap-2"><Badge variant="success">سجل مؤقت</Badge><Badge variant="default">معرّف الطفل: {receipt.newborn_id ?? "—"}</Badge></div>
              </CardContent>
            </Card>
          ) : (
            <Card className="shadow-sm">
              <CardContent className="p-5">
                <Baby className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
                <h2 className="mt-3 font-semibold">بعد نجاح التسجيل</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">يُنشأ سجل صحي للطفل ويصبح جاهزاً لجدولة جرعات برنامج التحصين بحسب الجدول المرجعي المعتمد للمنشأة.</p>
              </CardContent>
            </Card>
          )}
        </aside>
      </div>
    </div>
  );
}

function Field({ label, required = false, htmlFor, children }: { label: string; required?: boolean; htmlFor: string; children: ReactNode }) {
  return <label htmlFor={htmlFor} className="grid gap-2 text-sm font-medium text-foreground">{label}{required ? <span className="me-1 text-destructive" aria-hidden="true">*</span> : null}{children}</label>;
}
