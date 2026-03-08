import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import { useToast } from "../../components/Toast";

const PRIORITY_LABEL: Record<string, string> = {
  stat:   "⚡ فوري",
  urgent: "⚠ عاجل",
  normal: "عادي",
};

const PRIORITY_COLOR: Record<string, string> = {
  stat:   "var(--danger)",
  urgent: "var(--warning)",
  normal: "var(--gray-600)",
};

export default function WorkQueuePage() {
  const [queue,   setQueue]   = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  function load() {
    setLoading(true);
    api.get("/lab/work-queue")
      .then(r => setQueue(r.data.queue))
      .catch(() => toast.error("فشل تحميل قائمة العمل"))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function collectSample(id: string) {
    try {
      await api.patch(`/lab/samples/${id}/collect`);
      toast.success("تم تسجيل جمع العينة");
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.error || "خطأ في الجمع");
    }
  }

  async function receiveSample(id: string) {
    try {
      await api.patch(`/lab/samples/${id}/receive`);
      toast.success("تم استلام العينة في المختبر");
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.error || "خطأ في الاستلام");
    }
  }

  async function approveAll(orderId: string) {
    try {
      const r = await api.post(`/lab/orders/${orderId}/approve-all`);
      toast.success(`تمت الموافقة على ${r.data.approved} نتيجة`);
      load();
    } catch (err: any) {
      toast.error("خطأ في الموافقة");
    }
  }

  async function releaseOrder(orderId: string) {
    try {
      await api.post(`/lab/orders/${orderId}/release`);
      toast.success("تم إصدار النتائج للمريض");
      load();
    } catch (err: any) {
      toast.error("خطأ في الإصدار");
    }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>;

  const q = queue || {};
  const totalPending = (q.to_collect?.length || 0) + (q.to_process?.length || 0) +
    (q.enter_results?.length || 0) + (q.to_approve?.length || 0) + (q.to_release?.length || 0);

  function PriorityBadge({ p }: { p: string }) {
    return <span style={{ color: PRIORITY_COLOR[p], fontWeight: 700, fontSize: ".8rem" }}>{PRIORITY_LABEL[p]}</span>;
  }

  function Section({ title, count, color, children }: any) {
    if (!count) return null;
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
          <div className="card-title" style={{ margin: 0, color }}>
            {title} <span style={{ background: color, color: "#fff", borderRadius: 20, padding: "2px 8px", fontSize: ".75rem", marginRight: 8 }}>{count}</span>
          </div>
        </div>
        {children}
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>قائمة العمل</h2>
          <p>{totalPending > 0 ? `${totalPending} مهمة تحتاج إجراء` : "لا توجد مهام معلقة ✓"}</p>
        </div>
        <button className="btn btn-outline" onClick={load}>🔄 تحديث</button>
      </div>

      {totalPending === 0 && (
        <div className="card">
          <div className="empty-state">
            <p>✅ أحسنت! لا توجد مهام معلقة</p>
            <span>جميع الطلبات مكتملة</span>
          </div>
        </div>
      )}

      {/* 1. جمع العينات */}
      <Section title="🧪 عينات تحتاج جمع" count={q.to_collect?.length} color="var(--warning)">
        <div className="table-wrap">
          <table>
            <thead><tr><th>الباركود</th><th>المريض</th><th>النوع</th><th>الأولوية</th><th>إجراء</th></tr></thead>
            <tbody>
              {q.to_collect?.map((s: any) => (
                <tr key={s.id}>
                  <td style={{ fontFamily: "monospace", fontWeight: 600 }}>{s.barcode}</td>
                  <td>{s.patient_name}</td>
                  <td>{s.sample_type}</td>
                  <td><PriorityBadge p={s.priority} /></td>
                  <td><button className="btn btn-primary btn-sm" onClick={() => collectSample(s.id)}>جمع العينة</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* 2. إدخال المختبر */}
      <Section title="🔬 عينات مستلمة للتحليل" count={q.to_process?.length} color="var(--primary)">
        <div className="table-wrap">
          <table>
            <thead><tr><th>الباركود</th><th>المريض</th><th>النوع</th><th>الأولوية</th><th>إجراء</th></tr></thead>
            <tbody>
              {q.to_process?.map((s: any) => (
                <tr key={s.id}>
                  <td style={{ fontFamily: "monospace", fontWeight: 600 }}>{s.barcode}</td>
                  <td>{s.patient_name}</td>
                  <td>{s.sample_type}</td>
                  <td><PriorityBadge p={s.priority} /></td>
                  <td>
                    <Link to="/lab/results" className="btn btn-primary btn-sm">إدخال نتائج</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* 3. نتائج تحتاج موافقة */}
      <Section title="✅ نتائج تحتاج موافقة" count={q.to_approve?.length} color="var(--success)">
        <div className="table-wrap">
          <table>
            <thead><tr><th>المريض</th><th>الفحص</th><th>النتيجة</th><th>الحالة</th><th>الأولوية</th><th>وقت الإدخال</th></tr></thead>
            <tbody>
              {q.to_approve?.map((r: any) => (
                <tr key={r.id} className={r.is_abnormal ? "result-row-abnormal" : ""}>
                  <td>{r.patient_name}</td>
                  <td>{r.name_ar}</td>
                  <td>
                    <span className={r.is_abnormal ? (r.abnormal_flag === "H" ? "value-high" : "value-low") : "value-normal"}>
                      {r.value} {r.abnormal_flag && <span className={`badge badge-${r.abnormal_flag}`}>{r.abnormal_flag}</span>}
                    </span>
                  </td>
                  <td>{r.is_abnormal ? <span className="badge badge-abnormal">غير طبيعي</span> : <span className="badge badge-normal">طبيعي</span>}</td>
                  <td><PriorityBadge p={r.priority} /></td>
                  <td style={{ fontSize: ".75rem", color: "var(--gray-500)" }}>
                    {new Date(r.created_at).toLocaleString("ar-SA")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* 4. طلبات جاهزة للإصدار */}
      <Section title="📤 طلبات جاهزة للإصدار" count={q.to_release?.length} color="var(--primary)">
        <div className="table-wrap">
          <table>
            <thead><tr><th>رقم الطلب</th><th>المريض</th><th>عدد النتائج</th><th>الأولوية</th><th>إجراء</th></tr></thead>
            <tbody>
              {q.to_release?.map((o: any) => (
                <tr key={o.id}>
                  <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{o.id?.slice(0, 8)}</td>
                  <td>{o.patient_name}</td>
                  <td>{o.result_count} نتيجة معتمدة</td>
                  <td><PriorityBadge p={o.priority} /></td>
                  <td>
                    <div style={{ display: "flex", gap: 6 }}>
                      <button className="btn btn-outline btn-sm" onClick={() => approveAll(o.id)}>موافقة جماعية</button>
                      <button className="btn btn-success btn-sm" onClick={() => releaseOrder(o.id)}>إصدار للمريض</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}
