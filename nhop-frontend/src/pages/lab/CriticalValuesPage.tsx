import React, { useEffect, useState } from "react";
import api from "../../api/client";
import { useToast } from "../../components/Toast";

export default function CriticalValuesPage() {
  const toast = useToast();
  const [criticals, setCriticals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/lab/critical-values")
      .then(r => setCriticals(r.data.critical_results || []))
      .catch(() => toast.error("فشل تحميل القيم الحرجة"))
      .finally(() => setLoading(false));
  }, []);

  function refresh() {
    setLoading(true);
    api.get("/lab/critical-values")
      .then(r => setCriticals(r.data.critical_results || []))
      .catch(() => toast.error("فشل تحميل القيم الحرجة"))
      .finally(() => setLoading(false));
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2 style={{ color: "var(--danger)" }}>⚠ القيم الحرجة</h2>
          <p>نتائج تتجاوز الحدود الحرجة وتستوجب إشعاراً فورياً</p>
        </div>
        <button className="btn btn-outline" onClick={refresh}>تحديث</button>
      </div>

      {/* Thresholds Reference */}
      <div className="card" style={{ marginBottom: 20, background: "#fff9f0", border: "1px solid #f5c077" }}>
        <h4 style={{ marginBottom: 12, fontWeight: 600, color: "var(--warning)" }}>الحدود الحرجة المرجعية</h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 10 }}>
          {[
            { label: "الجلوكوز", value: "> 400 mg/dL" },
            { label: "الهيموجلوبين", value: "< 7 g/dL" },
            { label: "الصفائح الدموية", value: "< 50 ×10³/µL" },
            { label: "كريات الدم البيضاء", value: "> 30 ×10³/µL" },
            { label: "البوتاسيوم (K)", value: "< 2.5 أو > 6.5 mEq/L" },
            { label: "الصوديوم (Na)", value: "< 120 أو > 160 mEq/L" },
            { label: "الكرياتينين", value: "> 10 mg/dL" },
            { label: "INR", value: "> 5" },
          ].map(t => (
            <div key={t.label} style={{ background: "#fff", borderRadius: 8, padding: "8px 12px", border: "1px solid #f5c077" }}>
              <div style={{ fontWeight: 600, fontSize: ".8rem" }}>{t.label}</div>
              <div style={{ color: "var(--danger)", fontSize: ".75rem", marginTop: 2 }}>{t.value}</div>
            </div>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="card"><div className="spinner" /></div>
      ) : criticals.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div style={{ fontSize: "2rem", marginBottom: 8 }}>✅</div>
            <p>لا توجد قيم حرجة حالياً</p>
            <span>جميع النتائج المسجلة ضمن الحدود الطبيعية</span>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, border: "2px solid var(--danger)" }}>
          <div style={{ padding: "12px 16px", background: "var(--danger)", color: "#fff", fontWeight: 600, display: "flex", justifyContent: "space-between" }}>
            <span>نتائج تتطلب إجراءً فورياً</span>
            <span style={{ background: "#fff", color: "var(--danger)", borderRadius: 20, padding: "2px 10px", fontWeight: 700 }}>
              {criticals.length}
            </span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>المريض</th>
                  <th>الفحص</th>
                  <th>النتيجة</th>
                  <th>الحد الحرج</th>
                  <th>الوحدة</th>
                  <th>وقت النتيجة</th>
                  <th>الطلب</th>
                </tr>
              </thead>
              <tbody>
                {criticals.map((c: any) => (
                  <tr key={c.result_id} style={{ background: "#fff5f5" }}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{c.patient_name}</div>
                    </td>
                    <td>
                      <div>{c.test_name_ar || c.test_name}</div>
                      <div style={{ fontSize: ".75rem", color: "var(--gray-400)" }}>{c.test_code}</div>
                    </td>
                    <td>
                      <span style={{ color: "var(--danger)", fontWeight: 700, fontSize: "1.1rem" }}>
                        {c.value}
                      </span>
                    </td>
                    <td style={{ color: "var(--warning)", fontSize: ".8rem" }}>
                      {c.threshold_description || "—"}
                    </td>
                    <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>{c.unit || "—"}</td>
                    <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                      {c.created_at ? new Date(c.created_at).toLocaleString("ar-SA") : "—"}
                    </td>
                    <td style={{ fontSize: ".8rem" }}>
                      #{c.order_id?.slice(0, 8) || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding: "12px 16px", background: "#fff5f5", borderTop: "1px solid var(--gray-200)", fontSize: ".8rem", color: "var(--gray-600)" }}>
            * يجب الإبلاغ الفوري بهذه النتائج للطبيب المعالج. وثّق وقت الإبلاغ وهوية المُبلَّغ.
          </div>
        </div>
      )}
    </div>
  );
}
