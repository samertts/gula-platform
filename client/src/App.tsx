import { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  Bell,
  CheckCircle,
  ChevronLeft,
  Clock,
  Download,
  FileText,
  Menu,
  Plus,
  Search,
  Settings,
  Shield,
  Users,
  X,
} from "lucide-react";
import "./styles.css";

type ServiceState = "healthy" | "degraded" | "unknown";

interface PlatformStatus {
  status: ServiceState;
  updatedAt: string;
  message: string;
}

interface ActivityItem {
  id: string;
  title: string;
  detail: string;
  time: string;
  state: "done" | "review" | "new";
}

interface DashboardData {
  environment: "demo";
  generatedAt: string;
  user: { name: string; role: string; facility: string };
  summary: Array<{ label: string; value: string; note: string; trend: "up" | "down" | "neutral" }>;
  workload: Array<{ day: string; value: number }>;
  queue: Array<{ id: string; type: string; status: string; urgency: "normal" | "priority"; updated: string }>;
  activity: ActivityItem[];
  safety: { verifiedSamples: number; pendingReview: number; auditEvents: number };
}

const statusText: Record<ServiceState, string> = {
  healthy: "الخدمات الأساسية تعمل بصورة طبيعية",
  degraded: "المنصة تعمل في وضع محدود",
  unknown: "يجري التحقق من حالة المنصة",
};

const getActivityIcon = (state: ActivityItem["state"]) => {
  if (state === "done") return <CheckCircle size={18} />;
  if (state === "review") return <AlertCircle size={18} />;
  return <Users size={18} />;
};

