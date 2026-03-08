import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../../api/client";

export default function TrackOrderPage() {
  const { id }    = useParams<{ id: string }>();
  const [data,    setData]    = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api.get(`/portal/orders/${id}/status`)
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading-page"><div className="spinner" /></div>;
  if (!data)   return <div className="alert alert-error">الطلب غير موجود</div>;

  const progress = data.timeline?.filter((s: any) => s.done).length;
  const total    = data.timeline?.length || 1;
  const pct      = Math.round((progress / total) * 100);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>تتبع الطلب #{id?.slice(0, 8)}</h2>
          <p>الحالة الحالية لطلبك</p>
        </div>
        <Link to="/portal/orders" className="btn btn-outline">العودة</Link>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 16 }}>
        {/* Timeline */}
        <div className="card">
          <div className="card-title">مسار الطلب</div>

          {/* Progress bar */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: ".875rem", color: "var(--gray-600)" }}>التقدم</span>
              <span style={{ fontSize: ".875rem", fontWeight: 600 }}>{pct}%</span>
            </div>
            <div style={{ height: 10, background: "var(--gray-200)", borderRadius: 10 }}>
              <div style={{ width: `${pct}%`, height: "100%", background: data.is_ready ? "var(--success)" : "var(--primary)", borderRadius: 10, transition: "width .3s" }} />
            </div>
          </div>

          <ul className="timeline">
            {data.timeline?.map((step: any) => (
              <li key={step.step} className={`timeline-item ${step.done ? "done" : ""}`}>
                <div className="timeline-dot" />
                <div className="step-label">{step.label}</div>
                {step.time && (
                  <div className="step-time">{new Date(step.time).toLocaleString("ar-SA")}</div>
                )}
              </li>
            ))}
          </ul>

          {data.is_ready && (
            <div className="alert alert-success" style={{ marginTop: 20 }}>
              🎉 نتائجك جاهزة! <Link to={`/portal/reports/${id}`} style={{ fontWeight: 700 }}>اضغط هنا لعرضها</Link>
            </div>
          )}
        </div>

        {/* Details */}
        <div>
          <div className="card">
            <div className="card-title">تفاصيل الطلب</div>
            <table>
              <tbody>
                <tr>
                  <td style={{ color: "var(--gray-500)" }}>الأولوية</td>
                  <td>{data.order?.priority === "urgent" ? "عاجل" : data.order?.priority === "stat" ? "فوري" : "عادي"}</td>
                </tr>
                <tr>
                  <td style={{ color: "var(--gray-500)" }}>التاريخ</td>
                  <td style={{ fontSize: ".8rem" }}>{new Date(data.order?.created_at).toLocaleDateString("ar-SA")}</td>
                </tr>
              </tbody>
            </table>

            <div style={{ marginTop: 16 }}>
              <strong style={{ fontSize: ".875rem" }}>الفحوصات المطلوبة:</strong>
              <div style={{ marginTop: 8 }}>
                {data.tests?.map((t: any, i: number) => (
                  <div key={i} style={{ padding: "5px 0", borderBottom: "1px solid var(--gray-100)", fontSize: ".875rem" }}>
                    {t.name_ar}
                    <span className={`badge badge-${t.status}`} style={{ marginRight: 8, fontSize: ".7rem" }}>{t.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card" style={{ marginTop: 12 }}>
            <div className="card-title">العينات</div>
            {data.samples?.map((s: any) => (
              <div key={s.id} style={{ padding: "8px 0", borderBottom: "1px solid var(--gray-100)" }}>
                <div style={{ fontFamily: "monospace", fontSize: ".85rem", fontWeight: 600 }}>{s.barcode}</div>
                <div style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>{s.sample_type}</div>
                <span className={`badge badge-${s.status}`} style={{ marginTop: 4 }}>{s.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
