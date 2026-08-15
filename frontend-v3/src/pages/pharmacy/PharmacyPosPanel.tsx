import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Plus, Search, ShoppingCart, Trash2 } from "lucide-react";
import { pharmacyApi, type PharmacyDrugRecord, type PharmacySaleRequest } from "@/api/endpoints";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type CartLine = {
  drug: PharmacyDrugRecord;
  quantity: number;
};

function requestKey(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `pos-${Date.now()}`;
}

export default function PharmacyPosPanel() {
  const [search, setSearch] = useState("");
  const [patientId, setPatientId] = useState("");
  const [citizenId, setCitizenId] = useState("");
  const [billingPatientId, setBillingPatientId] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [lastSale, setLastSale] = useState<string | null>(null);

  const summary = useQuery({
    queryKey: ["pharmacy", "pos", "summary"],
    queryFn: () => pharmacyApi.summary(30),
    staleTime: 30_000,
  });

  const drugs = useQuery({
    queryKey: ["pharmacy", "pos", "drugs", search],
    queryFn: () => pharmacyApi.drugs(search.trim()),
    enabled: search.trim().length >= 2,
    staleTime: 30_000,
  });

  const saleMutation = useMutation({
    mutationFn: (payload: PharmacySaleRequest) => pharmacyApi.createSale(payload, payload.idempotency_key ?? requestKey()),
    onSuccess: (sale) => {
      setLastSale(`${sale.sale_number} · ${sale.total_amount.toLocaleString("ar-IQ")} ${sale.currency}`);
      setCart([]);
    },
  });

  const totalUnits = useMemo(() => cart.reduce((sum, line) => sum + line.quantity, 0), [cart]);

  const addToCart = (drug: PharmacyDrugRecord) => {
    setCart((current) => {
      const existing = current.find((line) => line.drug.id === drug.id);
      if (existing) return current.map((line) => line.drug.id === drug.id ? { ...line, quantity: line.quantity + 1 } : line);
      return [...current, { drug, quantity: 1 }];
    });
    setSearch("");
  };

  const submitSale = () => {
    if (!cart.length || !billingPatientId.trim()) return;
    const payload: PharmacySaleRequest = {
      patient_id: patientId.trim() || undefined,
      citizen_id: citizenId.trim() || undefined,
      billing_patient_id: Number(billingPatientId),
      encounter_ref: `PHARMACY-POS-${new Date().toISOString().slice(0, 10)}`,
      payment_method: "synthetic_settlement",
      issue_invoice: true,
      idempotency_key: requestKey(),
      lines: cart.map((line) => ({ drug_catalog_id: line.drug.id, quantity: line.quantity, quantity_unit: "unit" })),
    };
    saleMutation.mutate(payload);
  };

  return (
    <div dir="rtl">
      <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {[
          ["مبيعات 30 يومًا", summary.data ? `${Number(summary.data.sales_total).toLocaleString("ar-IQ")} IQD` : "—"],
          ["تكلفة المبيعات", summary.data ? `${Number(summary.data.cost_total).toLocaleString("ar-IQ")} IQD` : "—"],
          ["الربح الإجمالي", summary.data ? `${Number(summary.data.gross_profit).toLocaleString("ar-IQ")} IQD` : "—"],
          ["نواقص", summary.data?.low_stock_count ?? "—"],
          ["أصناف راكدة", summary.data?.stagnant_items.length ?? "—"],
        ].map(([label, value]) => <Card key={label}><CardContent className="p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-lg font-bold">{value}</p></CardContent></Card>)}
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(300px,0.8fr)]">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base"><Search className="h-5 w-5 text-indigo-600" />بيع سريع بالباركود أو الاسم</CardTitle>
          <p className="text-xs leading-6 text-muted-foreground">يبحث النظام في الكتالوج المؤسسي، ثم يختار الدفعة الصالحة الأقرب انتهاءً تلقائيًا عند الإتمام.</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="امسح الباركود أو اكتب اسم الدواء..." className="pr-9" aria-label="بحث الدواء بالباركود أو الاسم" />
          </div>
          {drugs.isLoading && <p className="text-sm text-muted-foreground">جارٍ البحث في كتالوج المؤسسة...</p>}
          {drugs.error && <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">تعذر تحميل الكتالوج. تحقق من جلسة المؤسسة أو عقد API.</p>}
          <div className="space-y-2">
            {(drugs.data?.items ?? []).map((drug) => (
              <button key={drug.id} type="button" onClick={() => addToCart(drug)} className="flex w-full items-center justify-between rounded-xl border p-3 text-right transition hover:border-indigo-400 hover:bg-indigo-50/50">
                <span><strong className="block">{drug.name_ar || drug.name}</strong><span className="text-xs text-muted-foreground">{drug.generic_name || drug.brand_name || drug.code} · {drug.barcode_gs1 || "بدون باركود"}</span></span>
                <Plus className="h-4 w-4 text-indigo-600" />
              </button>
            ))}
            {search.trim().length >= 2 && !drugs.isLoading && !drugs.data?.items?.length && <p className="rounded-lg border border-dashed p-5 text-center text-sm text-muted-foreground">لا توجد أصناف مطابقة.</p>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShoppingCart className="h-5 w-5 text-indigo-600" />السلة والربط بالسجل</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Input value={billingPatientId} onChange={(event) => setBillingPatientId(event.target.value.replace(/[^0-9]/g, ""))} placeholder="معرف Patient للفوترة (مطلوب)" inputMode="numeric" aria-label="معرف المريض للفوترة" />
          <Input value={citizenId} onChange={(event) => setCitizenId(event.target.value)} placeholder="معرف المواطن الوطني (اختياري لسجل العلاج)" aria-label="معرف المواطن" />
          <Input value={patientId} onChange={(event) => setPatientId(event.target.value)} placeholder="معرف Patient/FHIR (اختياري)" aria-label="معرف السجل الصحي" />
          <div className="space-y-2">
            {cart.map((line) => (
              <div key={line.drug.id} className="flex items-center justify-between gap-2 rounded-lg border p-3">
                <div><p className="font-semibold">{line.drug.name_ar || line.drug.name}</p><p className="text-xs text-muted-foreground">{line.quantity} وحدة</p></div>
                <div className="flex items-center gap-1"><Button size="sm" variant="outline" type="button" onClick={() => setCart((current) => current.map((item) => item.drug.id === line.drug.id ? { ...item, quantity: item.quantity + 1 } : item))}>+</Button><Button size="sm" variant="ghost" type="button" onClick={() => setCart((current) => current.filter((item) => item.drug.id !== line.drug.id))} aria-label={`حذف ${line.drug.name}`}><Trash2 className="h-4 w-4" /></Button></div>
              </div>
            ))}
            {!cart.length && <p className="rounded-lg border border-dashed p-5 text-center text-sm text-muted-foreground">السلة فارغة.</p>}
          </div>
          <div className="flex items-center justify-between rounded-lg bg-muted/50 p-3 text-sm"><span>إجمالي الوحدات</span><Badge variant="outline">{totalUnits}</Badge></div>
          <Button type="button" className="w-full" disabled={!cart.length || !billingPatientId.trim() || saleMutation.isPending} onClick={submitSale}>{saleMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}إتمام البيع وإصدار الفاتورة</Button>
          {saleMutation.error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">تعذر إتمام البيع. لم يتم اعتماد الفاتورة أو خصم المخزون.</p>}
          {lastSale && <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">تم البيع: {lastSale}. سُجلت حركة المخزون، والفاتورة، وسجل الصرف إن تم توفير معرف المواطن.</p>}
        </CardContent>
      </Card>
      </div>
      {summary.data?.synthetic && <p className="mt-3 text-xs text-muted-foreground">التقرير يعتمد على سجلات GULA الاصطناعية الحالية ولا يتصل بنظام دفع أو مورد خارجي.</p>}
    </div>
  );
}
