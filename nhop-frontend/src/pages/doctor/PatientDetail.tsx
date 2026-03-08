import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../../api/client";

/* ---- Inline SVG Sparkline ---- */
function Sparkline({ values, color = "var(--primary)", width = 120, height = 36 }: {
  values: number[]; color?: string; width?: number; height?: number;
}) {
  if (values.length < 2) return <span style={{ fontSize: ".75rem", color: "var(--gray-400)" }}>—</span>;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pad = 3;
  const W = width - pad * 2;
  const H = height - pad * 2;
  const pts = values.map((v, i) => {
    const x = pad + (i / (values.length - 1)) * W;
    const y = pad + H - ((v - min) / range) * H;
    return `${x},${y}`;
  }).join(" ");
  const lastPt = pts.split(" ").pop()!;
  const [lx, ly] = lastPt.split(",").map(Number);
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      <polyline fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" points={pts} />
      <circle cx={lx} cy={ly} r={3} fill={color} />
    </svg>
  );
}

export default function PatientDetail() {
  const { id }    = useParams<{ id: string }>();
  const [data,    setData]    = useState<any>(null);
  const [ai,      setAi]      = useState<any>(null);
  const [trends,  setTrends]  = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.get(`/doctor/patients/${id}`)
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));

    api.get(`/doctor/patients/${id}/results`)
      .then(r => setTrends(r.data.trends || []))
      .catch(() => {}); /* trends are optional — don't block the page */
  }, [id]);

  async function runAI() {
    setAiLoading(true);
    try {
      const r = await api.post(`/doctor/analyze/${id}`);
      setAi(r.data.analysis);
    } catch (err: any) {
      console.error(err);
    } finally {
      setAiLoading(false);
    }
  }

  if (loading) return <div className="loading-page"><div className="spinner" /></div>;
  if (!data)   return <div className="alert alert-error">المريض غير موجود</div>;

  const p = data.patient;

  const RISK_COLORS: Record<string, string> = {
    low:    "var(--success)",
    medium: "var(--warning)",
    high:   "var(--danger)",
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>{p.name}</h2>
          <p>ملف المريض الكامل</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <Link to={`/doctor/orders/new?patient=${id}`} className="btn btn-primary">طلب فحص جديد</Link>
          <button className="btn btn-outline" onClick={runAI} disabled={aiLoading}>
            {aiLoading ? "جاري التحليل..." : "🤖 تحليل AI"}
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 16 }}>
        {/* Patient Info */}
        <div>
          <div className="card">
            <div className="card-title">بيانات المريض</div>
            <table>
              <tbody>
                <tr><td style={{ color: "var(--gray-500)", width: 110 }}>الاسم</td><td><strong>{p.name}</strong></td></tr>
                <tr><td style={{ color: "var(--gray-500)" }}>الرقم الوطني</td><td>{p.national_id || "—"}</td></tr>
                <tr><td style={{ color: "var(--gray-500)" }}>الجوال</td><td>{p.phone || "—"}</td></tr>
                <tr><td style={{ color: "var(--gray-500)" }}>الجنس</td><td>{p.gender === "male" ? "ذكر" : p.gender === "female" ? "أنثى" : "—"}</td></tr>
                <tr><td style={{ color: "var(--gray-500)" }}>فصيلة الدم</td><td>{p.blood_type || "—"}</td></tr>
                <tr><td style={{ color: "var(--gray-500)" }}>تاريخ الميلاد</td><td>{p.birth_date ? new Date(p.birth_date).toLocaleDateString("ar-SA") : "—"}</td></tr>
              </tbody>
            </table>
          </div>

          {/* AI Analysis */}
          {ai && (
            <div className="card" style={{ marginTop: 16 }}>
              <div className="card-title">تحليل الذكاء الاصطناعي</div>
              <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontWeight: 600 }}>مستوى الخطر:</span>
                <span style={{ color: RISK_COLORS[ai.risk_level], fontWeight: 700, fontSize: "1.1rem" }}>
                  {ai.risk_level === "low" ? "منخفض" : ai.risk_level === "medium" ? "متوسط" : "مرتفع"}
                </span>
              </div>
              <div style={{ marginBottom: 12 }}>
                <strong>نتائج غير طبيعية:</strong> {ai.abnormal_count} من {ai.total_tests}
              </div>
              {ai.flags?.length > 0 && (
                <div>
                  <strong>تنبيهات:</strong>
                  {ai.flags.map((f: any, i: number) => (
                    <div key={i} className={`alert alert-${f.severity === "high" ? "error" : "warning"}`} style={{ marginTop: 6, padding: "8px 12px" }}>
                      <strong>{f.test}:</strong> {f.message}
                    </div>
                  ))}
                </div>
              )}
              {ai.recommendations?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <strong>توصيات:</strong>
                  <ul style={{ paddingRight: 18, marginTop: 6 }}>
                    {ai.recommendations.map((r: string, i: number) => (
                      <li key={i} style={{ marginBottom: 4, fontSize: ".875rem" }}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
              <p style={{ fontSize: ".75rem", color: "var(--gray-400)", marginTop: 12 }}>{ai.disclaimer}</p>
            </div>
          )}
        </div>

        {/* Orders & Abnormals */}
        <div>
          {/* Recent Abnormals */}
          {data.abnormal_results?.length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-title" style={{ color: "var(--danger)" }}>⚠️ نتائج غير طبيعية حديثة</div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>الفحص</th>
                      <th>القيمة</th>
                      <th>المرجع</th>
                      <th>التوجه</th>
                      <th>التاريخ</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.abnormal_results.map((r: any, i: number) => (
                      <tr key={i} className="result-row-abnormal">
                        <td>{r.name_ar}</td>
                        <td className={r.abnormal_flag === "H" ? "value-high" : "value-low"}>
                          {r.value} {r.unit}
                          <span className={`badge badge-${r.abnormal_flag}`} style={{ marginRight: 6 }}>{r.abnormal_flag}</span>
                        </td>
                        <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                          {r.normal_range_min}–{r.normal_range_max}
                        </td>
                        <td>{r.abnormal_flag === "H" ? "↑ مرتفع" : "↓ منخفض"}</td>
                        <td style={{ fontSize: ".8rem" }}>{new Date(r.created_at).toLocaleDateString("ar-SA")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Trend Charts */}
          {trends.length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-title">اتجاهات النتائج عبر الزمن</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12 }}>
                {trends.map((t: any) => {
                  const vals = (t.history || []).map((h: any) => parseFloat(h.value)).filter((v: number) => !isNaN(v));
                  const last = vals[vals.length - 1];
                  const isHigh = t.last_flag === "H";
                  const isLow  = t.last_flag === "L";
                  const sparkColor = isHigh ? "var(--danger)" : isLow ? "var(--info, #3b82f6)" : "var(--success)";
                  return (
                    <div key={t.code} style={{ background: "var(--gray-50)", borderRadius: 8, padding: "10px 12px", border: `1px solid ${isHigh || isLow ? "var(--warning)" : "var(--gray-200)"}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <span style={{ fontSize: ".8rem", fontWeight: 600 }}>{t.name_ar || t.code}</span>
                        {(isHigh || isLow) && (
                          <span style={{ fontSize: ".7rem", color: sparkColor, fontWeight: 700 }}>
                            {isHigh ? "↑" : "↓"} {t.last_flag}
                          </span>
                        )}
                      </div>
                      <Sparkline values={vals} color={sparkColor} />
                      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
                        <span style={{ fontSize: ".75rem", color: "var(--gray-500)" }}>
                          آخر: <strong style={{ color: sparkColor }}>{last != null ? `${last} ${t.unit || ""}` : "—"}</strong>
                        </span>
                        <span style={{ fontSize: ".7rem", color: "var(--gray-400)" }}>
                          {(t.history || []).length} قياس
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Orders History */}
          <div className="card">
            <div className="card-title">سجل الطلبات</div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>رقم الطلب</th>
                    <th>الحالة</th>
                    <th>الأولوية</th>
                    <th>التاريخ</th>
                    <th>إجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_orders?.map((o: any) => (
                    <tr key={o.id}>
                      <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{o.id?.slice(0, 8)}</td>
                      <td><span className={`badge badge-${o.status}`}>{o.status}</span></td>
                      <td>{o.priority}</td>
                      <td style={{ fontSize: ".8rem" }}>{new Date(o.created_at).toLocaleDateString("ar-SA")}</td>
                      <td>
                        {o.status === "completed" && (
                          <a href={`/api/lab/reports/${o.id}`} target="_blank" className="btn btn-outline btn-sm" rel="noreferrer">
                            النتائج
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                  {!data.recent_orders?.length && (
                    <tr><td colSpan={5}>
                      <div className="empty-state" style={{ padding: 20 }}><p>لا توجد طلبات</p></div>
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
