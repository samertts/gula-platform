import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import { useAuthStore } from "../../store/auth.store";

const STATUS_LABELS: Record<string, string> = {
  pending:    "انتظار",
  received:   "مستلم",
  processing: "قيد التحليل",
  completed:  "مكتمل",
  cancelled:  "ملغى",
};

export default function DoctorDashboard() {
  const { user } = useAuthStore();
  const [data,    setData]    = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/doctor/dashboard")
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-page"><div className="spinner" /></div>;

  const orders = data?.orders || {};

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>مرحباً، {user?.name}</h2>
          <p>لوحة تحكم الطبيب</p>
        </div>
        <Link to="/doctor/orders/new" className="btn btn-primary">+ طلب فحص جديد</Link>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">إجمالي الطلبات</div>
          <div className="stat-value">{(Object.values(orders) as any[]).reduce((a: number, b: any) => a + Number(b), 0)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">قيد التنفيذ</div>
          <div className="stat-value" style={{ color: "var(--warning)" }}>{(orders.pending || 0) + (orders.received || 0) + (orders.processing || 0)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">نتائج جاهزة</div>
          <div className="stat-value" style={{ color: "var(--success)" }}>{orders.completed || 0}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">آخر الطلبات</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>رقم الطلب</th>
                <th>المريض</th>
                <th>الرقم الوطني</th>
                <th>الحالة</th>
                <th>التاريخ</th>
                <th>إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {data?.recent_orders?.map((o: any) => (
                <tr key={o.id}>
                  <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{o.id?.slice(0, 8)}</td>
                  <td>{o.patient_name}</td>
                  <td>{o.national_id || "—"}</td>
                  <td><span className={`badge badge-${o.status}`}>{STATUS_LABELS[o.status] || o.status}</span></td>
                  <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                    {new Date(o.created_at).toLocaleDateString("ar-SA")}
                  </td>
                  <td>
                    {o.status === "completed" && (
                      <a href={`/api/lab/reports/${o.id}`} target="_blank"
                        className="btn btn-outline btn-sm" rel="noreferrer">
                        عرض النتائج
                      </a>
                    )}
                  </td>
                </tr>
              ))}
              {!data?.recent_orders?.length && (
                <tr><td colSpan={6}>
                  <div className="empty-state"><p>لا توجد طلبات بعد</p></div>
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
