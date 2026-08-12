import { BellOff, ChevronLeft, ClipboardList, FileBarChart2, FlaskConical, LayoutDashboard, Menu, Settings, Users, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { nextMobileSidebarState } from "@/lib/lab-data";

const menuItems = [
  { label: "الرئيسية", path: "/dashboard", icon: LayoutDashboard },
  { label: "الطلبات", path: "/orders", icon: ClipboardList },
  { label: "المرضى", path: "/patients", icon: Users },
  { label: "التقارير", path: "/reports", icon: FileBarChart2 },
  { label: "الإعدادات", path: "/settings", icon: Settings },
];

const pageTitles: Record<string, string> = {
  "/": "نظرة عامة", "/dashboard": "نظرة عامة", "/orders": "إدارة الطلبات", "/patients": "سجل المرضى", "/reports": "التقارير", "/settings": "الإعدادات",
};

export default function LabShell({ children }: { children: React.ReactNode }) {
  const [location, setLocation] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") setMobileOpen(false); };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const navigate = (path: string) => { setLocation(path); setMobileOpen(false); };

  return (
    <div className="app-shell">
      {mobileOpen ? <button className="sidebar-scrim" aria-label="إغلاق القائمة" onClick={() => setMobileOpen(false)} /> : null}
      <aside className={`sidebar ${mobileOpen ? "sidebar--open" : ""}`} aria-label="التنقل الرئيسي">
        <div className="brand-lockup"><span className="brand-mark"><FlaskConical size={24} strokeWidth={2.2} /></span><span className="brand-word"><b>GULA</b><small>إدارة المختبرات</small></span><button className="icon-button sidebar-close" aria-label="إغلاق القائمة" onClick={() => setMobileOpen(false)}><X size={20} /></button></div>
        <nav className="sidebar-nav"><p className="nav-label">القائمة الرئيسية</p>{menuItems.map((item) => { const Icon = item.icon; const active = location === item.path || (item.path === "/dashboard" && location === "/"); return <button key={item.path} className={`nav-item ${active ? "nav-item--active" : ""}`} onClick={() => navigate(item.path)} aria-current={active ? "page" : undefined}><Icon size={19} /><span>{item.label}</span>{active ? <ChevronLeft size={16} className="nav-chevron" /> : null}</button>; })}</nav>
        <div className="sidebar-footer"><div className="lab-status"><span className="status-dot status-dot--muted" /> حالة النظام غير متاحة</div><div className="user-card"><div className="user-avatar">—</div><div className="user-info"><b>لم تُحمّل هوية المستخدم</b><span>يتطلب عرض الدور عقد جلسة فعليًا</span></div></div></div>
      </aside>
      <div className="app-main">
        <header className="topbar"><button className="icon-button menu-button" aria-label="فتح القائمة" aria-expanded={mobileOpen} onClick={() => setMobileOpen(nextMobileSidebarState(mobileOpen))}><Menu size={22} /></button><div className="topbar-title"><span>GULA / {pageTitles[location] ?? "المنصة"}</span><h1>{pageTitles[location] ?? "المنصة"}</h1></div><div className="topbar-actions"><span className="outline-button"><BellOff size={17} /> التنبيهات غير متاحة</span></div></header>
        <main className="content-area">{children}</main>
      </div>
    </div>
  );
}