function App() {
  const [screen, setScreen] = useState<"signin" | "dashboard">("signin");
  const [platformStatus, setPlatformStatus] = useState<PlatformStatus>({
    status: "unknown",
    updatedAt: "",
    message: statusText.unknown,
  });
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [isStartingDemo, setIsStartingDemo] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [isNavOpen, setIsNavOpen] = useState(false);

  useEffect(() => {
    void loadPlatformStatus();
    if (window.sessionStorage.getItem("gula_demo_active") === "true") {
      void loadDemoDashboard();
    }
  }, []);

  async function loadPlatformStatus() {
    try {
      const response = await fetch("/api/v1/demo/status", { credentials: "include" });
      if (!response.ok) throw new Error("status-unavailable");
      const nextStatus = (await response.json()) as PlatformStatus;
      setPlatformStatus(nextStatus);
    } catch {
      setPlatformStatus({
        status: "unknown",
        updatedAt: "",
        message: "تعذر التحقق الآن. ستظل بيانات العرض محاكية وآمنة.",
      });
    }
  }

  async function startDemo() {
    setIsStartingDemo(true);
    setNotice(null);
    try {
      const response = await fetch("/api/v1/demo/session", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) throw new Error("demo-session-not-created");
      window.sessionStorage.setItem("gula_demo_active", "true");
      await loadDemoDashboard();
    } catch {
      setNotice("تعذّر تشغيل النسخة التجريبية. تحقّق من اتصال الواجهة بخدمة المنصة ثم أعد المحاولة.");
    } finally {
      setIsStartingDemo(false);
    }
  }

  async function loadDemoDashboard() {
    try {
      const response = await fetch("/api/v1/demo/dashboard", { credentials: "include" });
      if (!response.ok) throw new Error("demo-dashboard-not-available");
      const data = (await response.json()) as DashboardData;
      setDashboard(data);
      setScreen("dashboard");
    } catch {
      window.sessionStorage.removeItem("gula_demo_active");
      setScreen("signin");
      setNotice("انتهت جلسة العرض أو لم تكتمل. يمكنك بدء جلسة تجريبية جديدة دون الوصول إلى أي بيانات حقيقية.");
    }
  }

  async function leaveDemo() {
    window.sessionStorage.removeItem("gula_demo_active");
    setDashboard(null);
    setScreen("signin");
    setIsNavOpen(false);
    try {
      await fetch("/api/v1/demo/session", { method: "DELETE", credentials: "include" });
    } catch {
      // Ending the client session is sufficient for a non-clinical demo; the secure cookie expires automatically.
    }
  }

  if (screen === "dashboard" && dashboard) {
    return <Dashboard data={dashboard} isNavOpen={isNavOpen} onToggleNav={() => setIsNavOpen((open) => !open)} onLeaveDemo={leaveDemo} />;
  }

  return (
    <main className="auth-shell" dir="rtl">
      <section className="auth-visual" aria-label="تعريف بمنصة جولا">
        <div className="orb orb-one" />
        <div className="orb orb-two" />
        <header className="brand-row">
          <a className="brand" href="/" aria-label="الصفحة الرئيسية لمنصة جولا">
            <span className="brand-mark"><Activity size={22} strokeWidth={2.5} /></span>
            <span>جولا <small>GULA</small></span>
          </a>
          <span className={`system-pill ${platformStatus.status}`}>
            <span className="status-dot" />
            {platformStatus.status === "healthy" ? "جاهزية المنصة" : "فحص الجاهزية"}
          </span>
        </header>

        <div className="auth-hero">
          <p className="eyebrow">نظام معلومات المختبرات الصحية</p>
          <h1>قرارات مخبرية أوضح.<br />رعاية أكثر أماناً.</h1>
          <p className="hero-copy">واجهة تشغيلية موحّدة تدعم مسار العيّنة من الاستلام إلى التحقق، مع قابلية تتبع واضحة وأدوار وصول محكومة.</p>

          <div className="trust-grid" aria-label="مزايا موثوقية المنصة">
            <article>
              <span className="trust-icon teal"><Shield size={22} /></span>
              <div><strong>وصول محكوم</strong><small>أدوار وصلاحيات بحسب السياق</small></div>
            </article>
            <article>
              <span className="trust-icon purple"><CheckCircle size={22} /></span>
              <div><strong>سجل قابل للتتبع</strong><small>توثيق للعمليات الحساسة</small></div>
            </article>
            <article>
              <span className="trust-icon orange"><Activity size={22} /></span>
              <div><strong>تشغيل مرن</strong><small>مؤشرات حالة واضحة للفريق</small></div>
            </article>
          </div>
        </div>

        <footer className="visual-footer">
          <span className={`status-dot ${platformStatus.status}`} />
          <span>{platformStatus.message || statusText[platformStatus.status]}</span>
        </footer>
      </section>

      <section className="auth-panel">
        <div className="language-switch" aria-label="اختيار اللغة">
          <button className="active" type="button">العربية</button>
          <button type="button" disabled title="سيتم تفعيل الترجمة في الإصدار التالي">EN</button>
          <button type="button" disabled title="سيتم تفعيل الترجمة في الإصدار التالي">کوردی</button>
        </div>

        <div className="auth-content">
          <div className="mobile-brand brand">
            <span className="brand-mark"><Activity size={21} strokeWidth={2.5} /></span>
            <span>جولا <small>GULA</small></span>
          </div>
          <p className="eyebrow">بوابة الوصول الآمن</p>
          <h2>أهلاً بعودتك</h2>
          <p className="auth-subtitle">اختر نوع الوصول المناسب. لا تستخدم النسخة التجريبية في الأعمال السريرية أو مع بيانات المرضى.</p>

          {notice && <div className="notice" role="alert"><AlertCircle size={18} /><span>{notice}</span></div>}

          <div className="access-card">
            <div className="access-icon primary"><Shield size={24} /></div>
            <div>
              <strong>دخول المؤسسة</strong>
              <p>للمستخدمين المفوّضين عبر مزود هوية المؤسسة.</p>
            </div>
            <button type="button" className="icon-button" disabled title="يتطلب ربط مزود الهوية المؤسسي"><ArrowLeft size={20} /></button>
          </div>

          <div className="demo-card">
            <div className="demo-card-heading">
              <span className="access-icon demo"><Activity size={23} /></span>
              <div><strong>تجربة آمنة للمنصة</strong><p>مساحة عرض مستقلة ببيانات صناعية بالكامل.</p></div>
            </div>
            <ul>
              <li>لا تتصل ببيانات المرضى أو المختبرات الفعلية.</li>
              <li>تنتهي الجلسة تلقائياً بعد فترة قصيرة.</li>
              <li>توضح مسار العمل والضوابط دون أي عمليات سريرية.</li>
            </ul>
            <button className="primary-button" type="button" onClick={() => void startDemo()} disabled={isStartingDemo}>
              <span>{isStartingDemo ? "يجري تجهيز المساحة…" : "تشغيل الوصول التجريبي"}</span>
              <ArrowLeft size={19} />
            </button>
          </div>

          <p className="auth-footnote">باستخدامك للمنصة، تقرّ بالالتزام بسياسات الخصوصية والاستخدام المؤسسي المعتمدة.</p>
        </div>

        <footer className="auth-footer">
          <span>© {new Date().getFullYear()} GULA Platform</span>
          <a href="/privacy">الخصوصية</a>
          <a href="/terms">شروط الاستخدام</a>
        </footer>
      </section>
    </main>
  );
}

