import { DatabaseZap, Filter, Search } from "lucide-react";
import { useState } from "react";
import type { OrderStatus } from "@/lib/lab-data";
import { UiState } from "@/components/UiStates";

const filters: Array<"الكل" | OrderStatus> = ["الكل", "معلق", "قيد التنفيذ", "مكتمل"];

export default function Orders() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"الكل" | OrderStatus>("الكل");
  const connected = false;

  return (
    <div className="page-stack page-enter">
      <section className="page-hero">
        <div><span className="section-kicker">إدارة دورة الفحص</span><h2>الطلبات المخبرية</h2><p>تعرض قائمة الطلبات بعد ربط عقد قائمة الطلبات وتطبيق صلاحيات المنشأة والمستخدم.</p></div>
        <span className="outline-button" aria-label="إضافة طلب غير متاحة قبل ربط الخدمة"><DatabaseZap size={19} /> الخدمة غير متصلة</span>
      </section>
      <section className="orders-toolbar" aria-label="أدوات البحث والفلترة">
        <label className="search-control"><Search size={19} /><span className="sr-only">البحث في الطلبات</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="سيُتاح البحث بعد ربط قائمة الطلبات" disabled={!connected} /></label>
        <div className="filter-tabs" role="tablist" aria-label="فلترة حالة الطلب">{filters.map((filter) => <button key={filter} role="tab" aria-selected={filter === status} className={filter === status ? "is-active" : ""} onClick={() => setStatus(filter)} disabled={!connected}>{filter}</button>)}</div>
        <div className="toolbar-actions"><span className="outline-button"><Filter size={17} /> لا توجد فلاتر متاحة</span></div>
      </section>
      <section className="orders-summary"><span><Filter size={16} /> لا توجد بيانات متاحة للعرض</span><span>تُحدَّث هذه الشاشة عند اكتمال الربط</span></section>
      <section className="panel order-table-panel">
        <UiState kind="empty" title="لا توجد طلبات تشغيلية معروضة" description="لا تستخدم هذه الواجهة بيانات مرضى أو طلبات نموذجية. اربط مصدر الطلبات المعتمد وطبّق تفويض المستخدم لإظهار النتائج والبحث والفلترة." />
      </section>
    </div>
  );
}
