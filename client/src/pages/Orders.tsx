import { DatabaseZap, Filter, Search } from "lucide-react";
import { useState } from "react";
import type { OrderStatus } from "@/lib/lab-data";
import { UiState } from "@/components/UiStates";
import { trpc } from "@/lib/trpc";

const filters: Array<"الكل" | OrderStatus> = ["الكل", "معلق", "قيد التنفيذ", "مكتمل"];

export default function Orders() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"الكل" | OrderStatus>("الكل");
  const orders = trpc.orders.list.useQuery({ limit: 25 });
  const result = orders.data;
  const connected = result?.state === "ready";

  return (
    <div className="page-stack page-enter" data-contract-id="orders.read" data-permission="orders:read" data-workspace-context="required">
      <section className="page-hero">
        <div><span className="section-kicker">إدارة دورة الفحص</span><h2>الطلبات المخبرية</h2><p>تعرض الحقول الدنيا للطلبات فقط بعد تحقق الخادم من سياق المختبر وصلاحية القراءة.</p></div>
        <span className="outline-button" aria-label="إضافة طلب غير متاحة في عقد القراءة"><DatabaseZap size={19} /> عرض للقراءة فقط</span>
      </section>
      <section className="orders-toolbar" aria-label="أدوات البحث والفلترة">
        <label className="search-control"><Search size={19} /><span className="sr-only">البحث في الطلبات</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="البحث غير متاح في عقد القراءة الأولي" disabled /></label>
        <div className="filter-tabs" role="tablist" aria-label="فلترة حالة الطلب">{filters.map((filter) => <button key={filter} role="tab" aria-selected={filter === status} className={filter === status ? "is-active" : ""} onClick={() => setStatus(filter)} disabled>{filter}</button>)}</div>
        <div className="toolbar-actions"><span className="outline-button"><Filter size={17} /> الفلاتر تؤجّل حتى توثيق قيم الحالة</span></div>
      </section>
      {orders.isLoading ? <UiState kind="loading" title="يجري التحقق من سياق المنشأة" description="لن يُطلب عقد الطلبات قبل تحقق الخادم من الربط والصلاحية." /> : orders.isError ? <UiState kind="error" title="يتطلب عرض الطلبات جلسة مستخدم" description="سجّل الدخول أولًا ثم أعد المحاولة. لا تُعرض أي بيانات عند تعذر إثبات الجلسة." onRetry={() => orders.refetch()} /> : !connected ? <section className="panel order-table-panel"><UiState kind="empty" title={result?.label ?? "قائمة الطلبات غير متاحة"} description={result?.description ?? "لا توجد بيانات تشغيلية معروضة قبل اكتمال التحقق الخادمي."} /><div className="helper-note"><Filter size={16} /> العقد المرجعي: {result?.contractId ?? "orders.read"} — الصلاحية المطلوبة: {result?.requiredPermission ?? "orders:read"}</div></section> : result.items?.length === 0 ? <UiState kind="empty" title="لا توجد طلبات ضمن النطاق" description="تم التحقق من السياق والصلاحية، لكن عقد القائمة لم يُعد طلبات ضمن نطاق العرض الحالي." /> : <section className="panel order-table-panel"><section className="orders-summary"><span><Filter size={16} /> {result.total ?? result.items?.length ?? 0} طلبًا ضمن النطاق الموثق</span><span>عرض للقراءة فقط</span></section><div className="table-wrap"><table><thead><tr><th>رقم الطلب</th><th>الحالة</th><th>الأولوية</th><th>تاريخ الإنشاء</th></tr></thead><tbody>{result.items?.map((order) => <tr key={order.id}><td>{order.accessionNumber ?? `#${order.id}`}</td><td>{order.status ?? "—"}</td><td>{order.priority ?? "—"}</td><td>{order.createdAt ? new Date(order.createdAt).toLocaleDateString("ar-IQ") : "—"}</td></tr>)}</tbody></table></div></section>}
    </div>
  );
}
