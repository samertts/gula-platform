import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api from "../../api/client";

export default function NewOrderPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [patients,  setPatients]  = useState<any[]>([]);
  const [catalog,   setCatalog]   = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [catFilter, setCatFilter] = useState("");

  const [patientId, setPatientId]   = useState(searchParams.get("patient") || "");
  const [patSearch, setPatSearch]   = useState("");
  const [selectedTests, setSelectedTests] = useState<Set<string>>(new Set());
  const [priority,  setPriority]    = useState("normal");
  const [notes,     setNotes]       = useState("");

  const [loading,   setLoading]   = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error,     setError]     = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get("/lab/catalog"),
      api.get("/lab/catalog/categories"),
    ]).then(([c, cats]) => {
      setCatalog(c.data.tests || []);
      setCategories(cats.data.categories || []);
    }).finally(() => setLoading(false));
  }, []);

  function searchPatients(q: string) {
    setPatSearch(q);
    if (q.length < 2) { setPatients([]); return; }
    api.get("/doctor/patients", { params: { q } })
      .then(r => setPatients(r.data.patients || []));
  }

  function toggleTest(id: string) {
    setSelectedTests(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const filtered = catFilter ? catalog.filter(t => t.category === catFilter) : catalog;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!patientId) { setError("اختر مريضاً"); return; }
    if (!selectedTests.size) { setError("اختر فحصاً واحداً على الأقل"); return; }

    setSubmitting(true);
    setError("");
    try {
      const r = await api.post("/lab/orders", {
        patient_id:     patientId,
        test_ids:       Array.from(selectedTests),
        clinical_notes: notes || null,
        priority
      });
      navigate(`/doctor`);
    } catch (err: any) {
      setError(err.response?.data?.error || "خطأ في إنشاء الطلب");
    } finally {
      setSubmitting(false);
    }
  }

  const selectedPatient = patients.find(p => p.id === patientId);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>طلب فحص جديد</h2>
          <p>أنشئ طلب فحوصات مختبرية للمريض</p>
        </div>
      </div>

      <form onSubmit={submit}>
        <div style={{ display: "grid", gridTemplateColumns: "380px 1fr", gap: 16 }}>
          {/* Left: Patient + Settings */}
          <div>
            <div className="card">
              <div className="card-title">اختر المريض</div>
              {error && <div className="alert alert-error">{error}</div>}

              {/* Patient search */}
              <div className="form-group">
                <label>بحث عن مريض</label>
                <input
                  value={patSearch}
                  onChange={e => searchPatients(e.target.value)}
                  placeholder="اسم المريض أو الرقم الوطني"
                />
              </div>

              {patSearch && patients.length > 0 && (
                <div style={{ border: "1px solid var(--gray-200)", borderRadius: "var(--radius)", maxHeight: 180, overflow: "auto", marginBottom: 12 }}>
                  {patients.map(p => (
                    <div key={p.id}
                      onClick={() => { setPatientId(p.id); setPatSearch(p.name); setPatients([]); }}
                      style={{
                        padding: "10px 14px", cursor: "pointer",
                        background: patientId === p.id ? "var(--primary-lt)" : "#fff",
                        borderBottom: "1px solid var(--gray-100)"
                      }}>
                      <strong>{p.name}</strong>
                      <span style={{ color: "var(--gray-500)", fontSize: ".8rem", display: "block" }}>{p.national_id || p.phone}</span>
                    </div>
                  ))}
                </div>
              )}

              {patientId && selectedPatient && (
                <div className="alert alert-info" style={{ marginBottom: 12 }}>
                  ✓ {selectedPatient.name}
                </div>
              )}
              {patientId && !selectedPatient && searchParams.get("patient") && (
                <div className="alert alert-info" style={{ marginBottom: 12 }}>المريض محدد</div>
              )}

              <div className="form-group">
                <label>الأولوية</label>
                <select value={priority} onChange={e => setPriority(e.target.value)}>
                  <option value="normal">عادي</option>
                  <option value="urgent">عاجل</option>
                  <option value="stat">فوري (STAT)</option>
                </select>
              </div>

              <div className="form-group">
                <label>ملاحظات سريرية</label>
                <textarea value={notes} onChange={e => setNotes(e.target.value)}
                  rows={3} placeholder="أعراض، تشخيص مبدئي...">
                </textarea>
              </div>
            </div>

            {selectedTests.size > 0 && (
              <div className="card" style={{ marginTop: 12 }}>
                <div className="card-title">الفحوصات المختارة ({selectedTests.size})</div>
                {catalog.filter(t => selectedTests.has(t.id)).map(t => (
                  <div key={t.id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--gray-100)" }}>
                    <span style={{ fontSize: ".875rem" }}>{t.name_ar}</span>
                    <button type="button" onClick={() => toggleTest(t.id)}
                      style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer" }}>×</button>
                  </div>
                ))}
                <button type="submit" className="btn btn-primary"
                  style={{ width: "100%", marginTop: 16, justifyContent: "center" }} disabled={submitting}>
                  {submitting ? "جاري الإرسال..." : "إرسال الطلب"}
                </button>
              </div>
            )}
          </div>

          {/* Right: Test Catalog */}
          <div className="card">
            <div className="card-title">قائمة الفحوصات</div>

            <div className="filter-bar" style={{ marginBottom: 12 }}>
              <select value={catFilter} onChange={e => setCatFilter(e.target.value)}>
                <option value="">جميع التصنيفات</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {loading ? <div className="spinner" /> : (
              <div className="table-wrap" style={{ maxHeight: 500, overflow: "auto" }}>
                <table>
                  <thead>
                    <tr>
                      <th>✓</th>
                      <th>الاسم</th>
                      <th>الكود</th>
                      <th>التصنيف</th>
                      <th>المرجع الطبيعي</th>
                      <th>وقت الانجاز</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map(t => (
                      <tr key={t.id} onClick={() => toggleTest(t.id)}
                        style={{ cursor: "pointer", background: selectedTests.has(t.id) ? "var(--primary-lt)" : "" }}>
                        <td>
                          <input type="checkbox" checked={selectedTests.has(t.id)} onChange={() => toggleTest(t.id)} />
                        </td>
                        <td style={{ fontWeight: selectedTests.has(t.id) ? 600 : "normal" }}>{t.name_ar}</td>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{t.code}</td>
                        <td><span className="badge badge-processing" style={{ fontSize: ".7rem" }}>{t.category}</span></td>
                        <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                          {t.normal_range_min != null && t.normal_range_max != null
                            ? `${t.normal_range_min}–${t.normal_range_max} ${t.unit || ""}`
                            : t.normal_range_text || "—"}
                        </td>
                        <td style={{ fontSize: ".8rem" }}>{t.turnaround_hours}h</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
