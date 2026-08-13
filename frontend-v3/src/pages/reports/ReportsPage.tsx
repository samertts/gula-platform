export function ReportsPage() {
  return (
    <section
      dir="rtl"
      className="space-y-6"
      data-contract-status="unbound"
      data-governance-state="safe-empty"
      aria-labelledby="reports-title"
    >
      <div>
        <h1 id="reports-title" className="text-2xl font-bold">
          التقارير
        </h1>
        <p className="text-muted-foreground">سطح التقارير التشغيلية</p>
      </div>

      <div className="rounded-lg border border-dashed p-8 text-center">
        <h2 className="text-lg font-semibold">لا توجد تقارير تشغيلية معروضة</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          ستظهر التقارير بعد ربط مصدر البيانات المعتمد.
        </p>
      </div>
    </section>
  );
}

export default ReportsPage;
