import React, { useEffect, useState } from "react";
import api from "../../api/client";

export default function MyResultsPage() {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

  useEffect(() => {
    api.get("/portal/results")
      .then(r => setResults(r.data.results || []))
      .catch(err => setError(err.response?.data?.error || "خطأ في التحميل"))
      .finally(() => setLoading(false));
  }, []);

  /* group by category */
  const grouped: Record<string, any[]> = {};
  for (const r of results) {
    if (!grouped[r.category]) grouped[r.category] = [];
    grouped[r.category].push(r);
  }

  const CAT_LABELS: Record<string, string> = {
    hematology: "الدم والخلايا",
    chemistry:  "الكيمياء الحيوية",
    lipids:     "الدهون",
    kidney:     "وظائف الكلى",
    liver:      "وظائف الكبد",
    endocrine:  "الغدد الصماء",
    urine:      "تحليل البول",
    inflammation: "الالتهاب",
    vitamins:   "الفيتامينات",
    microbiology: "الميكروبيولوجي",
  };

  if (loading) return <div className="loading-page"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>نتائجي المختبرية</h2>
          <p>جميع نتائجك المصدرة</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {!error && results.length === 0 && (
        <div className="card">
          <div className="empty-state">
            <p>لا توجد نتائج بعد</p>
            <span>ستظهر نتائجك هنا بعد الانتهاء من التحليل</span>
          </div>
        </div>
      )}

      {Object.entries(grouped).map(([cat, rows]) => (
        <div className="card" key={cat} style={{ marginBottom: 16 }}>
          <div className="card-title">{CAT_LABELS[cat] || cat}</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>الفحص</th>
                  <th>النتيجة</th>
                  <th>المرجع الطبيعي</th>
                  <th>التوجه</th>
                  <th>التاريخ</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className={r.is_abnormal ? "result-row-abnormal" : "result-row-normal"}>
                    <td>{r.name_ar}</td>
                    <td>
                      <span className={r.is_abnormal ? (r.abnormal_flag === "H" ? "value-high" : "value-low") : "value-normal"}>
                        {r.value} {r.unit}
                      </span>
                      {r.is_abnormal && (
                        <span className={`badge badge-${r.abnormal_flag}`} style={{ marginRight: 6 }}>
                          {r.abnormal_flag === "H" ? "↑ مرتفع" : "↓ منخفض"}
                        </span>
                      )}
                    </td>
                    <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                      {r.normal_range_min != null && r.normal_range_max != null
                        ? `${r.normal_range_min} – ${r.normal_range_max} ${r.unit || ""}`
                        : r.normal_range_text || "—"}
                    </td>
                    <td>
                      {r.is_abnormal ? (
                        <span style={{ color: r.abnormal_flag === "H" ? "var(--danger)" : "var(--primary)" }}>
                          {r.abnormal_flag === "H" ? "فوق الطبيعي" : "تحت الطبيعي"}
                        </span>
                      ) : (
                        <span style={{ color: "var(--success)" }}>طبيعي ✓</span>
                      )}
                    </td>
                    <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                      {new Date(r.created_at).toLocaleDateString("ar-SA")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
