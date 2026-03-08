import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";

export default function PatientsPage() {
  const [patients,  setPatients]  = useState<any[]>([]);
  const [q,         setQ]         = useState("");
  const [loading,   setLoading]   = useState(true);
  const [showAdd,   setShowAdd]   = useState(false);
  const [form,      setForm]      = useState({ name: "", national_id: "", birth_date: "", gender: "", phone: "" });
  const [adding,    setAdding]    = useState(false);
  const [error,     setError]     = useState("");

  function load(query = "") {
    setLoading(true);
    api.get("/doctor/patients", { params: query ? { q: query } : {} })
      .then(r => setPatients(r.data.patients || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  function change(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  }

  async function addPatient(e: React.FormEvent) {
    e.preventDefault();
    setAdding(true);
    setError("");
    try {
      await api.post("/doctor/patients", form);
      setShowAdd(false);
      setForm({ name: "", national_id: "", birth_date: "", gender: "", phone: "" });
      load();
    } catch (err: any) {
      setError(err.response?.data?.error || "خطأ في إضافة المريض");
    } finally {
      setAdding(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>المرضى</h2>
          <p>قائمة المرضى المسجلين</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ إضافة مريض</button>
      </div>

      <div className="filter-bar">
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="بحث بالاسم أو الرقم الوطني أو الجوال"
          onKeyDown={e => e.key === "Enter" && load(q)}
          style={{ maxWidth: 320 }}
        />
        <button className="btn btn-outline btn-sm" onClick={() => load(q)}>بحث</button>
        {q && <button className="btn btn-outline btn-sm" onClick={() => { setQ(""); load(); }}>مسح</button>}
      </div>

      <div className="card">
        {loading ? (
          <div className="loading-page"><div className="spinner" /></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>الاسم</th>
                  <th>الرقم الوطني</th>
                  <th>الجوال</th>
                  <th>الجنس</th>
                  <th>تاريخ الميلاد</th>
                  <th>الطلبات</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {patients.map(p => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 600 }}>{p.name}</td>
                    <td>{p.national_id || "—"}</td>
                    <td>{p.phone || "—"}</td>
                    <td>{p.gender === "male" ? "ذكر" : p.gender === "female" ? "أنثى" : "—"}</td>
                    <td style={{ fontSize: ".8rem" }}>
                      {p.birth_date ? new Date(p.birth_date).toLocaleDateString("ar-SA") : "—"}
                    </td>
                    <td>{p.total_orders || 0}</td>
                    <td>
                      <div style={{ display: "flex", gap: 6 }}>
                        <Link to={`/doctor/patients/${p.id}`} className="btn btn-outline btn-sm">ملف المريض</Link>
                        <Link to={`/doctor/orders/new?patient=${p.id}`} className="btn btn-primary btn-sm">طلب فحص</Link>
                      </div>
                    </td>
                  </tr>
                ))}
                {!patients.length && (
                  <tr><td colSpan={7}>
                    <div className="empty-state"><p>لا توجد مرضى</p></div>
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Patient Modal */}
      {showAdd && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>إضافة مريض جديد</h3>
              <button className="modal-close" onClick={() => setShowAdd(false)}>×</button>
            </div>
            <form onSubmit={addPatient}>
              <div className="modal-body">
                {error && <div className="alert alert-error">{error}</div>}
                <div className="form-group">
                  <label>الاسم الكامل *</label>
                  <input name="name" value={form.name} onChange={change} required />
                </div>
                <div className="form-grid-2">
                  <div className="form-group">
                    <label>الرقم الوطني</label>
                    <input name="national_id" value={form.national_id} onChange={change} />
                  </div>
                  <div className="form-group">
                    <label>رقم الجوال</label>
                    <input name="phone" value={form.phone} onChange={change} />
                  </div>
                </div>
                <div className="form-grid-2">
                  <div className="form-group">
                    <label>الجنس</label>
                    <select name="gender" value={form.gender} onChange={change}>
                      <option value="">اختر</option>
                      <option value="male">ذكر</option>
                      <option value="female">أنثى</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>تاريخ الميلاد</label>
                    <input type="date" name="birth_date" value={form.birth_date} onChange={change} />
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
