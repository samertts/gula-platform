import React, { useEffect, useState } from "react";
import api from "../../api/client";

const STATUS_LABELS: Record<string, string> = {
  pending:    "انتظار",
  received:   "مستلم",
  processing: "قيد التحليل",
  completed:  "مكتمل",
  cancelled:  "ملغى",
};

const PRIORITY_LABELS: Record<string, string> = {
  normal: "عادي",
  urgent: "عاجل",
  stat:   "فوري",
};

export default function OrdersPage() {
  const [orders,  setOrders]  = useState<any[]>([]);
  const [status,  setStatus]  = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);

  function load() {
    setLoading(true);
    const params: any = {};
    if (status) params.status = status;
    api.get("/lab/orders", { params })
      .then(r => setOrders(r.data.orders || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [status]);

  async function release(orderId: string) {
    if (!confirm("إصدار النتائج للمريض؟")) return;
    try {
      await api.post(`/lab/orders/${orderId}/release`);
      load();
    } catch (err: any) {
      alert(err.response?.data?.error || "خطأ في الإصدار");
    }
  }

  async function viewOrder(id: string) {
    const r = await api.get(`/lab/orders/${id}`);
    setSelected(r.data);
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>طلبات المختبر</h2>
          <p>جميع طلبات الفحوصات الواردة</p>
        </div>
      </div>

      <div className="filter-bar">
        <select value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">جميع الحالات</option>
          <option value="pending">انتظار</option>
          <option value="received">مستلم</option>
          <option value="processing">قيد التحليل</option>
          <option value="completed">مكتمل</option>
        </select>
        <button className="btn btn-outline btn-sm" onClick={load}>تحديث</button>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading-page"><div className="spinner" /></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>رقم الطلب</th>
                  <th>المريض</th>
                  <th>الرقم الوطني</th>
                  <th>الطبيب</th>
                  <th>الأولوية</th>
                  <th>الحالة</th>
                  <th>التاريخ</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(o => (
                  <tr key={o.id}>
                    <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{o.id?.slice(0, 8)}</td>
                    <td>{o.patient_name}</td>
                    <td>{o.patient_national_id || "—"}</td>
                    <td>{o.doctor_name || "—"}</td>
                    <td>
                      <span className={`badge ${o.priority === "stat" ? "badge-abnormal" : o.priority === "urgent" ? "badge-pending" : "badge-processing"}`}>
                        {PRIORITY_LABELS[o.priority] || o.priority}
                      </span>
                    </td>
                    <td><span className={`badge badge-${o.status}`}>{STATUS_LABELS[o.status] || o.status}</span></td>
                    <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                      {new Date(o.created_at).toLocaleDateString("ar-SA")}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button className="btn btn-outline btn-sm" onClick={() => viewOrder(o.id)}>تفاصيل</button>
                        {o.status === "processing" && (
                          <button className="btn btn-success btn-sm" onClick={() => release(o.id)}>إصدار</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!orders.length && (
                  <tr><td colSpan={8}>
                    <div className="empty-state"><p>لا توجد طلبات</p></div>
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>تفاصيل الطلب</h3>
              <button className="modal-close" onClick={() => setSelected(null)}>×</button>
            </div>
            <div className="modal-body">
              <p><strong>المريض:</strong> {selected.order?.patient_name}</p>
              <p><strong>الحالة:</strong> {STATUS_LABELS[selected.order?.status]}</p>
              <p style={{ marginTop: 12, fontWeight: 600 }}>الفحوصات المطلوبة:</p>
              {selected.items?.map((item: any) => (
                <div key={item.id} style={{ padding: "6px 0", borderBottom: "1px solid var(--gray-100)" }}>
                  {item.name_ar} ({item.code})
                  <span className={`badge badge-${item.status}`} style={{ marginRight: 8 }}>{item.status}</span>
                </div>
              ))}
              <p style={{ marginTop: 12, fontWeight: 600 }}>العينات:</p>
              {selected.samples?.map((s: any) => (
                <div key={s.id} style={{ padding: "6px 0" }}>
                  {s.sample_type} — {s.barcode}
                  <span className={`badge badge-${s.status}`} style={{ marginRight: 8 }}>{s.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
