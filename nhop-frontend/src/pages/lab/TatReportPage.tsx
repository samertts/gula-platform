import React, { useEffect, useState } from "react";
import api from "../../api/client";

interface TatRow {
  category: string;
  total: string;
  avg_hours: string;
  max_hours: string;
  breached: string;
}

export default function TatReportPage() {
  const [rows, setRows]       = useState<TatRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState("");

  useEffect(() => {
    api.get("/lab/tat-report")
      .then(r => setRows(r.data.tat || []))
      .catch(() => setError("تعذّر تحميل تقرير TAT"))
      .finally(() => setLoading(false));
  }, []);

  const totalTests    = rows.reduce((s, r) => s + Number(r.total), 0);
  const totalBreached = rows.reduce((s, r) => s + Number(r.breached), 0);
  const breachPct     = totalTests ? Math.round((totalBreached / totalTests) * 100) : 0;

  function statusColor(avg: string, max: string) {
    const a = Number(avg);
    if (a <= 2)  return "var(--success)";
    if (a <= 6)  return "var(--warning)";
    return "var(--danger)";
  }

  return (
    <div style={{ padding: "24px" }}>
      <h2 style={{ marginBottom: 4 }}>تقرير زمن الاستجابة (TAT)</h2>
      <p style={{ color: "var(--gray-500)", marginBottom: 24, fontSize: 14 }}>
        آخر 30 يوم — Turnaround Time بالساعات
      </p>

      {loading && <p style={{ color: "var(--gray-400)" }}>جارٍ التحميل...</p>}
      {error   && <p style={{ color: "var(--danger)" }}>{error}</p>}

      {!loading && !error && (
        <>
          {/* Summary cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 28 }}>
            <SummaryCard label="إجمالي الفحوصات" value={totalTests.toLocaleString()} color="var(--primary)" />
            <SummaryCard label="تجاوزت الوقت المحدد" value={totalBreached.toLocaleString()} color="var(--danger)" />
            <SummaryCard label="نسبة التجاوز" value={`${breachPct}%`} color={breachPct > 20 ? "var(--danger)" : "var(--success)"} />
          </div>

          {rows.length === 0 ? (
            <div style={{
              textAlign: "center", padding: 48,
              background: "var(--surface)", borderRadius: 12,
              color: "var(--gray-400)"
            }}>
              لا توجد بيانات في آخر 30 يوم
            </div>
          ) : (
            <div style={{ background: "var(--surface)", borderRadius: 12, overflow: "hidden", border: "1px solid var(--border)" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "var(--bg)", borderBottom: "1px solid var(--border)" }}>
                    {["الفئة", "عدد الفحوصات", "متوسط الوقت (ساعة)", "أقصى وقت (ساعة)", "تجاوزات", "حالة"].map(h => (
                      <th key={h} style={{ padding: "12px 16px", textAlign: "right", fontSize: 13, fontWeight: 600, color: "var(--gray-500)" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => {
                    const color = statusColor(row.avg_hours, row.max_hours);
                    const breachPctRow = Number(row.total) ? Math.round((Number(row.breached) / Number(row.total)) * 100) : 0;
                    return (
                      <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                        <td style={{ padding: "12px 16px", fontWeight: 500 }}>{row.category}</td>
                        <td style={{ padding: "12px 16px" }}>{Number(row.total).toLocaleString()}</td>
                        <td style={{ padding: "12px 16px" }}>
                          <span style={{ color, fontWeight: 600 }}>{row.avg_hours}</span>
                        </td>
                        <td style={{ padding: "12px 16px", color: "var(--gray-600)" }}>{row.max_hours}</td>
                        <td style={{ padding: "12px 16px" }}>
                          <span style={{
                            background: Number(row.breached) > 0 ? "rgba(239,68,68,0.1)" : "rgba(34,197,94,0.1)",
                            color: Number(row.breached) > 0 ? "var(--danger)" : "var(--success)",
                            padding: "2px 8px", borderRadius: 6, fontSize: 13
                          }}>
                            {row.breached} ({breachPctRow}%)
                          </span>
                        </td>
                        <td style={{ padding: "12px 16px" }}>
                          <StatusBadge avg={Number(row.avg_hours)} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Bar chart */}
          {rows.length > 0 && (
            <div style={{ marginTop: 28, background: "var(--surface)", borderRadius: 12, padding: 24, border: "1px solid var(--border)" }}>
              <h3 style={{ marginBottom: 20, fontSize: 15 }}>متوسط زمن الاستجابة بالفئة</h3>
              {rows.map((row, i) => {
                const pct = Math.min(100, (Number(row.avg_hours) / 24) * 100);
                const color = statusColor(row.avg_hours, row.max_hours);
                return (
                  <div key={i} style={{ marginBottom: 14 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: 13 }}>
                      <span>{row.category}</span>
                      <span style={{ color, fontWeight: 600 }}>{row.avg_hours} ساعة</span>
                    </div>
                    <div style={{ height: 8, background: "var(--border)", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 4, transition: "width 0.6s ease" }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{
      background: "var(--surface)", borderRadius: 12, padding: 20,
      border: "1px solid var(--border)", textAlign: "center"
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, color, marginBottom: 6 }}>{value}</div>
      <div style={{ fontSize: 13, color: "var(--gray-500)" }}>{label}</div>
    </div>
  );
}

function StatusBadge({ avg }: { avg: number }) {
  if (avg <= 2)  return <span style={{ background: "rgba(34,197,94,0.1)",  color: "var(--success)", padding: "2px 8px", borderRadius: 6, fontSize: 12 }}>ممتاز</span>;
  if (avg <= 6)  return <span style={{ background: "rgba(234,179,8,0.1)",  color: "var(--warning)", padding: "2px 8px", borderRadius: 6, fontSize: 12 }}>مقبول</span>;
  return              <span style={{ background: "rgba(239,68,68,0.1)",   color: "var(--danger)",  padding: "2px 8px", borderRadius: 6, fontSize: 12 }}>يحتاج مراجعة</span>;
}
