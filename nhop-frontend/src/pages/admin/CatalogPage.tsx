import React, { useEffect, useState } from "react";
import api from "../../api/client";

export default function CatalogPage() {
  const [tests,    setTests]    = useState<any[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [catFilter, setCatFilter] = useState("");
  const [showAdd,  setShowAdd]  = useState(false);
  const [form,     setForm]     = useState({
    code: "", name_ar: "", name_en: "", category: "", sample_type: "blood",
    unit: "", normal_range_min: "", normal_range_max: "", price: "", turnaround_hours: "24"
  });
  const [adding,   setAdding]   = useState(false);
  const [error,    setError]    = useState("");

  function load() {
    setLoading(true);
    const params: any = {};
    if (catFilter) params.category = catFilter;
    api.get("/lab/catalog", { params })
      .then(r => setTests(r.data.tests || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [catFilter]);

  function change(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  }

  async function addTest(e: React.FormEvent) {
    e.preventDefault();
    setAdding(true);
    setError("");
    try {
      await api.post("/lab/catalog", {
        ...form,
        normal_range_min: form.normal_range_min ? Number(form.normal_range_min) : null,
        normal_range_max: form.normal_range_max ? Number(form.normal_range_max) : null,
        price:            Number(form.price) || 0,
        turnaround_hours: Number(form.turnaround_hours) || 24,
      });
      setShowAdd(false);
      setForm({ code: "", name_ar: "", name_en: "", category: "", sample_type: "blood", unit: "", normal_range_min: "", normal_range_max: "", price: "", turnaround_hours: "24" });
      load();
    } catch (err: any) {
      setError(err.response?.data?.error || "خطأ في الإضافة");
    } finally {
      setAdding(false);
    }
  }

  const categories = [...new Set(tests.map(t => t.category))].sort();

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>قائمة الفحوصات</h2>
          <p>{tests.length} فحص مسجل</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ إضافة فحص</button>
      </div>

      <div className="filter-bar">
        <select value={catFilter} onChange={e => setCatFilter(e.target.value)}>
          <option value="">جميع التصنيفات</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="card">
        {loading ? <div className="spinner" /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>الكود</th>
                  <th>الاسم (عربي)</th>
                  <th>الاسم (إنجليزي)</th>
                  <th>التصنيف</th>
                  <th>نوع العينة</th>
                  <th>المرجع الطبيعي</th>
                  <th>الوحدة</th>
                  <th>وقت الإنجاز</th>
                </tr>
              </thead>
              <tbody>
                {tests.map(t => (
                  <tr key={t.id}>
                    <td style={{ fontFamily: "monospace", fontWeight: 700 }}>{t.code}</td>
                    <td>{t.name_ar}</td>
                    <td style={{ color: "var(--gray-500)" }}>{t.name_en}</td>
                    <td><span className="badge badge-processing" style={{ fontSize: ".7rem" }}>{t.category}</span></td>
                    <td>{t.sample_type}</td>
                    <td style={{ fontSize: ".8rem" }}>
                      {t.normal_range_min != null && t.normal_range_max != null
                        ? `${t.normal_range_min} – ${t.normal_range_max}`
                        : t.normal_range_text || "—"}
                    </td>
                    <td>{t.unit || "—"}</td>
                    <td>{t.turnaround_hours}h</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Test Modal */}
      {showAdd && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>إضافة فحص جديد</h3>
              <button className="modal-close" onClick={() => setShowAdd(false)}>×</button>
            </div>
            <form onSubmit={addTest}>
              <div className="modal-body">
                {error && <div className="alert alert-error">{error}</div>}
                <div className="form-grid-2">
                  <div className="form-group">
                    <label>الكود *</label>
                    <input name="code" value={form.code} onChange={change} placeholder="CBC" required />
                  </div>
                  <div className="form-group">
                    <label>التصنيف *</label>
                    <input name="category" value={form.category} onChange={change} placeholder="hematology" required />
                  </div>
                </div>
                <div className="form-grid-2">
                  <div className="form-group">
                    <label>الاسم بالعربية *</label>
                    <input name="name_ar" value={form.name_ar} onChange={change} required />
                  </div>
                  <div className="form-group">
                    <label>الاسم بالإنجليزية *</label>
                    <input name="name_en" value={form.name_en} onChange={change} required />
                  </div>
                </div>
                <div className="form-grid-3">
                  <div className="form-group">
                    <label>نوع العينة</label>
                    <select name="sample_type" value={form.sample_type} onChange={change}>
                      <option value="blood">دم</option>
                      <option value="urine">بول</option>
                      <option value="nasal">مسحة أنف</option>
                      <option value="varies">متنوع</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>الوحدة</label>
                    <input name="unit" value={form.unit} onChange={change} placeholder="g/dL" />
                  </div>
                  <div className="form-group">
                    <label>وقت الإنجاز (ساعة)</label>
                    <input name="turnaround_hours" type="number" value={form.turnaround_hours} onChange={change} />
                  </div>
                </div>
                <div className="form-grid-2">
                  <div className="form-group">
                    <label>الحد الأدنى الطبيعي</label>
                    <input name="normal_range_min" type="number" step="any" value={form.normal_range_min} onChange={change} />
                  </div>
                  <div className="form-group">
                    <label>الحد الأقصى الطبيعي</label>
                    <input name="normal_range_max" type="number" step="any" value={form.normal_range_max} onChange={change} />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowAdd(false)}>إلغاء</button>
                <button type="submit" className="btn btn-primary" disabled={adding}>
                  {adding ? "جاري الحفظ..." : "إضافة"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
