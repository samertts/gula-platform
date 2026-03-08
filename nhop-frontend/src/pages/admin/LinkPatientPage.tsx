import React, { useEffect, useState } from "react";
import api from "../../api/client";
import { useToast } from "../../components/Toast";

export default function LinkPatientPage() {
  const toast = useToast();

  /* Users list */
  const [users, setUsers] = useState<any[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [selectedUser, setSelectedUser] = useState<any>(null);

  /* Patients list */
  const [patients, setPatients] = useState<any[]>([]);
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<any>(null);

  const [linking, setLinking] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingPatients, setLoadingPatients] = useState(true);

  useEffect(() => {
    api.get("/auth/users", { params: { role: "patient" } })
      .then(r => setUsers(r.data.users || []))
      .catch(() => toast.error("فشل تحميل المستخدمين"))
      .finally(() => setLoadingUsers(false));

    api.get("/patients")
      .then(r => setPatients(r.data.patients || r.data || []))
      .catch(() => toast.error("فشل تحميل المرضى"))
      .finally(() => setLoadingPatients(false));
  }, []);

  const filteredUsers = users.filter(u =>
    !userSearch ||
    u.name?.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.email?.toLowerCase().includes(userSearch.toLowerCase())
  );

  const filteredPatients = patients.filter(p =>
    !patientSearch ||
    p.name?.toLowerCase().includes(patientSearch.toLowerCase()) ||
    p.national_id?.includes(patientSearch) ||
    p.phone?.includes(patientSearch)
  );

  async function linkPatient() {
    if (!selectedUser || !selectedPatient) {
      toast.error("اختر مستخدماً ومريضاً أولاً");
      return;
    }
    setLinking(true);
    try {
      await api.post(`/patients/${selectedPatient.id}/link-user`, { user_id: selectedUser.id });
      toast.success(`تم ربط ${selectedUser.name} بسجل ${selectedPatient.name} بنجاح`);
      setSelectedUser(null);
      setSelectedPatient(null);
      /* Refresh patients to show updated link */
      const r = await api.get("/patients");
      setPatients(r.data.patients || r.data || []);
    } catch (err: any) {
      toast.error(err.response?.data?.error || "خطأ في الربط");
    } finally {
      setLinking(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>ربط حسابات المرضى</h2>
          <p>ربط حساب مستخدم بسجل مريض للوصول إلى النتائج</p>
        </div>
      </div>

      {/* Link action card */}
      {(selectedUser || selectedPatient) && (
        <div className="card" style={{ marginBottom: 20, background: "var(--primary-lt)", border: "1px solid var(--primary)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: ".8rem", color: "var(--gray-500)", marginBottom: 4 }}>المستخدم المحدد</div>
              {selectedUser
                ? <strong>{selectedUser.name} — {selectedUser.email}</strong>
                : <span style={{ color: "var(--gray-400)" }}>لم يتم اختيار مستخدم</span>}
            </div>
            <div style={{ color: "var(--primary)", fontSize: "1.5rem", fontWeight: 700 }}>⟷</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: ".8rem", color: "var(--gray-500)", marginBottom: 4 }}>سجل المريض المحدد</div>
              {selectedPatient
                ? <strong>{selectedPatient.name} — {selectedPatient.national_id || "—"}</strong>
                : <span style={{ color: "var(--gray-400)" }}>لم يتم اختيار مريض</span>}
            </div>
            <button
              className="btn btn-primary"
              onClick={linkPatient}
              disabled={linking || !selectedUser || !selectedPatient}>
              {linking ? "جاري الربط..." : "ربط الآن"}
            </button>
            <button
              className="btn btn-outline"
              onClick={() => { setSelectedUser(null); setSelectedPatient(null); }}>
              إلغاء
            </button>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Users Panel */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--gray-200)", fontWeight: 600 }}>
            حسابات المستخدمين (دور مريض)
          </div>
          <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--gray-100)" }}>
            <input
              placeholder="بحث بالاسم أو البريد..."
              value={userSearch}
              onChange={e => setUserSearch(e.target.value)}
              style={{ width: "100%", padding: "6px 10px", border: "1px solid var(--gray-200)", borderRadius: 6 }}
            />
          </div>
          {loadingUsers ? <div className="spinner" /> : (
            <div style={{ maxHeight: 420, overflow: "auto" }}>
              {filteredUsers.map(u => (
                <div
                  key={u.id}
                  onClick={() => setSelectedUser(u)}
                  style={{
                    padding: "12px 16px",
                    cursor: "pointer",
                    borderBottom: "1px solid var(--gray-100)",
                    background: selectedUser?.id === u.id ? "var(--primary-lt)" : "#fff",
                    borderRight: selectedUser?.id === u.id ? "3px solid var(--primary)" : "3px solid transparent",
                  }}>
                  <div style={{ fontWeight: 600, fontSize: ".875rem" }}>{u.name}</div>
                  <div style={{ fontSize: ".75rem", color: "var(--gray-500)", marginTop: 2 }}>
                    {u.email}
                    {u.patient_id && (
                      <span style={{ marginRight: 8, color: "var(--success)", fontWeight: 600 }}>✓ مرتبط</span>
                    )}
                  </div>
                </div>
              ))}
              {!filteredUsers.length && (
                <div className="empty-state" style={{ padding: 24 }}><p>لا يوجد مستخدمون</p></div>
              )}
            </div>
          )}
        </div>

        {/* Patients Panel */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--gray-200)", fontWeight: 600 }}>
            سجلات المرضى
          </div>
          <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--gray-100)" }}>
            <input
              placeholder="بحث بالاسم أو الهوية أو الجوال..."
              value={patientSearch}
              onChange={e => setPatientSearch(e.target.value)}
              style={{ width: "100%", padding: "6px 10px", border: "1px solid var(--gray-200)", borderRadius: 6 }}
            />
          </div>
          {loadingPatients ? <div className="spinner" /> : (
            <div style={{ maxHeight: 420, overflow: "auto" }}>
              {filteredPatients.map(p => (
                <div
                  key={p.id}
                  onClick={() => setSelectedPatient(p)}
                  style={{
                    padding: "12px 16px",
                    cursor: "pointer",
                    borderBottom: "1px solid var(--gray-100)",
                    background: selectedPatient?.id === p.id ? "var(--primary-lt)" : "#fff",
                    borderRight: selectedPatient?.id === p.id ? "3px solid var(--primary)" : "3px solid transparent",
                  }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontWeight: 600, fontSize: ".875rem" }}>{p.name}</span>
                    {p.user_id && (
                      <span style={{ fontSize: ".7rem", color: "var(--success)", fontWeight: 700 }}>✓ مرتبط</span>
                    )}
                  </div>
                  <div style={{ fontSize: ".75rem", color: "var(--gray-500)", marginTop: 2 }}>
                    {p.national_id && <span>رقم الهوية: {p.national_id} — </span>}
                    {p.phone || "—"}
                  </div>
                </div>
              ))}
              {!filteredPatients.length && (
                <div className="empty-state" style={{ padding: 24 }}><p>لا يوجد مرضى</p></div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="card" style={{ marginTop: 20, background: "var(--gray-50)" }}>
        <h4 style={{ marginBottom: 8, fontWeight: 600 }}>كيفية الربط</h4>
        <ol style={{ paddingRight: 20, lineHeight: 1.8, color: "var(--gray-600)", fontSize: ".875rem" }}>
          <li>انقر على المستخدم المراد ربطه من القائمة اليسرى (يجب أن يكون دوره "مريض")</li>
          <li>انقر على سجل المريض المقابل من القائمة اليمنى</li>
          <li>انقر على زر "ربط الآن" في شريط التأكيد</li>
          <li>بعد الربط، سيتمكن المستخدم من الوصول إلى نتائجه عبر بوابة المريض</li>
        </ol>
      </div>
    </div>
  );
}
