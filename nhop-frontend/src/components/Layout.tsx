import React from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth.store";

/* ---- Icons (inline SVG) ---- */
const Icon = {
  home:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>,
  flask:    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 3h6l1 9H8L9 3z"/><path d="M8 12l-4 7a1 1 0 0 0 .89 1.45h14.22A1 1 0 0 0 20 19l-4-7"/><line x1="9" y1="3" x2="9" y2="7"/><line x1="15" y1="3" x2="15" y2="7"/></svg>,
  users:    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  file:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>,
  activity: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  logout:   <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>,
  plus:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
  list:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>,
  settings: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 0-14.14 0"/><path d="M4.93 19.07a10 10 0 0 0 14.14 0"/></svg>,
  check:    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>,
  alert:    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  user:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>,
  link:     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>,
};

const NAV_CONFIG: Record<string, Array<{ label: string; to: string; icon: React.ReactNode; group?: string }>> = {
  lab: [
    { label: "لوحة التحكم",   to: "/lab",             icon: Icon.home },
    { label: "قائمة العمل",   to: "/lab/queue",       icon: Icon.list },
    { label: "الطلبات",       to: "/lab/orders",      icon: Icon.file },
    { label: "العينات",       to: "/lab/samples",     icon: Icon.flask },
    { label: "إدخال النتائج", to: "/lab/results",     icon: Icon.activity },
    { label: "اعتماد النتائج", to: "/lab/approval",   icon: Icon.check },
    { label: "القيم الحرجة",  to: "/lab/critical",    icon: Icon.alert },
    { label: "الملف الشخصي",  to: "/lab/profile",     icon: Icon.user },
  ],
  doctor: [
    { label: "لوحة التحكم",  to: "/doctor",             icon: Icon.home },
    { label: "المرضى",       to: "/doctor/patients",    icon: Icon.users },
    { label: "طلب فحص جديد", to: "/doctor/orders/new",  icon: Icon.plus },
    { label: "الملف الشخصي", to: "/doctor/profile",     icon: Icon.user },
  ],
  patient: [
    { label: "الرئيسية",     to: "/portal",             icon: Icon.home },
    { label: "نتائجي",       to: "/portal/results",     icon: Icon.activity },
    { label: "طلباتي",       to: "/portal/orders",      icon: Icon.list },
    { label: "الملف الشخصي", to: "/portal/profile",     icon: Icon.user },
  ],
  admin: [
    { label: "لوحة التحكم",    to: "/admin",              icon: Icon.home },
    { label: "قائمة الفحوصات", to: "/admin/catalog",      icon: Icon.flask },
    { label: "المستخدمون",     to: "/admin/users",        icon: Icon.users },
    { label: "ربط المريض",     to: "/admin/link-patient", icon: Icon.link },
    { label: "المختبر",        to: "/lab",                icon: Icon.settings },
    { label: "الطبيب",         to: "/doctor",             icon: Icon.activity },
    { label: "الملف الشخصي",   to: "/admin/profile",      icon: Icon.user },
  ],
};

const ROLE_LABELS: Record<string, string> = {
  admin:     "مدير النظام",
  lab_staff: "فني مختبر",
  doctor:    "طبيب",
  patient:   "مريض",
  citizen:   "مواطن",
};

const PORTAL_LABELS: Record<string, string> = {
  lab:     "منصة المختبر",
  doctor:  "بوابة الطبيب",
  patient: "بوابة المريض",
  admin:   "الإدارة",
};

interface LayoutProps { role: string; }

export default function Layout({ role }: LayoutProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const navItems = NAV_CONFIG[role] || [];

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const initials = user?.name?.split(" ").map(w => w[0]).slice(0, 2).join("") || "U";

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>NHOP</h1>
          <p>{PORTAL_LABELS[role] || "المنصة الصحية"}</p>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/lab" || item.to === "/doctor" || item.to === "/portal" || item.to === "/admin"}
              className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-user">
          <div className="user-avatar">{initials}</div>
          <div className="user-info" style={{ flex: 1, minWidth: 0 }}>
            <p style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user?.name}
            </p>
            <span>{ROLE_LABELS[user?.role || ""] || user?.role}</span>
          </div>
          <button onClick={handleLogout} title="تسجيل الخروج"
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--gray-400)", padding: "4px" }}>
            {Icon.logout}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
