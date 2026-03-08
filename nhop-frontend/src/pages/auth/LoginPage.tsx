import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../../api/client";
import { useAuthStore } from "../../store/auth.store";

export default function LoginPage() {
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { data } = await api.post("/auth/login", { email, password });
      setAuth(data.user, data.access_token);

      const role = data.user.role;
      if (role === "admin")     navigate("/admin");
      else if (role === "lab_staff") navigate("/lab");
      else if (role === "doctor")    navigate("/doctor");
      else navigate("/portal");

    } catch (err: any) {
      const msg = err.response?.data?.error || "حدث خطأ، حاول مرة أخرى";
      const msgs: Record<string, string> = {
        invalid_credentials: "البريد الإلكتروني أو كلمة المرور غير صحيحة",
        account_disabled:    "الحساب معطل، تواصل مع الإدارة",
      };
      setError(msgs[msg] || msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>NHOP</h1>
          <p>منصة المختبرات الصحية الوطنية</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={submit}>
          <div className="form-group">
            <label>البريد الإلكتروني</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="example@nhop.sa"
              required
            />
          </div>

          <div className="form-group">
            <label>كلمة المرور</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center", marginTop: 8 }}
            type="submit" disabled={loading}>
            {loading ? "جاري تسجيل الدخول..." : "تسجيل الدخول"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: 20, fontSize: ".875rem", color: "var(--gray-500)" }}>
          مواطن جديد؟{" "}
          <Link to="/register" style={{ color: "var(--primary)", fontWeight: 600 }}>سجّل حساباً</Link>
        </p>
      </div>
    </div>
  );
}
