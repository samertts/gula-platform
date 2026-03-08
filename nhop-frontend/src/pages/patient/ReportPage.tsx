import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../../api/client";

const CAT_LABELS: Record<string, string> = {
  hematology:   "الدم والخلايا",
  chemistry:    "الكيمياء الحيوية",
  lipids:       "الدهون",
  kidney:       "وظائف الكلى",
  liver:        "وظائف الكبد",
  endocrine:    "الغدد الصماء",
  urine:        "تحليل البول",
  inflammation: "مؤشرات الالتهاب",
  vitamins:     "الفيتامينات",
  microbiology: "الميكروبيولوجي",
};

export default function ReportPage() {
  const { id }    = useParams<{ id: string }>();
  const [report,  setReport]  = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

  useEffect(() => {
    if (!id) return;
    api.get(`/portal/report/${id}`)
      .then(r => setReport(r.data.report))
      .catch(err => setError(err.response?.data?.error || "خطأ في تحميل التقرير"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading-page"><div className="spinner" /></div>;
  if (error)   return <div className="alert alert-error">{error}</div>;
  if (!report) return null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>تقرير نتائج المختبر</h2>
          <p>رقم التقرير: {report.report_id}</p>
        </div>
        <button className="btn btn-outline" onClick={() => window.print()}>🖨️ طباعة</button>
      </div>

      {/* Patient Info Card */}
      <div className="card" style={{ marginBottom: 16, background: "var(--primary)", color: "#fff" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16 }}>
          <div>
            <div style={{ fontSize: ".75rem", opacity: .8 }}>اسم المريض</div>
            <div style={{ fontWeight: 700, fontSize: "1.05rem", marginTop: 4 }}>{report.patient?.name}</div>
          </div>
          <div>
            <div style={{ fontSize: ".75rem", opacity: .8 }}>الرقم الوطني</div>
            <div style={{ fontWeight: 600, marginTop: 4 }}>{report.patient?.national_id || "—"}</div>
          </div>
          <div>
            <div style={{ fontSize: ".75rem", opacity: .8 }}>الجنس</div>
            <div style={{ fontWeight: 600, marginTop: 4 }}>
              {report.patient?.gender === "male" ? "ذكر" : report.patient?.gender === "female" ? "أنثى" : "—"}
            </div>
          </div>
          <div>
            <div style={{ fontSize: ".75rem", opacity: .8 }}>تاريخ التقرير</div>
            <div style={{ fontWeight: 600, marginTop: 4 }}>
              {new Date(report.generated_at).toLocaleDateString("ar-SA")}
            </div>
          </div>
        </div>
      </div>

      {/* Summary */}
      {report.abnormal_count > 0 && (
        <div className="alert alert-warning" style={{ marginBottom: 16 }}>
          ⚠️ يوجد {report.abnormal_count} نتيجة غير طبيعية من أصل {report.total_tests} فحص. يُرجى مراجعة طبيبك.
        </div>
      )}

      {/* Results by Category */}
      {Object.entries(report.results_by_category || {}).map(([cat, rows]: [string, any]) => (
        <div className="card" key={cat} style={{ marginBottom: 16 }}>
          <div className="card-title">{CAT_LABELS[cat] || cat}</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>الفحص</th>
                  <th>الكود</th>
                  <th>النتيجة</th>
                  <th>المرجع الطبيعي</th>
                  <th>الحالة</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r: any, i: number) => (
                  <tr key={i} className={r.is_abnormal ? "result-row-abnormal" : "result-row-normal"}>
                    <td style={{ fontWeight: 500 }}>{r.name_ar}</td>
                    <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{r.code}</td>
                    <td>
                      <span className={r.is_abnormal ? (r.abnormal_flag === "H" ? "value-high" : "value-low") : "value-normal"}>
                        <strong>{r.value}</strong> {r.unit}
                      </span>
                    </td>
                    <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                      {r.normal_range_min != null && r.normal_range_max != null
                        ? `${r.normal_range_min} – ${r.normal_range_max} ${r.unit || ""}`
                        : r.normal_range_text || "—"}
                    </td>
                    <td>
                      {r.is_abnormal ? (
                        <span className={`badge badge-${r.abnormal_flag}`}>
                          {r.abnormal_flag === "H" ? "↑ مرتفع" : "↓ منخفض"}
                        </span>
                      ) : (
                        <span className="badge badge-normal">✓ طبيعي</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {/* Disclaimer */}
      <div className="card" style={{ background: "var(--gray-50)", borderStyle: "dashed" }}>
        <p style={{ fontSize: ".8rem", color: "var(--gray-500)", textAlign: "center" }}>
          ⚠️ {report.disclaimer}
        </p>
        <p style={{ fontSize: ".75rem", color: "var(--gray-400)", textAlign: "center", marginTop: 4 }}>
          NHOP — منصة المختبرات الصحية الوطنية
        </p>
      </div>
    </div>
  );
}
