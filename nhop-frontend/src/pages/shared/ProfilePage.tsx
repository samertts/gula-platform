import React, { useEffect, useState } from "react";
import api from "../../api/client";
import { useAuthStore } from "../../store/auth.store";
import { useToast } from "../../components/Toast";

export default function ProfilePage() {
  const { user, setAuth } = useAuthStore();
  const toast = useToast();

  const [profile, setProfile] = useState({ name: "", email: "", phone: "" });
  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm: "" });
  const [saving, setSaving] = useState(false);
  const [changingPw, setChangingPw] = useState(false);
  const [pwError, setPwError] = useState("");

  useEffect(() => {
    if (user) setProfile({ name: user.name || "", email: user.email || "", phone: user.phone || "" });
  }, [user]);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const r = await api.patch("/auth/me", { name: profile.name, phone: profile.phone });
      setAuth(r.data.user, localStorage.getItem("token") || "");
      toast.success("تم حفظ الملف الشخصي");
    } catch (err: any) {
      toast.error(err.response?.data?.error || "خطأ في الحفظ");
    } finally {
      setSaving(false);
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setPwError("");
    if (pwForm.new_password !== pwForm.confirm) {
      setPwError("كلمة المرور الجديدة وتأكيدها غير متطابقتين");
      return;
    }
    if (pwForm.new_password.length < 8) {
      setPwError("كلمة المرور يجب أن تكون 8 أحرف على الأقل");
      return;
    }
    setChangingPw(true);
    try {
      await api.post("/auth/change-password", {
        current_password: pwForm.current_password,
        new_password: pwForm.new_password,
      });
      setPwForm({ current_password: "", new_password: "", confirm: "" });
      toast.success("تم تغيير كلمة المرور بنجاح");
    } catch (err: any) {
      setPwError(err.response?.data?.error || "خطأ في تغيير كلمة المرور");
    } finally {
      setChangingPw(false);
    }
  }

  const initials = user?.name?.split(" ").map((w: string) => w[0]).slice(0, 2).join("") || "U";
  const ROLE_AR: Record<string, string> = {
    admin: "مدير النظام", lab_staff: "فني مختبر", doctor: "طبيب", patient: "مريض", citizen: "مواطن",
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>الملف الشخصي</h2>
          <p>إدارة بياناتك الشخصية وكلمة المرور</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Profile Info */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
            <div className="user-avatar" style={{ width: 64, height: 64, fontSize: "1.5rem", borderRadius: "50%", background: "var(--primary)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, flexShrink: 0 }}>
              {initials}
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>{user?.name}</div>
              <div style={{ color: "var(--gray-500)", fontSize: ".85rem" }}>{user?.email}</div>
              <span className="badge badge-processing" style={{ marginTop: 4, display: "inline-block" }}>
                {ROLE_AR[user?.role || ""] || user?.role}
              </span>
            </div>
          </div>

          <form onSubmit={saveProfile}>
            <div className="form-group">
              <label>الاسم الكامل *</label>
              <input
                value={profile.name}
                onChange={e => setProfile(f => ({ ...f, name: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label>البريد الإلكتروني</label>
              <input value={profile.email} disabled style={{ background: "var(--gray-100)", cursor: "not-allowed" }} />
              <small style={{ color: "var(--gray-400)", fontSize: ".75rem" }}>لا يمكن تغيير البريد الإلكتروني</small>
            </div>
            <div className="form-group">
              <label>رقم الجوال</label>
              <input
                value={profile.phone}
                onChange={e => setProfile(f => ({ ...f, phone: e.target.value }))}
                placeholder="05xxxxxxxx"
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={saving} style={{ width: "100%" }}>
              {saving ? "جاري الحفظ..." : "حفظ التغييرات"}
            </button>
          </form>
        </div>

        {/* Change Password */}
        <div className="card">
          <h3 style={{ marginBottom: 20, fontSize: "1rem", fontWeight: 600 }}>تغيير كلمة المرور</h3>
          <form onSubmit={changePassword}>
            {pwError && <div className="alert alert-error" style={{ marginBottom: 16 }}>{pwError}</div>}
            <div className="form-group">
              <label>كلمة المرور الحالية *</label>
              <input
                type="password"
                value={pwForm.current_password}
                onChange={e => setPwForm(f => ({ ...f, current_password: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label>كلمة المرور الجديدة *</label>
              <input
                type="password"
                value={pwForm.new_password}
                onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))}
                minLength={8}
                required
              />
            </div>
            <div className="form-group">
              <label>تأكيد كلمة المرور الجديدة *</label>
              <input
                type="password"
                value={pwForm.confirm}
                onChange={e => setPwForm(f => ({ ...f, confirm: e.target.value }))}
                minLength={8}
                required
              />
            </div>
            <div className="alert" style={{ background: "var(--gray-50)", border: "1px solid var(--gray-200)", borderRadius: 8, padding: "10px 14px", fontSize: ".8rem", color: "var(--gray-600)", marginBottom: 16 }}>
              • الحد الأدنى 8 أحرف<br />
              • يُنصح باستخدام أحرف وأرقام ورموز
            </div>
            <button type="submit" className="btn btn-outline" disabled={changingPw} style={{ width: "100%" }}>
              {changingPw ? "جاري التغيير..." : "تغيير كلمة المرور"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
