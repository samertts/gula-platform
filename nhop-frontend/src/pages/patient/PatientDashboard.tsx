import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import { useAuthStore } from "../../store/auth.store";

export default function PatientDashboard() {
  const { user }  = useAuthStore();
  const [orders,  setOrders]  = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

  useEffect(() => {
    api.get("/portal/orders")
      .then(r => setOrders(r.data.orders || []))
      .catch(err => {
        const e = err.response?.data?.error;
        if (e === "patient_profile_not_found") {
          setError("لم يتم ربط حسابك بملف مريض بعد. تواصل مع المختبر.");
        } else {
          setError("خطأ في تحميل البيانات");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const readyOrders = orders.filter(o => o.status === "completed");

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>مرحباً، {user?.name}</h2>
          <p>بوابة المريض — نتائجك وتحليلاتك</p>
        </div>
      </div>

      {error && <div className="alert alert-warning">{error}</div>}

      {!error && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">إجمالي الطلبات</div>
              <div className="stat-value">{orders.length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">نتائج جاهزة</div>
              <div className="stat-value" style={{ color: "var(--success)" }}>{readyOrders.length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">قيد الإجراء</div>
              <div className="stat-value" style={{ color: "var(--warning)" }}>{orders.length - readyOrders.length}</div>
            </div>
          </div>

          {/* Ready Orders */}
          {readyOrders.length > 0 && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-title" style={{ color: "var(--success)" }}>✅ نتائجك جاهزة</div>
              {readyOrders.map(o => (
                <div key={o.id} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "12px 0", borderBottom: "1px solid var(--gray-100)"
                }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>طلب #{o.id?.slice(0, 8)}</div>
                    <div style={{ fontSize: ".8rem", color: "var(--gray-500)" }}>
                      {o.test_count} فحص — {new Date(o.created_at).toLocaleDateString("ar-SA")}
                    </div>
                  </div>
                  <Link to={`/portal/reports/${o.id}`} className="btn btn-primary btn-sm">
                    عرض النتائج
                  </Link>
                </div>
              ))}
            </div>
          )}

          {/* All Orders */}
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
              <div className="card-title" style={{ margin: 0 }}>جميع الطلبات</div>
              <Link to="/portal/orders" className="btn btn-outline btn-sm">عرض الكل</Link>
            </div>

            {loading ? (
              <div className="loading-page"><div className="spinner" /></div>
            ) : orders.length === 0 ? (
              <div className="empty-state">
                <p>لا توجد طلبات بعد</p>
                <span>ستظهر طلبات الفحوصات هنا عند إضافتها من قبل طبيبك</span>
              </div>
            ) : (
              orders.slice(0, 5).map(o => (
                <div key={o.id} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "10px 0", borderBottom: "1px solid var(--gray-100)"
                }}>
                  <div>
                    <span style={{ fontFamily: "monospace", fontSize: ".85rem" }}>#{o.id?.slice(0, 8)}</span>
                    <span style={{ fontSize: ".8rem", color: "var(--gray-500)", marginRight: 8 }}>
                      {new Date(o.created_at).toLocaleDateString("ar-SA")}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <span className={`badge badge-${o.status}`}>
                      {o.status === "completed" ? "جاهز" : o.status === "processing" ? "قيد التحليل" : "انتظار"}
                    </span>
                    <Link to={`/portal/orders/${o.id}/track`} className="btn btn-outline btn-sm">تتبع</Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
