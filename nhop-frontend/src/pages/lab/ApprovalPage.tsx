import React, { useEffect, useState } from "react";
import api from "../../api/client";
import { useToast } from "../../components/Toast";

export default function ApprovalPage() {
  const [orders,   setOrders]   = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [results,  setResults]  = useState<any[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const toast = useToast();

  /* load orders in processing state */
  function loadOrders() {
    setLoading(true);
    api.get("/lab/orders", { params: { status: "processing" } })
      .then(r => setOrders(r.data.orders || []))
      .catch(() => toast.error("فشل تحميل الطلبات"))
      .finally(() => setLoading(false));
  }

  useEffect(() => { loadOrders(); }, []);

  async function selectOrder(order: any) {
    setSelected(order);
    setResults([]);
    try {
      const r = await api.get(`/lab/orders/${order.id}/pending-results`);
      setResults(r.data.results || []);
    } catch {
      toast.error("فشل تحميل النتائج");
    }
  }

  async function approveOne(resultId: string, notes = "") {
    try {
      await api.patch(`/lab/results/${resultId}/approve`, { notes });
      setResults(prev => prev.filter(r => r.id !== resultId));
      toast.success("تم اعتماد النتيجة");
    } catch (err: any) {
      toast.error(err.response?.data?.error || "خطأ في الاعتماد");
    }
  }

  async function approveAll() {
    if (!selected) return;
    setSubmitting(true);
    try {
      const r = await api.post(`/lab/orders/${selected.id}/approve-all`);
      toast.success(`تم اعتماد ${r.data.approved} نتيجة`);
      setResults([]);
      loadOrders();
      setSelected(null);
    } catch (err: any) {
      toast.error(err.response?.data?.error || "خطأ في الاعتماد الجماعي");
    } finally {
      setSubmitting(false);
    }
  }

  async function releaseOrder() {
    if (!selected) return;
    if (!confirm("إصدار كافة النتائج المعتمدة للمريض؟")) return;
    try {
      await api.post(`/lab/orders/${selected.id}/release`);
      toast.success("تم إصدار النتائج للمريض بنجاح");
      setSelected(null);
      setResults([]);
      loadOrders();
    } catch (err: any) {
      toast.error(err.response?.data?.error || "خطأ في الإصدار");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>اعتماد النتائج</h2>
          <p>مراجعة واعتماد نتائج الفحوصات قبل إصدارها للمريض</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 16 }}>
        {/* Orders List */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--gray-200)", fontWeight: 600, display: "flex", justifyContent: "space-between" }}>
            <span>طلبات قيد التحليل</span>
            <span style={{ background: "var(--warning)", color: "#fff", borderRadius: 20, padding: "2px 8px", fontSize: ".75rem" }}>{orders.length}</span>
          </div>
          {loading ? <div className="spinner" /> : (
            <div style={{ overflow: "auto", maxHeight: 500 }}>
              {orders.map(o => (
                <div key={o.id}
                  onClick={() => selectOrder(o)}
                  style={{
                    padding: "12px 16px",
                    cursor: "pointer",
                    borderBottom: "1px solid var(--gray-100)",
                    background: selected?.id === o.id ? "var(--primary-lt)" : "#fff",
                    borderRight: selected?.id === o.id ? "3px solid var(--primary)" : "3px solid transparent",
                  }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontWeight: 600, fontSize: ".875rem" }}>{o.patient_name}</span>
                    <span style={{
                      color: o.priority === "stat" ? "var(--danger)" : o.priority === "urgent" ? "var(--warning)" : "var(--gray-400)",
                      fontSize: ".75rem", fontWeight: 700
                    }}>
                      {o.priority === "stat" ? "⚡STAT" : o.priority === "urgent" ? "⚠عاجل" : "عادي"}
                    </span>
                  </div>
                  <div style={{ fontSize: ".75rem", color: "var(--gray-500)", marginTop: 4 }}>
                    #{o.id?.slice(0, 8)} — {new Date(o.created_at).toLocaleDateString("ar-SA")}
                  </div>
                </div>
              ))}
              {!orders.length && (
                <div className="empty-state" style={{ padding: 24 }}>
                  <p>لا توجد طلبات</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Results Approval */}
        <div className="card">
          {!selected ? (
            <div className="empty-state">
              <p>اختر طلباً للمراجعة</p>
              <span>اختر طلباً من اليمين لعرض نتائجه واعتمادها</span>
            </div>
          ) : (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
                <div>
                  <strong>{selected.patient_name}</strong>
                  <span style={{ color: "var(--gray-500)", fontSize: ".875rem", marginRight: 10 }}>
                    #{selected.id?.slice(0, 8)}
                  </span>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {results.length > 0 && (
                    <button className="btn btn-outline" onClick={approveAll} disabled={submitting}>
                      ✓ اعتماد الكل ({results.length})
                    </button>
                  )}
                  <button className="btn btn-success" onClick={releaseOrder}>
                    📤 إصدار للمريض
                  </button>
                </div>
              </div>

              {results.length === 0 ? (
                <div className="alert alert-success">
                  ✅ جميع النتائج معتمدة — يمكن إصدارها للمريض
                </div>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>الفحص</th>
                        <th>النتيجة</th>
                        <th>المرجع</th>
                        <th>الحالة</th>
                        <th>الفني</th>
                        <th>إجراء</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map((r: any) => (
                        <tr key={r.id} className={r.is_abnormal ? "result-row-abnormal" : "result-row-normal"}>
                          <td>
                            <div style={{ fontWeight: 500 }}>{r.name_ar}</div>
                            <div style={{ fontSize: ".75rem", color: "var(--gray-400)" }}>{r.code}</div>
                          </td>
                          <td>
                            <span className={r.is_abnormal ? (r.abnormal_flag === "H" ? "value-high" : "value-low") : "value-normal"}>
                              <strong>{r.value}</strong> {r.unit}
                            </span>
                            {r.is_abnormal && (
                              <span className={`badge badge-${r.abnormal_flag}`} style={{ marginRight: 6 }}>
                                {r.abnormal_flag === "H" ? "↑" : "↓"} {r.abnormal_flag}
                              </span>
                            )}
                          </td>
                          <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                            {r.normal_range_min != null && r.normal_range_max != null
                              ? `${r.normal_range_min}–${r.normal_range_max} ${r.unit || ""}`
                              : r.normal_range_text || "—"}
                          </td>
                          <td>
                            {r.is_abnormal
                              ? <span className="badge badge-abnormal">⚠ غير طبيعي</span>
                              : <span className="badge badge-normal">✓ طبيعي</span>}
                          </td>
                          <td style={{ fontSize: ".8rem" }}>{r.tech_name || "—"}</td>
                          <td>
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => approveOne(r.id)}>
                              اعتماد
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
