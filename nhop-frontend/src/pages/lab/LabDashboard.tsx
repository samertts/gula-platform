import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";

const STATUS_LABELS: Record<string, string> = {
  pending:    "انتظار",
  received:   "مستلمة",
  processing: "قيد التحليل",
  completed:  "مكتملة",
  cancelled:  "ملغاة",
};

export default function LabDashboard() {
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
  const samples = stats?.samples || {};
  const results = stats?.results || {};

  const totalOrders: number = (Object.values(orders) as any[]).reduce((a: number, b: any) => a + Number(b), 0);
  const pendingOrders = orders.pending || 0;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>لوحة تحكم المختبر</h2>
          <p>إجمالي آخر 7 أيام</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <Link to="/lab/samples" className="btn btn-outline">العينات</Link>
          <Link to="/lab/results" className="btn btn-primary">إدخال نتائج</Link>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">إجمالي الطلبات</div>
          <div className="stat-value">{totalOrders}</div>
          <div className="stat-sub">آخر 7 أيام</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">طلبات قيد الانتظار</div>
          <div className="stat-value" style={{ color: "var(--warning)" }}>{pendingOrders}</div>
          <div className="stat-sub">تحتاج إجراء</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">طلبات مكتملة</div>
          <div className="stat-value" style={{ color: "var(--success)" }}>{orders.completed || 0}</div>
          <div className="stat-sub">جاهزة للاستلام</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">نتائج غير طبيعية</div>
          <div className="stat-value" style={{ color: "var(--danger)" }}>{results.abnormal || 0}</div>
          <div className="stat-sub">من {results.total || 0} نتيجة</div>
        </div>
      </div>

      {/* Order Status Breakdown */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div className="card">
          <div className="card-title">حالة الطلبات</div>
          <table>
            <tbody>
              {Object.entries(orders).map(([status, count]) => (
                <tr key={status}>
                  <td>
                    <span className={`badge badge-${status}`}>{STATUS_LABELS[status] || status}</span>
                  </td>
                  <td style={{ textAlign: "left", fontWeight: 600 }}>{String(count)}</td>
                </tr>
              ))}
              {!Object.keys(orders).length && (
                <tr><td colSpan={2} style={{ textAlign: "center", color: "var(--gray-400)", padding: 20 }}>لا توجد طلبات</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="card-title">حالة العينات</div>
          <table>
            <tbody>
              {Object.entries(samples).map(([status, count]) => (
                <tr key={status}>
                  <td>
                    <span className={`badge badge-${status}`}>{STATUS_LABELS[status] || status}</span>
                  </td>
                  <td style={{ textAlign: "left", fontWeight: 600 }}>{String(count)}</td>
                </tr>
              ))}
              {!Object.keys(samples).length && (
                <tr><td colSpan={2} style={{ textAlign: "center", color: "var(--gray-400)", padding: 20 }}>لا توجد عينات</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title">إجراءات سريعة</div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Link to="/lab/orders" className="btn btn-outline">📋 عرض الطلبات الجديدة</Link>
          <Link to="/lab/samples" className="btn btn-outline">🧪 استلام العينات</Link>
          <Link to="/lab/results" className="btn btn-primary">✅ إدخال نتائج</Link>
        </div>
      </div>
    </div>
  );
}
