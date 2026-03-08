import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";

export default function MyOrdersPage() {
  const [orders,  setOrders]  = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/portal/orders")
      .then(r => setOrders(r.data.orders || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const STATUS_LABELS: Record<string, string> = {
    pending:    "انتظار",
    received:   "تم استلام العينة",
    processing: "قيد التحليل",
    completed:  "النتائج جاهزة",
    cancelled:  "ملغى",
  };

  if (loading) return <div className="loading-page"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>طلباتي</h2>
          <p>جميع طلبات الفحوصات الخاصة بك</p>
        </div>
      </div>

      <div className="card">
        {orders.length === 0 ? (
          <div className="empty-state">
            <p>لا توجد طلبات بعد</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>رقم الطلب</th>
                  <th>عدد الفحوصات</th>
                  <th>الحالة</th>
                  <th>التاريخ</th>
                  <th>إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(o => (
                  <tr key={o.id}>
                    <td style={{ fontFamily: "monospace", fontSize: ".85rem" }}>#{o.id?.slice(0, 8)}</td>
                    <td>{o.test_count || 0} فحص</td>
                    <td>
                      <span className={`badge badge-${o.status}`}>
                        {STATUS_LABELS[o.status] || o.status}
                      </span>
                    </td>
                    <td style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                      {new Date(o.created_at).toLocaleDateString("ar-SA")}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 6 }}>
                        <Link to={`/portal/orders/${o.id}/track`} className="btn btn-outline btn-sm">تتبع</Link>
                        {o.status === "completed" && (
                          <Link to={`/portal/reports/${o.id}`} className="btn btn-primary btn-sm">النتائج</Link>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
