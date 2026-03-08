import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../../api/client";
import { useAuthStore } from "../../store/auth.store";

export default function RegisterPage() {
  const [form, setForm] = useState({ name: "", email: "", password: "", phone: "", national_id: "", role: "citizen" });
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  function change(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { data } = await api.post("/auth/register", form);
      setAuth(data.user, data.access_token);
      navigate("/portal");
    } catch (err: any) {
      const msg = err.response?.data?.error || "حدث خطأ";
      const msgs: Record<string, string> = {
        email_already_registered:            "هذا البريد الإلكتروني مسجل مسبقاً",
        self_registration_only_patient_or_citizen: "التسجيل متاح للمرضى والمواطنين فقط",
      };
      setError(msgs[msg] || msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card" style={{ maxWidth: 500 }}>
        <div className="auth-logo">
          <h1>NHOP</h1>
          <p>إنشاء حساب جديد</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={submit}>
          <div className="form-group">
            <label>الاسم الكامل *</label>
            <input name="name" value={form.name} onChange={change} placeholder="الاسم الرباعي" required />
          </div>

          <div className="form-grid-2">
            <div className="form-group">
              <label>رقم الهوية / الإقامة</label>
              <input name="national_id" value={form.national_id} onChange={change} placeholder="1xxxxxxxxx" />
            </div>
            <div className="form-group">
              <label>رقم الجوال</label>
              <input name="phone" value={form.phone} onChange={change} placeholder="05xxxxxxxx" />
            </div>
          </div>

          <div className="form-group">
            <label>البريد الإلكتروني *</label>
            <input type="email" name="email" value={form.email} onChange={change} required />
          </div>

          <div className="form-group">
            <label>كلمة المرور *</label>
            <input type="password" name="password" value={form.password} onChange={change}
              placeholder="8 أحرف على الأقل" minLength={8} required />
          </div>

          <div className="form-group">
            <label>نوع الحساب *</label>
            <select name="role" value={form.role} onChange={change}>
              <option value="citizen">مواطن</option>
              <option value="patient">مريض</option>
            </select>
          </div>

          <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center", marginTop: 8 }}
            type="submit" disabled={loading}>
            {loading ? "جاري التسجيل..." : "إنشاء الحساب"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: 20, fontSize: ".875rem", color: "var(--gray-500)" }}>
          لديك حساب؟{" "}
          <Link to="/login" style={{ color: "var(--primary)", fontWeight: 600 }}>تسجيل الدخول</Link>
        </p>
      </div>
    </div>
  );
}