function Dashboard({ data, isNavOpen, onToggleNav, onLeaveDemo }: { data: DashboardData; isNavOpen: boolean; onToggleNav: () => void; onLeaveDemo: () => void }) {
  const navItems = ["نظرة عامة", "المرضى", "الطلبات", "العينات", "النتائج", "التقارير"];
  const peak = Math.max(...data.workload.map((item) => item.value));

  return (
    <main className="app-shell" dir="rtl">
      <aside className={`sidebar ${isNavOpen ? "open" : ""}`}>
        <div className="sidebar-brand brand">
          <span className="brand-mark"><Activity size={21} strokeWidth={2.5} /></span>
          <span>جولا <small>GULA</small></span>
          <button className="sidebar-close" type="button" onClick={onToggleNav} aria-label="إغلاق القائمة"><X size={20} /></button>
        </div>
        <div className="demo-badge"><span className="status-dot" /> بيئة عرض تجريبية</div>
        <nav aria-label="التنقل الرئيسي">
          {navItems.map((item, index) => <button className={`nav-item ${index === 0 ? "selected" : ""}`} type="button" key={item}><span className="nav-symbol">{index + 1}</span>{item}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <button className="nav-item" type="button"><Settings size={18} />الإعدادات</button>
          <button className="leave-demo" type="button" onClick={onLeaveDemo}>إنهاء النسخة التجريبية <ArrowLeft size={17} /></button>
        </div>
      </aside>

      {isNavOpen && <button className="sidebar-backdrop" type="button" aria-label="إغلاق القائمة" onClick={onToggleNav} />}

      <section className="workspace">
        <header className="topbar">
          <button className="menu-button" type="button" onClick={onToggleNav} aria-label="فتح القائمة"><Menu size={23} /></button>
          <div className="breadcrumb"><span>مساحة العمل</span><ChevronLeft size={15} /><strong>نظرة عامة</strong></div>
          <div className="top-actions">
            <button className="search-button" type="button" aria-label="البحث"><Search size={19} /><span>بحث سريع</span></button>
            <button className="round-button" type="button" aria-label="التنبيهات"><Bell size={19} /><i /></button>
            <div className="profile"><span className="avatar">د</span><div><strong>{data.user.name}</strong><small>{data.user.role}</small></div></div>
          </div>
        </header>

        <div className="demo-banner"><Shield size={18} /><span><strong>عرض توضيحي فقط.</strong> جميع الأسماء والمؤشرات والأنشطة أدناه بيانات محاكية، ولا تتاح أي عمليات سريرية أو بيانات حقيقية.</span></div>

        <div className="dashboard-content">
          <div className="dashboard-title-row">
            <div><p className="eyebrow">{data.user.facility}</p><h1>صباح الخير، {data.user.name}</h1><p>هذه لمحة عن سير العمل في بيئة العرض.</p></div>
            <div className="date-box"><Clock size={17} /><span>تم التحديث للتو</span></div>
          </div>

          <section className="stat-grid" aria-label="المؤشرات الرئيسية">
            {data.summary.map((stat, index) => (
              <article className="stat-card" key={stat.label}>
                <div className={`stat-icon tone-${index}`}><Activity size={21} /></div>
                <div><p>{stat.label}</p><strong>{stat.value}</strong><small className={stat.trend}>{stat.note}</small></div>
              </article>
            ))}
          </section>

          <section className="dashboard-grid">
            <article className="panel workload-panel">
              <div className="panel-heading"><div><h2>وتيرة الاستقبال</h2><p>عينات تم استلامها خلال سبعة أيام</p></div><button className="text-button" type="button">هذا الأسبوع <ChevronLeft size={15} /></button></div>
              <div className="chart-wrap" aria-label="رسم يوضح حجم استقبال العينات خلال أسبوع">
                {data.workload.map((item) => <div className="bar-column" key={item.day}><span className="bar-value">{item.value}</span><div className="bar-track"><i style={{ height: `${Math.round((item.value / peak) * 100)}%` }} /></div><small>{item.day}</small></div>)}
              </div>
              <div className="chart-caption"><span><i className="legend-dot" />وارد العينات</span><strong>+8.6% <small>مقارنة بالأسبوع السابق</small></strong></div>
            </article>

            <article className="panel safety-panel">
              <div className="panel-heading"><div><h2>مؤشرات السلامة</h2><p>حالة الضوابط في بيئة العرض</p></div><Shield size={22} className="panel-emblem" /></div>
              <div className="safety-ring"><div><strong>100%</strong><span>بيانات محاكية</span></div></div>
              <div className="safety-list">
                <div><span className="mini-icon green"><CheckCircle size={16} /></span><p>عينات متحققة<strong>{data.safety.verifiedSamples}</strong></p></div>
                <div><span className="mini-icon amber"><AlertCircle size={16} /></span><p>بانتظار مراجعة<strong>{data.safety.pendingReview}</strong></p></div>
                <div><span className="mini-icon blue"><FileText size={16} /></span><p>سجل نشاط<strong>{data.safety.auditEvents}</strong></p></div>
              </div>
            </article>
          </section>

          <section className="lower-grid">
            <article className="panel queue-panel">
              <div className="panel-heading"><div><h2>قائمة العمل</h2><p>طلبات تدريبية منتظرة في بيئة العرض</p></div><button type="button" className="outline-button"><Plus size={16} /> طلب تدريبي</button></div>
              <div className="table-scroll"><table><thead><tr><th>المعرّف</th><th>الفحص</th><th>الحالة</th><th>آخر تحديث</th><th /></tr></thead><tbody>{data.queue.map((row) => <tr key={row.id}><td><strong>{row.id}</strong></td><td>{row.type}</td><td><span className={`table-status ${row.urgency}`}>{row.status}</span></td><td>{row.updated}</td><td><button className="more-button" type="button" aria-label={`تفاصيل ${row.id}`}><ChevronLeft size={17} /></button></td></tr>)}</tbody></table></div>
              <button className="view-all" type="button">عرض قائمة التدريب كاملة <ArrowLeft size={16} /></button>
            </article>

            <article className="panel activity-panel">
              <div className="panel-heading"><div><h2>آخر الأنشطة</h2><p>تسلسل أحداث تمثيلي</p></div><button className="round-button compact" type="button" aria-label="تنزيل سجل العرض"><Download size={17} /></button></div>
              <div className="activity-list">{data.activity.map((item) => <div className="activity-row" key={item.id}><span className={`activity-icon ${item.state}`}>{getActivityIcon(item.state)}</span><div><strong>{item.title}</strong><p>{item.detail}</p></div><time>{item.time}</time></div>)}</div>
            </article>
          </section>
        </div>
      </section>
    </main>
  );
}

export default App;
