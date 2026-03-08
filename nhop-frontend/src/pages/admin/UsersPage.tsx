import React, { useEffect, useState } from "react";
import api from "../../api/client";

const ROLE_LABELS: Record<string, string> = {
  admin:     "مدير",
  lab_staff: "فني مختبر",
  doctor:    "طبيب",
  patient:   "مريض",
  citizen:   "مواطن",
};

export default function UsersPage() {
  const [users,   setUsers]   = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [role,    setRole]    = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form,    setForm]    = useState({ name: "", email: "", password: "", role: "lab_staff", phone: "" });
  const [adding,  setAdding]  = useState(false);
  const [error,   setError]   = useState("");

  function load() {
    setLoading(true);
    const params: any = {};
    if (role) params.role = role;
    api.get("/auth/users", { params })
      .then(r => setUsers(r.data.users || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [role]);

  function change(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  }

  async function addUser(e: React.FormEvent) {
    e.preventDefault();
    setAdding(true);
    setError("");
    try {
      await api.post("/auth/users", form);
      setShowAdd(false);
      setForm({ name: "", email: "", password: "", role: "lab_staff", phone: "" });
      load();
    } catch (err: any) {
      setError(err.response?.data?.error || "خطأ في إضافة المستخدم");
    } finally {
      setAdding(false);
    }
  }

  async function toggleStatus(userId: string, isActive: boolean) {
    try {
      await api.patch(`/auth/users/${userId}/status`, { is_active: isActive });
      load();
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>إدارة المستخدمين</h2>
          <p>كافة مستخدمي المنصة</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ إضافة مستخدم</button>
      </div>

      <div className="filter-bar">
        <select value={role} onChange={e => setRole(e.target.value)}>
          <option value="">جميع الأدوار</option>
          <option value="admin">مدير</option>
          <option value="lab_staff">فني مختبر</option>
          <option value="doctor">طبيب</option>
          <option value="patient">مريض</option>
          <option value="citizen">مواطن</option>
        </select>
      </div>

      <div className="card">
        {loading ? <div className="spinner" /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>الاسم</th>
                  <th>البريد الإلكتروني</th>
                  <th>الدور</th>
                  <th>الجوال</th>
                  <th>الحالة</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td style={{ fontWeight: 600 }}>{u.name}</td>
                    <td style={{ fontSize: ".85rem", color: "var(--gray-600)" }}>{u.email}</td>
                    <td>
                      <span className="badge badge-processing">{ROLE_LABELS[u.role] || u.role}</span>
                    </td>
                    <td>{u.phone || "—"}</td>
                    <td>
                      <span className={`badge ${u.is_active ? "badge-completed" : "badge-cancelled"}`}>
                        {u.is_active ? "نشط" : "معطل"}
                      </span>
                    </td>
                    <td>
                      <button
                        className={`btn btn-sm ${u.is_active ? "btn-danger" : "btn-success"}`}
                        onClick={() => toggleStatus(u.id, !u.is_active)}>
                        {u.is_active ? "تعطيل" : "تفعيل"}
                      </button>
                    </td>
                  </tr>
                ))}
                {!users.length && (
                  <tr><td colSpan={6}>
                    <div className="empty-state"><p>لا يوجد مستخدمون</p></div>
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add User Modal */}
      {showAdd && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>إضافة مستخدم جديد</h3>
              <button className="modal-close" onClick={() => setShowAdd(false)}>×</button>
            </div>
            <form onSubmit={addUser}>
              <div className="modal-body">
                {error && <div className="alert alert-error">{error}</div>}
                <div className="form-group">
                  <label>الاسم الكامل *</label>
                  <input name="name" value={form.name} onChange={change} required />
                </div>
                <div className="form-grid-2">
                  <div className="form-group">
                    <label>البريد الإلكتروني *</label>
                    <input type="email" name="email" value={form.email} onChange={change} required />
                  </div>
                  <div className="form-group">
                    <label>كلمة المرور *</label>
                    <input type="password" name="password" value={form.password} onChange={change} minLength={8} required />
                  </div>
                </div>
                <div className="form-grid-2">
                  <div className="form-group">
                    <label>الدور *</label>
                    <select name="role" value={form.role} onChange={change}>
                      <option value="lab_staff">فني مختبر</option>
                      <option value="doctor">طبيب</option>
                      <option value="admin">مدير</option>
                      <option value="patient">مريض</option>
                      <option value="citizen">مواطن</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>الجوال</label>
                    <input name="phone" value={form.phone} onChange={change} />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowAdd(false)}>إلغاء</button>
                <button type="submit" className="btn btn-primary" disabled={adding}>
                  {adding ? "جاري الإضافة..." : "إضافة"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
