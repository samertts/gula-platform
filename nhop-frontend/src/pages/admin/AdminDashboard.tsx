import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";

export default function AdminDashboard() {
  const [stats,   setStats]   = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/lab/stats")
      .then(r => setStats(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-page"><div className="spinner" /></div>;

  const orders  = stats?.orders  || {};
  const results = stats?.results || {};

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>لوحة التحكم — مدير النظام</h2>
          <p>نظرة عامة على منصة NHOP</p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">إجمالي الطلبات</div>
          <div className="stat-value">{(Object.values(orders) as any[]).reduce((a: number, b: any) => a + Number(b), 0)}</div>
          <div className="stat-sub">آخر 7 أيام</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">طلبات مكتملة</div>
          <div className="stat-value" style={{ color: "var(--success)" }}>{orders.completed || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">قيد المعالجة</div>
          <div className="stat-value" style={{ color: "var(--warning)" }}>
            {(orders.pending || 0) + (orders.received || 0) + (orders.processing || 0)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">نتائج غير طبيعية</div>
          <div className="stat-value" style={{ color: "var(--danger)" }}>{results.abnormal || 0}</div>
          <div className="stat-sub">من {results.total || 0}</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div className="card">
          <div className="card-title">إدارة النظام</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <Link to="/admin/catalog" className="btn btn-outline">📋 إدارة قائمة الفحوصات</Link>
            <Link to="/admin/users"   className="btn btn-outline">👥 إدارة المستخدمين</Link>
            <Link to="/lab"           className="btn btn-outline">🧪 منصة المختبر</Link>
            <Link to="/doctor"        className="btn btn-outline">👨‍⚕️ بوابة الطبيب</Link>
          </div>
        </div>

        <div className="card">
          <div className="card-title">حالة الطلبات</div>
          <table>
            <tbody>
              {Object.entries(orders).map(([status, count]) => {
                const labels: Record<string, string> = {
                  pending: "انتظار", received: "مستلم", processing: "قيد التحليل",
                  completed: "مكتمل", cancelled: "ملغى"
                };
                return (
                  <tr key={status}>
                    <td><span className={`badge badge-${status}`}>{labels[status] || status}</span></td>
                    <td style={{ textAlign: "left", fontWeight: 700 }}>{String(count)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
