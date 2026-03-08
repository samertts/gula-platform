import React, { useEffect, useState } from "react";
import api from "../../api/client";

const STATUS_LABELS: Record<string, string> = {
  ordered:    "مطلوب",
  collected:  "مجموع",
  received:   "مستلم",
  processing: "قيد التحليل",
  completed:  "مكتمل",
  rejected:   "مرفوض",
};

export default function SamplesPage() {
  const [samples,  setSamples]  = useState<any[]>([]);
  const [status,   setStatus]   = useState("");
  const [loading,  setLoading]  = useState(true);
  const [rejectId, setRejectId] = useState<string | null>(null);
  const [reason,   setReason]   = useState("");

  function load() {
    setLoading(true);
    const params: any = {};
    if (status) params.status = status;
    api.get("/lab/samples", { params })
      .then(r => setSamples(r.data.samples || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [status]);

  async function collect(id: string) {
    try {
      await api.patch(`/lab/samples/${id}/collect`);
      load();
    } catch (err: any) {
      alert(err.response?.data?.error || "خطأ");
    }
  }

  async function receive(id: string) {
    try {
      await api.patch(`/lab/samples/${id}/receive`);
      load();
    } catch (err: any) {
      alert(err.response?.data?.error || "خطأ");
    }
  }

  async function confirmReject() {
    if (!rejectId) return;
    try {
      await api.patch(`/lab/samples/${rejectId}/reject`, { reason: reason || "لم يُحدد" });
      setRejectId(null);
      setReason("");
      load();
    } catch (err: any) {
      alert(err.response?.data?.error || "خطأ");
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>إدارة العينات</h2>
          <p>تتبع واستلام العينات المختبرية</p>
        </div>
      </div>

      <div className="filter-bar">
        <select value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">جميع الحالات</option>
          <option value="ordered">مطلوب</option>
          <option value="collected">مجموع</option>
          <option value="received">مستلم</option>
          <option value="processing">قيد التحليل</option>
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
                  <th>الباركود</th>
                  <th>المريض</th>
                  <th>نوع العينة</th>
                  <th>الحالة</th>
                  <th>تاريخ الجمع</th>
                  <th>تاريخ الاستلام</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {samples.map(s => (
                  <tr key={s.id}>
                    <td style={{ fontFamily: "monospace", fontSize: ".85rem", fontWeight: 600 }}>{s.barcode}</td>
                    <td>{s.patient_name}</td>
                    <td>{s.sample_type}</td>
                    <td><span className={`badge badge-${s.status}`}>{STATUS_LABELS[s.status] || s.status}</span></td>
                    <td style={{ fontSize: ".8rem" }}>
                      {s.collected_at ? new Date(s.collected_at).toLocaleString("ar-SA") : "—"}
                    </td>
                    <td style={{ fontSize: ".8rem" }}>
                      {s.received_at ? new Date(s.received_at).toLocaleString("ar-SA") : "—"}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 6 }}>
                        {s.status === "ordered" && (
                          <button className="btn btn-primary btn-sm" onClick={() => collect(s.id)}>جمع</button>
                        )}
                        {s.status === "collected" && (
                          <button className="btn btn-success btn-sm" onClick={() => receive(s.id)}>استلام</button>
                        )}
                        {["ordered", "collected"].includes(s.status) && (
                          <button className="btn btn-danger btn-sm" onClick={() => setRejectId(s.id)}>رفض</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!samples.length && (
                  <tr><td colSpan={7}>
                    <div className="empty-state"><p>لا توجد عينات</p></div>
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Reject Modal */}
      {rejectId && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 380 }}>
            <div className="modal-header">
              <h3>رفض العينة</h3>
              <button className="modal-close" onClick={() => setRejectId(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>سبب الرفض</label>
                <input value={reason} onChange={e => setReason(e.target.value)} placeholder="مثال: عينة غير كافية" />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-outline" onClick={() => setRejectId(null)}>إلغاء</button>
              <button className="btn btn-danger" onClick={confirmReject}>تأكيد الرفض</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
