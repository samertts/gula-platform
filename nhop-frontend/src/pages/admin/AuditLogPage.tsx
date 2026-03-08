import React, { useEffect, useState, useCallback } from "react";
import api from "../../api/client";

interface AuditEntry {
  id: number;
  user_id: number | null;
  user_name: string | null;
  user_role: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  details: Record<string, unknown>;
  ip: string | null;
  created_at: string;
}

const ROLE_LABELS: Record<string, string> = {
  admin: "مدير", lab_staff: "فني مختبر", doctor: "طبيب", patient: "مريض", citizen: "مواطن",
};

const ACTION_LABELS: Record<string, string> = {
  login: "تسجيل دخول",
  logout: "تسجيل خروج",
  create_order: "إنشاء طلب",
  results_entered: "إدخال نتائج",
  result_approved: "اعتماد نتيجة",
  order_released: "إصدار تقرير",
  sample_collected: "جمع عينة",
  sample_received: "استلام عينة",
  sample_rejected: "رفض عينة",
  password_changed: "تغيير كلمة مرور",
};

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("ar-IQ", { dateStyle: "short", timeStyle: "short" });
}

function actionColor(action: string) {
  if (action === "login") return "var(--primary)";
  if (action.includes("approve") || action.includes("released")) return "var(--success)";
  if (action.includes("reject")) return "var(--danger)";
  if (action.includes("create") || action.includes("entered")) return "var(--warning)";
  return "var(--gray-500)";
}

export default function AuditLogPage() {
  const [logs, setLogs]       = useState<AuditEntry[]>([]);
  const [total, setTotal]     = useState(0);
  const [page, setPage]       = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState("");
  const [filterAction, setFilterAction] = useState("");

  const limit = 30;

  const load = useCallback(() => {
    setLoading(true);
    const params: Record<string, string | number> = { page, limit };
    if (filterAction) params.action = filterAction;
    api.get("/auth/audit-logs", { params })
      .then(r => { setLogs(r.data.logs || []); setTotal(r.data.total || 0); })
      .catch(() => setError("تعذّر تحميل سجل العمليات"))
      .finally(() => setLoading(false));
  }, [page, filterAction]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h2 style={{ margin: 0 }}>سجل العمليات</h2>
          <p style={{ color: "var(--gray-500)", marginTop: 4, fontSize: 14 }}>
            Audit Log — تتبع كل الأنشطة الحساسة في النظام
          </p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <input
            placeholder="فلترة حسب العملية..."
            value={filterAction}
            onChange={e => { setFilterAction(e.target.value); setPage(1); }}
            style={{
              padding: "8px 12px", border: "1px solid var(--border)", borderRadius: 8,
              background: "var(--surface)", color: "var(--text)", fontSize: 14, minWidth: 200
            }}
          />
          <button onClick={load} style={{
            padding: "8px 16px", background: "var(--primary)", color: "#fff",
            border: "none", borderRadius: 8, cursor: "pointer", fontSize: 14
          }}>
            تحديث
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 24 }}>
        <StatCard label="إجمالي العمليات" value={total.toLocaleString()} />
        <StatCard label="عدد الصفحات" value={totalPages.toLocaleString()} />
        <StatCard label="الصفحة الحالية" value={`${page} / ${totalPages || 1}`} />
      </div>

      {loading && <p style={{ color: "var(--gray-400)", textAlign: "center", padding: 32 }}>جارٍ التحميل...</p>}
      {error   && <p style={{ color: "var(--danger)", textAlign: "center" }}>{error}</p>}

      {!loading && !error && (
        <>
          {logs.length === 0 ? (
            <div style={{
              textAlign: "center", padding: 48,
              background: "var(--surface)", borderRadius: 12,
              color: "var(--gray-400)", border: "1px solid var(--border)"
            }}>
              لا توجد سجلات بعد
            </div>
          ) : (
            <div style={{ background: "var(--surface)", borderRadius: 12, overflow: "hidden", border: "1px solid var(--border)" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "var(--bg)", borderBottom: "1px solid var(--border)" }}>
                    {["الوقت", "المستخدم", "الدور", "العملية", "الكيان", "التفاصيل", "IP"].map(h => (
                      <th key={h} style={{ padding: "10px 14px", textAlign: "right", fontSize: 12, fontWeight: 600, color: "var(--gray-500)" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => (
                    <tr key={log.id} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 14px", fontSize: 12, color: "var(--gray-500)", whiteSpace: "nowrap" }}>
                        {formatDate(log.created_at)}
                      </td>
                      <td style={{ padding: "10px 14px", fontSize: 13, fontWeight: 500 }}>
                        {log.user_name || <span style={{ color: "var(--gray-400)" }}>—</span>}
                      </td>
                      <td style={{ padding: "10px 14px" }}>
                        {log.user_role ? (
                          <span style={{
                            background: "var(--bg)", padding: "2px 8px", borderRadius: 6,
                            fontSize: 11, color: "var(--gray-600)"
                          }}>
                            {ROLE_LABELS[log.user_role] || log.user_role}
                          </span>
                        ) : "—"}
                      </td>
                      <td style={{ padding: "10px 14px" }}>
                        <span style={{
                          color: actionColor(log.action),
                          fontSize: 12, fontWeight: 600,
                          background: `${actionColor(log.action)}18`,
                          padding: "2px 8px", borderRadius: 6
                        }}>
                          {ACTION_LABELS[log.action] || log.action}
                        </span>
                      </td>
                      <td style={{ padding: "10px 14px", fontSize: 12, color: "var(--gray-500)" }}>
                        {log.entity_type ? `${log.entity_type}${log.entity_id ? ` #${log.entity_id}` : ""}` : "—"}
                      </td>
                      <td style={{ padding: "10px 14px", fontSize: 11, color: "var(--gray-400)", maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {Object.keys(log.details || {}).length > 0
                          ? JSON.stringify(log.details).substring(0, 50) + (JSON.stringify(log.details).length > 50 ? "..." : "")
                          : "—"
                        }
                      </td>
                      <td style={{ padding: "10px 14px", fontSize: 11, color: "var(--gray-400)" }}>
                        {log.ip || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 20 }}>
              <button
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
                style={{
                  padding: "6px 14px", border: "1px solid var(--border)", borderRadius: 6,
                  background: page === 1 ? "var(--bg)" : "var(--surface)",
                  cursor: page === 1 ? "not-allowed" : "pointer", color: "var(--text)",
                  opacity: page === 1 ? 0.4 : 1
                }}
              >
                السابق
              </button>
              <span style={{ padding: "6px 14px", fontSize: 14, color: "var(--gray-500)" }}>
                {page} / {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                style={{
                  padding: "6px 14px", border: "1px solid var(--border)", borderRadius: 6,
                  background: page >= totalPages ? "var(--bg)" : "var(--surface)",
                  cursor: page >= totalPages ? "not-allowed" : "pointer", color: "var(--text)",
                  opacity: page >= totalPages ? 0.4 : 1
                }}
              >
                التالي
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div style={{
      background: "var(--surface)", borderRadius: 10, padding: "16px 20px",
      border: "1px solid var(--border)"
    }}>
      <div style={{ fontSize: 22, fontWeight: 700, color: "var(--primary)", marginBottom: 4 }}>{value}</div>
      <div style={{ fontSize: 12, color: "var(--gray-500)" }}>{label}</div>
    </div>
  );
}
