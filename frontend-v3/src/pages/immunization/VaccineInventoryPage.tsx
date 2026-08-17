/**
 * فلسفة التصميم: غرفة تشغيل صحية هادئة RTL؛ تسلسل بصري واضح، ألوان كهرمانية للإنذار
 * وأخضر للحالة السليمة، مع أقل قدر من بيانات المريض وعدم عرض أرقام اتصال.
 */
import { type FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { toast } from "@/hooks/useToast";
import { AlertTriangle, Boxes, CheckCircle2, Snowflake } from "lucide-react";

interface VaccineLot {
  id: string;
  catalog_id: string;
  lot_number: string;
  expiry_date: string;
  available_quantity: number;
  received_quantity: number;
  quarantined: boolean;
  quarantine_reason: string;
  storage_equipment_id: string;
}

interface InventoryReport {
  total_lots: number;
  available_doses: number;
  quarantined_lots: number;
  expired_lots: number;
  wasted_doses: number;
  dispensed_doses: number;
  out_of_range_readings: number;
}

function formatDate(value: string) {
  return value ? new Intl.DateTimeFormat("ar-IQ", { dateStyle: "medium" }).format(new Date(value)) : "غير محدد";
}

export function VaccineInventoryPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const canManage = ["master_admin", "admin", "lab_admin"].includes(user?.role ?? "");
  const canReport = ["master_admin", "ministry_admin", "province_admin", "admin", "lab_admin"].includes(user?.role ?? "");
  const [catalog, setCatalog] = useState({ vaccine_code: "", name: "", name_ar: "", storage_min_c: "", storage_max_c: "" });
  const [lot, setLot] = useState({ catalog_id: "", lot_number: "", quantity: "", expiry_date: "", storage_equipment_id: "" });
  const [reading, setReading] = useState({ equipment_id: "", temperature_c: "", minimum_allowed_c: "", maximum_allowed_c: "", notes: "" });

  const inventory = useQuery({
    queryKey: ["vaccine-inventory"],
    queryFn: () => api.get("/public-health/vaccinations/inventory").then((response) => response.data as VaccineLot[]),
  });
  const report = useQuery({
    queryKey: ["vaccine-inventory", "report"],
    queryFn: () => api.get("/public-health/vaccinations/inventory/report").then((response) => response.data as InventoryReport),
    enabled: canReport,
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["vaccine-inventory"] });
  };
  const createCatalog = useMutation({
    mutationFn: () => api.post("/public-health/vaccinations/inventory/catalog", {
      ...catalog,
      storage_min_c: catalog.storage_min_c ? Number(catalog.storage_min_c) : undefined,
      storage_max_c: catalog.storage_max_c ? Number(catalog.storage_max_c) : undefined,
    }),
    onSuccess: () => { setCatalog({ vaccine_code: "", name: "", name_ar: "", storage_min_c: "", storage_max_c: "" }); invalidate(); toast({ variant: "success", title: "تم حفظ تعريف اللقاح" }); },
    onError: () => toast({ variant: "destructive", title: "تعذر حفظ تعريف اللقاح" }),
  });
  const receiveLot = useMutation({
    mutationFn: () => api.post(`/public-health/vaccinations/inventory/catalog/${encodeURIComponent(lot.catalog_id)}/lots`, { ...lot, quantity: Number(lot.quantity), expiry_date: new Date(lot.expiry_date).toISOString() }),
    onSuccess: () => { setLot({ catalog_id: "", lot_number: "", quantity: "", expiry_date: "", storage_equipment_id: "" }); invalidate(); toast({ variant: "success", title: "تم تسجيل دفعة اللقاح" }); },
    onError: () => toast({ variant: "destructive", title: "تعذر تسجيل الدفعة" }),
  });
  const saveReading = useMutation({
    mutationFn: () => api.post("/public-health/vaccinations/inventory/cold-chain/readings", { ...reading, temperature_c: Number(reading.temperature_c), minimum_allowed_c: reading.minimum_allowed_c ? Number(reading.minimum_allowed_c) : undefined, maximum_allowed_c: reading.maximum_allowed_c ? Number(reading.maximum_allowed_c) : undefined }),
    onSuccess: () => { setReading({ equipment_id: "", temperature_c: "", minimum_allowed_c: "", maximum_allowed_c: "", notes: "" }); invalidate(); toast({ variant: "success", title: "تم تسجيل قراءة سلسلة التبريد" }); },
    onError: () => toast({ variant: "destructive", title: "تعذر تسجيل القراءة" }),
  });

  const submit = (event: FormEvent<HTMLFormElement>, action: () => void) => { event.preventDefault(); action(); };
  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="مخزون اللقاحات وسلسلة التبريد" description="إدارة الدفعات، الصلاحية، الحجر، الاستهلاك المرتبط بالجرعة، وقراءات سلسلة التبريد داخل المنشأة." />
      {canReport && report.data ? <section className="grid gap-4 md:grid-cols-4" aria-label="مؤشرات المخزون">
        <Metric label="الجرعات المتاحة" value={report.data.available_doses} tone="sky" icon={Boxes} />
        <Metric label="الدفعات المحجورة" value={report.data.quarantined_lots} tone="amber" icon={AlertTriangle} />
        <Metric label="الجرعات المصروفة" value={report.data.dispensed_doses} tone="emerald" icon={CheckCircle2} />
        <Metric label="انحرافات التبريد" value={report.data.out_of_range_readings} tone="amber" icon={Snowflake} />
      </section> : null}
      <div className="grid gap-5 xl:grid-cols-2">
        {canManage ? <Card><CardHeader><CardTitle>تعريف لقاح قابل للاعتماد</CardTitle><p className="text-sm text-muted-foreground">لا يُضاف جدول جرعات من هذه الشاشة؛ التعريف يخص الكتالوج والمجال الحراري فقط.</p></CardHeader><CardContent><form className="grid gap-3 md:grid-cols-2" onSubmit={(event) => submit(event, () => createCatalog.mutate())}>
          <Input aria-label="رمز اللقاح" placeholder="رمز اللقاح" value={catalog.vaccine_code} onChange={(e) => setCatalog({ ...catalog, vaccine_code: e.target.value })} required />
          <Input aria-label="اسم اللقاح" placeholder="اسم اللقاح" value={catalog.name} onChange={(e) => setCatalog({ ...catalog, name: e.target.value })} required />
          <Input aria-label="الاسم العربي" placeholder="الاسم العربي" value={catalog.name_ar} onChange={(e) => setCatalog({ ...catalog, name_ar: e.target.value })} />
          <Input aria-label="الحد الأدنى للحرارة" type="number" placeholder="الحد الأدنى °C" value={catalog.storage_min_c} onChange={(e) => setCatalog({ ...catalog, storage_min_c: e.target.value })} />
          <Input aria-label="الحد الأعلى للحرارة" type="number" placeholder="الحد الأعلى °C" value={catalog.storage_max_c} onChange={(e) => setCatalog({ ...catalog, storage_max_c: e.target.value })} />
          <div className="md:col-span-2 flex justify-end"><Button type="submit" loading={createCatalog.isPending}>حفظ التعريف</Button></div>
        </form></CardContent></Card> : null}
        {canManage ? <Card><CardHeader><CardTitle>استلام دفعة</CardTitle><p className="text-sm text-muted-foreground">تُمنع الدفعات المنتهية، ويُحفظ رقم التشغيلة مع أثر تدقيقي.</p></CardHeader><CardContent><form className="grid gap-3 md:grid-cols-2" onSubmit={(event) => submit(event, () => receiveLot.mutate())}>
          <Input aria-label="معرّف تعريف اللقاح" placeholder="معرّف تعريف اللقاح" value={lot.catalog_id} onChange={(e) => setLot({ ...lot, catalog_id: e.target.value })} required />
          <Input aria-label="رقم التشغيلة" placeholder="رقم التشغيلة" value={lot.lot_number} onChange={(e) => setLot({ ...lot, lot_number: e.target.value })} required />
          <Input aria-label="الكمية" type="number" min="1" placeholder="الكمية" value={lot.quantity} onChange={(e) => setLot({ ...lot, quantity: e.target.value })} required />
          <Input aria-label="تاريخ الانتهاء" type="date" value={lot.expiry_date} onChange={(e) => setLot({ ...lot, expiry_date: e.target.value })} required />
          <Input aria-label="معرّف جهاز التبريد" placeholder="معرّف جهاز التبريد" value={lot.storage_equipment_id} onChange={(e) => setLot({ ...lot, storage_equipment_id: e.target.value })} />
          <div className="md:col-span-2 flex justify-end"><Button type="submit" loading={receiveLot.isPending}>تسجيل الدفعة</Button></div>
        </form></CardContent></Card> : null}
        {canManage ? <Card><CardHeader><CardTitle>قراءة سلسلة التبريد</CardTitle><p className="text-sm text-muted-foreground">عند خروج القراءة عن المجال تُحجر الدفعات المرتبطة بالجهاز للمراجعة.</p></CardHeader><CardContent><form className="grid gap-3 md:grid-cols-2" onSubmit={(event) => submit(event, () => saveReading.mutate())}>
          <Input aria-label="معرّف الجهاز" placeholder="معرّف الجهاز" value={reading.equipment_id} onChange={(e) => setReading({ ...reading, equipment_id: e.target.value })} required />
          <Input aria-label="درجة الحرارة" type="number" step="0.1" placeholder="درجة الحرارة °C" value={reading.temperature_c} onChange={(e) => setReading({ ...reading, temperature_c: e.target.value })} required />
          <Input aria-label="الحد الأدنى" type="number" step="0.1" placeholder="الحد الأدنى °C" value={reading.minimum_allowed_c} onChange={(e) => setReading({ ...reading, minimum_allowed_c: e.target.value })} />
          <Input aria-label="الحد الأعلى" type="number" step="0.1" placeholder="الحد الأعلى °C" value={reading.maximum_allowed_c} onChange={(e) => setReading({ ...reading, maximum_allowed_c: e.target.value })} />
          <div className="md:col-span-2 flex justify-end"><Button type="submit" loading={saveReading.isPending}>حفظ القراءة</Button></div>
        </form></CardContent></Card> : null}
      </div>
      <Card><CardHeader><CardTitle>الدفعات الحالية</CardTitle></CardHeader><CardContent>{inventory.isLoading ? <p className="py-8 text-center text-sm text-muted-foreground">يجري تحميل المخزون…</p> : <div className="space-y-2">{(inventory.data ?? []).map((item) => <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3"><div><p className="font-medium">{item.lot_number}</p><p className="text-xs text-muted-foreground">الانتهاء: {formatDate(item.expiry_date)} · الجهاز: {item.storage_equipment_id || "غير محدد"}</p></div><div className="flex items-center gap-2"><span className="text-sm">{item.available_quantity} جرعة</span><Badge variant={item.quarantined ? "warning" : "success"}>{item.quarantined ? "محجورة" : "متاحة"}</Badge></div></div>)}{!inventory.isLoading && inventory.data?.length === 0 ? <p className="py-8 text-center text-sm text-muted-foreground">لا توجد دفعات مسجلة للمنشأة.</p> : null}</div>}</CardContent></Card>
    </div>
  );
}

function Metric({ label, value, tone, icon: Icon }: { label: string; value: number; tone: "sky" | "amber" | "emerald"; icon: typeof Boxes }) {
  const styles = { sky: "bg-sky-50 text-sky-900", amber: "bg-amber-50 text-amber-900", emerald: "bg-emerald-50 text-emerald-900" };
  return <Card className={styles[tone]}><CardContent className="flex items-center justify-between p-4"><div><p className="text-sm opacity-75">{label}</p><p className="mt-1 text-2xl font-semibold">{value}</p></div><Icon className="h-6 w-6" aria-hidden="true" /></CardContent></Card>;
}
