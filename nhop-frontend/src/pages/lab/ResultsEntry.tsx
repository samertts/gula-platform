import React, { useEffect, useState } from "react";
import api from "../../api/client";

export default function ResultsEntry() {
  const [samples,   setSamples]   = useState<any[]>([]);
  const [selected,  setSelected]  = useState<any>(null);
  const [tests,     setTests]     = useState<any[]>([]);
  const [entries,   setEntries]   = useState<Record<string, string>>({});
  const [loading,   setLoading]   = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message,   setMessage]   = useState("");

  /* load received samples */
  useEffect(() => {
    api.get("/lab/samples", { params: { status: "received" } })
      .then(r => setSamples(r.data.samples || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function selectSample(sample: any) {
    setSelected(sample);
    setEntries({});
    setMessage("");
    /* get order items for this sample */
    const r = await api.get(`/lab/orders/${sample.order_id}`);
    const items = r.data.items || [];
    setTests(items);
    /* init empty entries */
    const init: Record<string, string> = {};
    items.forEach((i: any) => { init[i.test_catalog_id] = ""; });
    setEntries(init);
  }

  async function submit() {
    if (!selected) return;
    const results = Object.entries(entries)
      .filter(([, v]) => v.trim() !== "")
      .map(([test_catalog_id, value]) => ({ test_catalog_id, value }));

    if (!results.length) {
      setMessage("أدخل قيمة واحدة على الأقل");
      return;
    }

    setSubmitting(true);
    setMessage("");
    try {
      await api.post("/lab/results", { sample_id: selected.id, results });
      setMessage("✅ تم حفظ النتائج بنجاح");
      setSelected(null);
      setTests([]);
      setEntries({});
      /* refresh samples */
      const r = await api.get("/lab/samples", { params: { status: "received" } });
      setSamples(r.data.samples || []);
    } catch (err: any) {
      setMessage("❌ " + (err.response?.data?.error || "خطأ في الحفظ"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>إدخال النتائج</h2>
          <p>أدخل نتائج الفحوصات للعينات المستلمة</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 16 }}>
        {/* Sample list */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--gray-200)", fontWeight: 600, fontSize: ".9rem" }}>
            العينات المستلمة ({samples.length})
          </div>
          {loading ? <div className="spinner" /> : (
            <div style={{ overflow: "auto", maxHeight: 500 }}>
              {samples.map(s => (
                <div key={s.id}
                  onClick={() => selectSample(s)}
                  style={{
                    padding: "12px 16px",
                    cursor: "pointer",
                    borderBottom: "1px solid var(--gray-100)",
                    background: selected?.id === s.id ? "var(--primary-lt)" : "#fff",
                    borderRight: selected?.id === s.id ? "3px solid var(--primary)" : "3px solid transparent",
                  }}>
                  <div style={{ fontWeight: 600, fontFamily: "monospace", fontSize: ".85rem" }}>{s.barcode}</div>
                  <div style={{ fontSize: ".8rem", color: "var(--gray-600)", marginTop: 2 }}>{s.patient_name}</div>
                  <div style={{ fontSize: ".75rem", color: "var(--gray-400)" }}>{s.sample_type}</div>
                </div>
              ))}
              {!samples.length && (
                <div className="empty-state" style={{ padding: 24 }}>
                  <p>لا توجد عينات مستلمة</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Results form */}
        <div className="card">
          {!selected ? (
            <div className="empty-state">
              <p>اختر عينة للبدء</p>
              <span>اختر عينة من القائمة على اليمين لإدخال النتائج</span>
            </div>
          ) : (
            <>
              <div style={{ marginBottom: 20, padding: "12px 16px", background: "var(--gray-50)", borderRadius: "var(--radius)" }}>
                <strong>العينة:</strong> {selected.barcode} &nbsp;|&nbsp;
                <strong>المريض:</strong> {selected.patient_name} &nbsp;|&nbsp;
                <strong>النوع:</strong> {selected.sample_type}
              </div>

              {message && (
                <div className={`alert ${message.startsWith("✅") ? "alert-success" : "alert-error"}`}>{message}</div>
              )}

              <div style={{ maxHeight: 400, overflow: "auto" }}>
                <table>
                  <thead>
                    <tr>
                      <th>الفحص</th>
                      <th>الكود</th>
                      <th>المرجع</th>
                      <th>القيمة</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tests.map(t => (
                      <tr key={t.test_catalog_id || t.id}>
                        <td>{t.name_ar}</td>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{t.code}</td>
                        <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                          {t.normal_range_min != null && t.normal_range_max != null
                            ? `${t.normal_range_min} – ${t.normal_range_max}`
                            : t.normal_range_text || "—"}
                        </td>
                        <td>
                          <input
                            style={{ width: 120, margin: 0 }}
                            placeholder="أدخل القيمة"
                            value={entries[t.test_catalog_id] || ""}
                            onChange={e => setEntries(v => ({ ...v, [t.test_catalog_id]: e.target.value }))}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: 20, display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button className="btn btn-outline" onClick={() => setSelected(null)}>إلغاء</button>
                <button className="btn btn-primary" onClick={submit} disabled={submitting}>
                  {submitting ? "جاري الحفظ..." : "حفظ النتائج"}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
