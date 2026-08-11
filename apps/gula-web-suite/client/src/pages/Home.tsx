import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowLeftRight,
  Bell,
  Building2,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Command,
  FlaskConical,
  Globe2,
  Inbox,
  LayoutDashboard,
  LockKeyhole,
  LogOut,
  Plus,
  Save,
  Menu,
  Microscope,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  TestTube2,
  Users,
  X,
} from "lucide-react";
import { startLogin } from "@/const";
import { useAuth } from "@/_core/hooks/useAuth";
import { trpc } from "@/lib/trpc";
import type { WorkspaceId } from "@shared/lis-policy";

type Language = "ar" | "en";
type ViewId = "dashboard" | "health" | "patients" | "orders" | "samples" | "results" | "inbox" | "settings";

type QueryState<T> = { data?: T; isLoading: boolean };
type WorkspaceData = { id: WorkspaceId; label: { ar: string; en: string }; description: { ar: string; en: string }; accent: string; capabilities: readonly string[] };
type DashboardData = { workspace: WorkspaceData; counts: { orders: number; samples: number; pendingResults: number; criticalAlerts: number } | null; recentActivity: Array<{ id: number; action: string; entityType: string; outcome: string; createdAt: Date }> };
type PatientRow = { id: number; medicalRecordNumber: string; firstName: string; lastName: string; sex: string; updatedAt: Date };
type OrderRow = { id: number; orderNumber: string; priority: string; status: string; createdAt: Date };
type SampleRow = { id: number; barcode: string; specimenType: string; status: string; version: number; updatedAt: Date };
type ResultRow = { id: number; value: string | null; status: string; isCritical: number; version: number; updatedAt: Date };
type PatientTimelineEntry = { id: string; source: "laboratory" | "clinical" | "alerts" | "radiology" | "pharmacy" | "hospital" | "emergency"; kind: string; title: string; detail: string | null; status: string; isCritical: boolean; occurredAt: Date };
type InboxData = {
  notifications: Array<{ id: number; title: string; message: string; status: string; createdAt: Date }>;
  tasks: Array<{ id: number; title: string; description: string | null; priority: string; status: string; createdAt: Date }>;
  alerts: Array<{ id: number; severity: string; title: string; message: string; status: string; createdAt: Date }>;
  approvals: Array<{ id: number; title: string; description: string | null; status: string; createdAt: Date }>;
  messages: Array<{ id: number; subject: string; body: string; status: string; createdAt: Date }>;
};
type AppUser = { name: string | null; email: string | null; role: string };
type Copy = { [Key in keyof typeof copy.ar]: string };

const copy = {
  ar: {
    brand: "GULA",
    brandSub: "المنصة الصحية الوطنية الشاملة",
    welcome: "منصة صحية وطنية متكاملة للقطاعين العام والخاص والمختلط",
    welcomeText: "إدارة المستشفيات، العيادات، الصيدليات، الأشعة، الطوارئ، والصحة العامة، مع مساحة إدارة المختبرات (LIS) كمساحة تشغيل أولى متكاملة من حساب GULA موحد.",
    login: "تسجيل الدخول الآمن",
    loginHint: "استخدم حساب GULA للوصول إلى مساحات العمل الخاصة بك.",
    secure: "هوية موحدة وصلاحيات قابلة للتدقيق",
    dashboard: "نظرة عامة",
    patients: "المرضى",
    orders: "طلبات الفحوصات",
    samples: "العينات",
    results: "النتائج",
    inbox: "الوارد والمهام",
    settings: "الإعدادات",
    workspaces: "مساحات العمل",
    workspace: "مساحة العمل",
    switchWorkspace: "تبديل مساحة العمل",
    commandCenter: "مركز الأوامر",
    search: "ابحث عن مريض، طلب، عينة أو نتيجة...",
    operationalPulse: "نبض التشغيل",
    operationalPulseText: "مؤشرات مباشرة من نطاقك التنظيمي، دون أرقام تجريبية.",
    ordersCount: "الطلبات",
    samplesCount: "العينات",
    pendingResults: "نتائج بانتظار المراجعة",
    criticalAlerts: "تنبيهات حرجة",
    noData: "لا توجد بيانات في نطاقك حاليًا",
    noDataHint: "ستظهر السجلات هنا بعد تسجيل عمليات حقيقية في النظام.",
    recentActivity: "آخر نشاط موثق",
    noActivity: "لا يوجد نشاط موثق بعد",
    patientsHint: "الوصول إلى المرضى وفق الدور والسياق التنظيمي.",
    ordersHint: "تتبّع مراحل الطلب من المسودة حتى الإصدار.",
    samplesHint: "استلام العينة وربط الباركود والتحقق من المسار.",
    resultsHint: "نتائج قابلة للمراجعة والإصدار وفق قواعد المختبر.",
    inboxHint: "إدارة الإشعارات والمهام والتنبيهات الموجهة لحسابك.",
    emptyView: "هذه الوحدة جاهزة ضمن مساحة العمل الحالية.",
    emptyViewHint: "لا توجد سجلات متاحة لهذا النطاق الآن.",
    signOut: "تسجيل الخروج",
    language: "English",
    role: "الدور",
    institution: "المؤسسة",
    laboratory: "المختبر",
    account: "الحساب الموحد",
    privacy: "مركز الخصوصية",
    audit: "كل عملية حساسة تُسجل وتُراجع.",
    loading: "جارٍ تحميل السياق الآمن...",
    accessDenied: "لا توجد مساحة عمل مصرح بها لهذا الحساب.",
    retry: "إعادة المحاولة",
    patient: "المريض",
    order: "الطلب",
    sample: "العينة",
    result: "النتيجة",
    status: "الحالة",
    updated: "آخر تحديث",
    emptyInbox: "الوارد نظيف",
    emptyInboxHint: "لا توجد إشعارات أو مهام مسجلة لحسابك.",
  },
  en: {
    brand: "GULA",
    brandSub: "Comprehensive National Health Platform",
    welcome: "Integrated national health platform for public, private, and mixed sectors",
    welcomeText: "Manage hospitals, clinics, pharmacies, radiology, emergency, and public health, featuring Laboratory Information System (LIS) as the primary operational workspace from a single GULA Account.",
    login: "Secure sign in",
    loginHint: "Use your GULA Account to access your authorized workspaces.",
    secure: "Unified identity with auditable access",
    dashboard: "Overview",
    patients: "Patients",
    orders: "Lab orders",
    samples: "Samples",
    results: "Results",
    inbox: "Inbox & tasks",
    settings: "Settings",
    workspaces: "Workspaces",
    workspace: "Workspace",
    switchWorkspace: "Switch workspace",
    commandCenter: "Command center",
    search: "Search for a patient, order, sample, or result...",
    operationalPulse: "Operational pulse",
    operationalPulseText: "Live indicators from your organizational scope, with no demo numbers.",
    ordersCount: "Orders",
    samplesCount: "Samples",
    pendingResults: "Pending review",
    criticalAlerts: "Critical alerts",
    noData: "No data in your scope yet",
    noDataHint: "Records will appear here after real operations are recorded.",
    recentActivity: "Recent audited activity",
    noActivity: "No audited activity yet",
    patientsHint: "Patient access is constrained by role and organization context.",
    ordersHint: "Track each order from draft through release.",
    samplesHint: "Receive specimens, link barcodes, and verify processing.",
    resultsHint: "Reviewable and releasable results under laboratory rules.",
    inboxHint: "Manage notifications, tasks, and alerts assigned to your account.",
    emptyView: "This module is ready inside the current workspace.",
    emptyViewHint: "No records are available for this scope yet.",
    signOut: "Sign out",
    language: "العربية",
    role: "Role",
    institution: "Institution",
    laboratory: "Laboratory",
    account: "Unified account",
    privacy: "Privacy center",
    audit: "Every sensitive action is recorded and reviewable.",
    loading: "Loading secure context...",
    accessDenied: "No authorized workspace is available for this account.",
    retry: "Retry",
    patient: "Patient",
    order: "Order",
    sample: "Sample",
    result: "Result",
    status: "Status",
    updated: "Updated",
    emptyInbox: "Inbox is clear",
    emptyInboxHint: "No notifications or tasks are recorded for your account.",
  },
} as const;

export default function Home() {
  const { user, loading: authLoading, isAuthenticated, error: authError, logout } = useAuth();
  const [language, setLanguage] = useState<Language>("ar");
  const [view, setView] = useState<ViewId>("dashboard");
  const [workspaceId, setWorkspaceId] = useState<WorkspaceId | undefined>();
  const [searchTerm, setSearchTerm] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const t = copy[language];
  const direction = language === "ar" ? "rtl" : "ltr";

  const contextQuery = trpc.lis.context.useQuery(undefined, {
    enabled: isAuthenticated,
    retry: false,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    document.documentElement.dir = direction;
    document.documentElement.lang = language;
  }, [direction, language]);

  useEffect(() => {
    if (!workspaceId && contextQuery.data?.defaultWorkspaceId) {
      setWorkspaceId(contextQuery.data.defaultWorkspaceId as WorkspaceId);
    }
  }, [contextQuery.data?.defaultWorkspaceId, workspaceId]);

  const workspace = useMemo(
    () => contextQuery.data?.workspaces.find((item) => item.id === workspaceId) ?? contextQuery.data?.workspaces[0],
    [contextQuery.data?.workspaces, workspaceId],
  );

  const dashboardQuery = trpc.lis.dashboard.useQuery(
    { workspaceId },
    { enabled: isAuthenticated && Boolean(workspaceId), retry: false },
  );
  const patientsQuery = trpc.lis.patients.useQuery(
    { workspaceId },
    { enabled: isAuthenticated && Boolean(workspaceId) && view === "patients", retry: false },
  );
  const ordersQuery = trpc.lis.orders.useQuery(
    { workspaceId },
    { enabled: isAuthenticated && Boolean(workspaceId) && view === "orders", retry: false },
  );
  const samplesQuery = trpc.lis.samples.useQuery(
    { workspaceId },
    { enabled: isAuthenticated && Boolean(workspaceId) && view === "samples", retry: false },
  );
  const resultsQuery = trpc.lis.results.useQuery(
    { workspaceId },
    { enabled: isAuthenticated && Boolean(workspaceId) && view === "results", retry: false },
  );
  const inboxQuery = trpc.lis.inbox.useQuery(undefined, {
    enabled: isAuthenticated && view === "inbox",
    retry: false,
  });
  const patientTimelineQuery = trpc.lis.patientTimeline.useQuery(undefined, {
    enabled: isAuthenticated && user?.role === "patient" && view === "health",
    retry: false,
  });

  const navigation = [
    { id: "dashboard" as const, label: t.dashboard, icon: LayoutDashboard },
    ...(user?.role === "patient" ? [{ id: "health" as const, label: language === "ar" ? "سجلي الصحي" : "My health record", icon: Activity }] : []),
    { id: "patients" as const, label: t.patients, icon: Users },
    { id: "orders" as const, label: t.orders, icon: ClipboardList },
    { id: "samples" as const, label: t.samples, icon: TestTube2 },
    { id: "results" as const, label: t.results, icon: FlaskConical },
    { id: "inbox" as const, label: t.inbox, icon: Inbox },
  ];

  const chooseView = (nextView: ViewId) => {
    setView(nextView);
    setMobileMenuOpen(false);
  };

  if (authLoading || (isAuthenticated && contextQuery.isLoading)) {
    return <LoadingScreen language={language} text={t.loading} />;
  }

  if (!isAuthenticated || !user) {
    return (
      <LoginScreen
        language={language}
        onLanguageChange={setLanguage}
        onLogin={startLogin}
        error={authError?.message}
      />
    );
  }

  if (contextQuery.error) {
    return <ErrorScreen language={language} text={contextQuery.error.message} onRetry={() => contextQuery.refetch()} />;
  }

  if (!workspace) {
    return <ErrorScreen language={language} text={t.accessDenied} onRetry={() => contextQuery.refetch()} />;
  }

  return (
    <div className="gula-app" dir={direction}>
      <aside className={`gula-sidebar ${mobileMenuOpen ? "is-open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-mark"><Microscope size={22} strokeWidth={1.8} /></div>
          <div>
            <div className="brand-name">{t.brand}</div>
            <div className="brand-subtitle">{t.brandSub}</div>
          </div>
          <button className="icon-button sidebar-close" onClick={() => setMobileMenuOpen(false)} aria-label="Close menu"><X size={18} /></button>
        </div>

        <div className="workspace-card">
          <div className="eyebrow"><Sparkles size={13} /> {t.workspace}</div>
          <div className="workspace-selected">
            <div className={`workspace-dot accent-${workspace.accent}`} />
            <div className="workspace-selected-text">
              <strong>{workspace.label[language]}</strong>
              <span>{workspace.description[language]}</span>
            </div>
            <ChevronDown size={16} className="muted-icon" />
          </div>
          <select
            className="workspace-select"
            value={workspace.id}
            onChange={(event) => setWorkspaceId(event.target.value as WorkspaceId)}
            aria-label={t.switchWorkspace}
          >
            {contextQuery.data?.workspaces.map((item) => <option key={item.id} value={item.id}>{item.label[language]}</option>)}
          </select>
        </div>

        <div className="nav-label">{t.workspace}</div>
        <nav className="sidebar-nav" aria-label={t.workspace}>
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = view === item.id;
            return (
              <button key={item.id} className={`nav-item ${active ? "active" : ""}`} onClick={() => chooseView(item.id)}>
                <Icon size={18} strokeWidth={active ? 2.2 : 1.8} />
                <span>{item.label}</span>
                {item.id === "inbox" && (inboxQuery.data?.notifications.length ?? 0) > 0 ? <span className="nav-badge">{inboxQuery.data?.notifications.length}</span> : null}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-lower">
          <div className="security-note"><ShieldCheck size={17} /><div><strong>{t.account}</strong><span>{t.audit}</span></div></div>
          <button className="nav-item" onClick={() => chooseView("settings")}><Settings2 size={18} /><span>{t.settings}</span></button>
          <button className="nav-item signout" onClick={() => void logout()}><LogOut size={18} /><span>{t.signOut}</span></button>
        </div>
      </aside>

      {mobileMenuOpen ? <button className="sidebar-overlay" aria-label="Close menu" onClick={() => setMobileMenuOpen(false)} /> : null}

      <main className="gula-main">
        <header className="topbar">
          <div className="topbar-leading">
            <button className="icon-button menu-toggle" onClick={() => setMobileMenuOpen(true)} aria-label="Open menu"><Menu size={20} /></button>
            <div className="breadcrumb"><span>{t.brand}</span><ArrowLeftRight size={14} /><strong>{workspace.label[language]}</strong></div>
          </div>
          <div className="topbar-actions">
            <form className="global-search" onSubmit={(event) => { event.preventDefault(); if (searchTerm.trim()) chooseView("patients"); }}>
              <Search size={17} />
              <input value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder={t.search} aria-label={t.search} />
              <kbd><Command size={11} /> K</kbd>
            </form>
            <button className="language-toggle" onClick={() => setLanguage(language === "ar" ? "en" : "ar")}><Globe2 size={16} /><span>{t.language}</span></button>
            <button className="notification-button" onClick={() => chooseView("inbox")} aria-label={t.inbox}><Bell size={18} /><span className="notification-dot" /></button>
            <div className="profile-chip"><div className="avatar">{initials(user.name)}</div><div className="profile-copy"><strong>{user.name || t.account}</strong><span>{roleLabel(user.role, language)}</span></div><ChevronDown size={15} className="muted-icon" /></div>
          </div>
        </header>

        <div className="page-container">
          <div className="page-heading">
            <div><div className="section-kicker">{t.workspace} / {workspace.label[language]}</div><h1>{viewTitle(view, t)}</h1><p>{viewDescription(view, t)}</p></div>
            <div className="context-pill"><Building2 size={15} /><span>{contextQuery.data?.organization.institution?.[language === "ar" ? "nameAr" : "nameEn"] || t.institution}</span><span className="pill-separator">/</span><span>{contextQuery.data?.organization.laboratory?.[language === "ar" ? "nameAr" : "nameEn"] || t.laboratory}</span></div>
          </div>

          {view === "dashboard" ? <DashboardView language={language} t={t} query={dashboardQuery} workspace={workspace} onSelect={chooseView} /> : null}
          {view === "health" && user.role === "patient" ? <PatientHealthView language={language} query={patientTimelineQuery} /> : null}
          {view === "patients" ? <PatientsView language={language} t={t} query={patientsQuery} user={user} /> : null}
          {view === "orders" ? <OrdersView language={language} t={t} query={ordersQuery} user={user} workspaceId={workspace.id} /> : null}
          {view === "samples" ? <SamplesView language={language} t={t} query={samplesQuery} user={user} /> : null}
          {view === "results" ? <ResultsView language={language} t={t} query={resultsQuery} user={user} /> : null}
          {view === "inbox" ? <InboxView language={language} t={t} query={inboxQuery} /> : null}
          {view === "settings" ? <SettingsView language={language} t={t} user={user} /> : null}
        </div>
      </main>
    </div>
  );
}

function roleLabel(role: string, language: Language) {
  const labels: Record<string, { ar: string; en: string }> = {
    patient: { ar: "المواطن / المريض", en: "Citizen / Patient" },
    lab_staff: { ar: "طاقم المختبر", en: "Laboratory Staff" },
    physician: { ar: "الطبيب", en: "Physician" },
    institution_admin: { ar: "مدير المؤسسة", en: "Institution Admin" },
    system_admin: { ar: "مدير النظام", en: "System Admin" },
  };
  return labels[role]?.[language] || role;
}

function viewTitle(view: ViewId, t: Copy) {
  return { dashboard: t.dashboard, health: t.patient, patients: t.patients, orders: t.orders, samples: t.samples, results: t.results, inbox: t.inbox, settings: t.settings }[view];
}

function viewDescription(view: ViewId, t: Copy) {
  return { dashboard: t.operationalPulseText, health: t.audit, patients: t.patientsHint, orders: t.ordersHint, samples: t.samplesHint, results: t.resultsHint, inbox: t.inboxHint, settings: t.privacy }[view];
}

function LoadingScreen({ language, text }: { language: Language; text: string }) {
  return <div className="loading-screen" dir={language === "ar" ? "rtl" : "ltr"}><div className="loading-orbit"><Activity size={25} /></div><strong>{text}</strong><span>GULA HEALTH</span></div>;
}

function ErrorScreen({ language, text, onRetry }: { language: Language; text: string; onRetry: () => void }) {
  const isArabic = language === "ar";
  return <div className="loading-screen" dir={isArabic ? "rtl" : "ltr"}><div className="error-icon"><LockKeyhole size={24} /></div><strong>{text}</strong><button className="primary-button compact" onClick={onRetry}>{isArabic ? "إعادة المحاولة" : "Retry"}</button></div>;
}

function LoginScreen({ language, onLanguageChange, onLogin, error }: { language: Language; onLanguageChange: (language: Language) => void; onLogin: () => void; error?: string }) {
  const t = copy[language];
  const isArabic = language === "ar";
  return (
    <div className="login-shell" dir={isArabic ? "rtl" : "ltr"}>
      <div className="login-visual"><div className="visual-grid" /><div className="visual-top"><div className="brand-mark large"><Microscope size={30} /></div><div><div className="brand-name">GULA</div><div className="brand-subtitle">{t.brandSub}</div></div></div><div className="visual-copy"><div className="visual-kicker"><span className="live-dot" /> {isArabic ? "منصة صحية وطنية موحدة" : "Unified national health platform"}</div><h1>{isArabic ? "رعاية مترابطة،\nقرارات أكثر أمانًا." : "Connected care,\nsafer decisions."}</h1><p>{t.welcomeText}</p><div className="visual-stats"><div><strong>1</strong><span>{isArabic ? "حساب موحد" : "Unified account"}</span></div><div><strong>∞</strong><span>{isArabic ? "مساحات عمل" : "Workspaces"}</span></div><div><strong>24/7</strong><span>{isArabic ? "تدقيق وحماية" : "Audit & protection"}</span></div></div></div><div className="visual-footer"><ShieldCheck size={15} /> {t.secure}</div></div>
      <div className="login-panel"><button className="language-switch" onClick={() => onLanguageChange(isArabic ? "en" : "ar")}><Globe2 size={16} /> {t.language}</button><div className="login-card"><div className="mobile-brand"><div className="brand-mark"><Microscope size={21} /></div><div><strong>GULA</strong><small>{t.brandSub}</small></div></div><div className="eyebrow"><Sparkles size={14} /> {isArabic ? "وصول صحي موحّد" : "Unified health access"}</div><h2>{t.welcome}</h2><p>{t.loginHint}</p><button className="primary-button login-button" onClick={onLogin}><LockKeyhole size={18} /> {t.login}</button>{error ? <div className="auth-error"><X size={16} /> {error}</div> : null}<div className="login-divider"><span>{isArabic ? "يعمل عبر" : "Works across"}</span></div><div className="platforms"><span>WEB</span><span>ANDROID</span><span>iOS</span><span>DESKTOP</span></div><div className="login-note"><CheckCircle2 size={15} /> {t.audit}</div></div><div className="login-footer">© GULA Platform · {isArabic ? "الخصوصية والشروط" : "Privacy & terms"}</div></div>
    </div>
  );
}

function DashboardView({ language, t, query, workspace, onSelect }: { language: Language; t: Copy; query: QueryState<DashboardData>; workspace: WorkspaceData; onSelect: (view: ViewId) => void }) {
  const counts = query.data?.counts;
  const stats = [
    { label: t.ordersCount, value: counts?.orders, icon: ClipboardList, tone: "blue", action: "orders" as const },
    { label: t.samplesCount, value: counts?.samples, icon: TestTube2, tone: "amber", action: "samples" as const },
    { label: t.pendingResults, value: counts?.pendingResults, icon: FlaskConical, tone: "violet", action: "results" as const },
    { label: t.criticalAlerts, value: counts?.criticalAlerts, icon: Bell, tone: "rose", action: "inbox" as const },
  ];
  return <>
    <section className="workspace-hero"><div className="hero-symbol"><Microscope size={34} /></div><div><div className="hero-eyebrow">{language === "ar" ? "مساحة عمل متاحة" : "Authorized workspace"}</div><h2>{workspace.label[language]}</h2><p>{workspace.description[language]}</p></div><div className="hero-capabilities">{workspace.capabilities.slice(0, 3).map((capability) => <span key={capability}>{capability}</span>)}</div></section>
    <section className="stats-grid">{stats.map((stat) => { const Icon = stat.icon; return <button key={stat.label} className="stat-card" onClick={() => onSelect(stat.action)}><div className={`stat-icon ${stat.tone}`}><Icon size={19} /></div><div className="stat-copy"><span>{stat.label}</span><strong>{formatCount(stat.value)}</strong></div><ArrowLeftRight size={15} className="stat-arrow" /></button>; })}</section>
    <section className="dashboard-grid"><div className="panel activity-panel"><div className="panel-heading"><div><h3>{t.recentActivity}</h3><p>{t.audit}</p></div><div className="panel-heading-icon"><Activity size={17} /></div></div>{query.data?.recentActivity.length ? <div className="activity-list">{query.data.recentActivity.map((item) => <div className="activity-row" key={item.id}><div className={`activity-status ${item.outcome}`}><CheckCircle2 size={14} /></div><div><strong>{item.action}</strong><span>{item.entityType} · {new Date(item.createdAt).toLocaleString(language === "ar" ? "ar" : "en")}</span></div><span className="activity-outcome">{item.outcome}</span></div>)}</div> : <EmptyState title={t.noActivity} hint={t.noDataHint} />}</div><div className="panel focus-panel"><div className="focus-orb"><Sparkles size={21} /></div><div className="eyebrow">{language === "ar" ? "مصمم للعمل الآمن" : "Designed for safe work"}</div><h3>{language === "ar" ? "الواجهة تتكيف، والصلاحية لا تتنازل." : "The interface adapts. Authorization never does."}</h3><p>{language === "ar" ? "كل مساحة عمل تعرض القدرات التي يثبتها حسابك وسياق مؤسستك فقط." : "Each workspace exposes only capabilities proven by your account and organization context."}</p><div className="focus-rule"><ShieldCheck size={16} /><span>{language === "ar" ? "RBAC + سياق تنظيمي + سجل تدقيق" : "RBAC + organization context + audit"}</span></div></div></section>
  </>;
}

function PatientHealthView({ language, query }: { language: Language; query: QueryState<PatientTimelineEntry[]> }) {
  const isArabic = language === "ar";
  const entries = query.data ?? [];
  const sourceLabels: Record<PatientTimelineEntry["source"], string> = isArabic
    ? { laboratory: "المختبر", clinical: "العيادات والسجل السريري", alerts: "التنبيهات", radiology: "الأشعة", pharmacy: "الصيدلية", hospital: "المستشفى", emergency: "الطوارئ" }
    : { laboratory: "Laboratory", clinical: "Clinical record", alerts: "Alerts", radiology: "Radiology", pharmacy: "Pharmacy", hospital: "Hospital", emergency: "Emergency" };

  return <section className="panel data-panel patient-health-timeline">
    <div className="panel-heading">
      <div className="panel-title-wrap">
        <div className="panel-heading-icon"><Activity size={18} /></div>
        <div>
          <h3>{isArabic ? "سجلي الصحي الموحد" : "My unified health record"}</h3>
          <p>{isArabic ? "تسلسل زمني لسجلاتك المصرح بها من المختبر والأشعة والصيدلية والعيادات والمستشفى والطوارئ." : "A chronological view of your authorized laboratory, imaging, pharmacy, clinical, hospital, and emergency records."}</p>
        </div>
      </div>
      <div className="context-pill"><ShieldCheck size={15} /><span>{isArabic ? "مرئي لحسابك فقط" : "Visible only to your account"}</span></div>
    </div>
    {query.isLoading ? <div className="data-loading"><span /><span /><span /></div> : entries.length === 0 ? <EmptyState title={isArabic ? "لا توجد سجلات صحية منشورة بعد" : "No released health records yet"} hint={isArabic ? "ستظهر الفحوصات والنتائج والتحديثات السريرية هنا عند تسجيلها وإصدارها لك." : "Released results, clinical updates, and approved alerts will appear here."} /> : <div className="timeline-list">{entries.map((entry) => <article className={`timeline-entry ${entry.isCritical ? "is-critical" : ""}`} key={entry.id}>
      <div className="timeline-marker"><span /></div>
      <div className="timeline-content">
        <div className="timeline-meta"><span className={`status-chip ${entry.source}`}>{sourceLabels[entry.source]}</span><time>{new Date(entry.occurredAt).toLocaleString(isArabic ? "ar" : "en")}</time></div>
        <h4>{entry.title}</h4>
        {entry.detail ? <p>{entry.detail}</p> : null}
        <div className="timeline-footer"><span className={`status-chip ${entry.status}`}>{entry.status}</span>{entry.isCritical ? <span className="critical-flag"><Bell size={14} /> {isArabic ? "تنبيه مهم" : "Important alert"}</span> : null}</div>
      </div>
    </article>)}</div>}
  </section>;
}

function PatientsView({ language, t, query, user }: { language: Language; t: Copy; query: QueryState<PatientRow[]>; user: AppUser }) {
  const rows = query.data ?? [];
  const utils = trpc.useUtils();
  const mutation = trpc.lis.createPatient.useMutation({ onSuccess: () => { void utils.lis.patients.invalidate(); } });
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ medicalRecordNumber: "", firstName: "", lastName: "", sex: "unknown" as "female" | "male" | "other" | "unknown" });
  const canCreate = ["institution_admin", "system_admin"].includes(user.role);
  const submit = (event: React.FormEvent) => { event.preventDefault(); mutation.mutate({ ...form }); };
  return <>
    <DataPanel icon={Users} title={t.patients} hint={t.patientsHint} loading={query.isLoading} empty={rows.length === 0} emptyTitle={t.noData} emptyHint={t.noDataHint} action={canCreate ? <button className="secondary-button" onClick={() => setOpen(!open)}><Plus size={15} /> {language === "ar" ? "إضافة مريض" : "Add patient"}</button> : null}>{rows.map((row) => <div className="data-row" key={row.id}><div className="row-avatar">{row.firstName[0]}{row.lastName[0]}</div><div className="row-main"><strong>{row.firstName} {row.lastName}</strong><span>{row.medicalRecordNumber}</span></div><span className="row-meta">{row.sex}</span><span className="row-meta">{new Date(row.updatedAt).toLocaleDateString(language === "ar" ? "ar" : "en")}</span></div>)}</DataPanel>
    {open && canCreate ? <form className="inline-form panel" onSubmit={submit}><div className="form-heading"><div><div className="eyebrow">{language === "ar" ? "سجل جديد" : "New record"}</div><h3>{language === "ar" ? "إضافة مريض" : "Add patient"}</h3></div><button type="button" className="icon-button" onClick={() => setOpen(false)}><X size={17} /></button></div><div className="form-grid"><label><span>{language === "ar" ? "رقم الملف" : "MRN"}</span><input required value={form.medicalRecordNumber} onChange={(e) => setForm({ ...form, medicalRecordNumber: e.target.value })} /></label><label><span>{language === "ar" ? "الاسم الأول" : "First name"}</span><input required value={form.firstName} onChange={(e) => setForm({ ...form, firstName: e.target.value })} /></label><label><span>{language === "ar" ? "اسم العائلة" : "Last name"}</span><input required value={form.lastName} onChange={(e) => setForm({ ...form, lastName: e.target.value })} /></label><label><span>{language === "ar" ? "الجنس" : "Sex"}</span><select value={form.sex} onChange={(e) => setForm({ ...form, sex: e.target.value as typeof form.sex })}><option value="unknown">—</option><option value="female">{language === "ar" ? "أنثى" : "Female"}</option><option value="male">{language === "ar" ? "ذكر" : "Male"}</option><option value="other">{language === "ar" ? "آخر" : "Other"}</option></select></label></div>{mutation.error ? <div className="form-error">{mutation.error.message}</div> : null}<button className="primary-button compact" disabled={mutation.isPending}><Save size={15} /> {mutation.isPending ? "…" : (language === "ar" ? "حفظ" : "Save")}</button></form> : null}
  </>;
}

function OrdersView({ language, t, query, user, workspaceId }: { language: Language; t: Copy; query: QueryState<OrderRow[]>; user: AppUser; workspaceId: WorkspaceId }) {
  const rows = query.data ?? [];
  const utils = trpc.useUtils();
  const mutation = trpc.lis.createLabOrder.useMutation({ onSuccess: () => { void utils.lis.orders.invalidate(); } });
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ patientId: "", laboratoryId: "", orderNumber: "", priority: "routine" as "routine" | "urgent" | "stat", testCode: "", testNameAr: "", testNameEn: "" });
  const canCreate = user.role === "physician";
  const submit = (event: React.FormEvent) => { event.preventDefault(); mutation.mutate({ patientId: Number(form.patientId), laboratoryId: Number(form.laboratoryId), orderNumber: form.orderNumber, priority: form.priority, tests: [{ testCode: form.testCode, testNameAr: form.testNameAr, testNameEn: form.testNameEn }] }); };
  return <>
    <DataPanel icon={ClipboardList} title={t.orders} hint={t.ordersHint} loading={query.isLoading} empty={rows.length === 0} emptyTitle={t.noData} emptyHint={t.noDataHint} action={canCreate && workspaceId === "clinical" ? <button className="secondary-button" onClick={() => setOpen(!open)}><Plus size={15} /> {language === "ar" ? "طلب جديد" : "New order"}</button> : null}>{rows.map((row) => <div className="data-row" key={row.id}><div className="row-leading-icon blue"><ClipboardList size={17} /></div><div className="row-main"><strong>{row.orderNumber}</strong><span>{language === "ar" ? "أولوية" : "Priority"}: {row.priority}</span></div><span className={`status-chip ${row.status}`}>{row.status}</span><span className="row-meta">{new Date(row.createdAt).toLocaleDateString(language === "ar" ? "ar" : "en")}</span></div>)}</DataPanel>
    {open && canCreate ? <form className="inline-form panel" onSubmit={submit}><div className="form-heading"><div><div className="eyebrow">{language === "ar" ? "مسودة طلب" : "Order draft"}</div><h3>{language === "ar" ? "إنشاء طلب فحص" : "Create lab order"}</h3></div><button type="button" className="icon-button" onClick={() => setOpen(false)}><X size={17} /></button></div><div className="form-grid"><label><span>{language === "ar" ? "معرف المريض" : "Patient ID"}</span><input required inputMode="numeric" value={form.patientId} onChange={(e) => setForm({ ...form, patientId: e.target.value })} /></label><label><span>{language === "ar" ? "معرف المختبر" : "Laboratory ID"}</span><input required inputMode="numeric" value={form.laboratoryId} onChange={(e) => setForm({ ...form, laboratoryId: e.target.value })} /></label><label><span>{language === "ar" ? "رقم الطلب" : "Order number"}</span><input required value={form.orderNumber} onChange={(e) => setForm({ ...form, orderNumber: e.target.value })} /></label><label><span>{language === "ar" ? "الأولوية" : "Priority"}</span><select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value as typeof form.priority })}><option value="routine">Routine</option><option value="urgent">Urgent</option><option value="stat">STAT</option></select></label><label><span>{language === "ar" ? "رمز الفحص" : "Test code"}</span><input required value={form.testCode} onChange={(e) => setForm({ ...form, testCode: e.target.value })} /></label><label><span>{language === "ar" ? "اسم الفحص بالعربية" : "Test name (Arabic)"}</span><input required value={form.testNameAr} onChange={(e) => setForm({ ...form, testNameAr: e.target.value })} /></label><label><span>{language === "ar" ? "اسم الفحص بالإنجليزية" : "Test name (English)"}</span><input required value={form.testNameEn} onChange={(e) => setForm({ ...form, testNameEn: e.target.value })} /></label></div>{mutation.error ? <div className="form-error">{mutation.error.message}</div> : null}<button className="primary-button compact" disabled={mutation.isPending}><Save size={15} /> {mutation.isPending ? "…" : (language === "ar" ? "حفظ المسودة" : "Save draft")}</button></form> : null}
  </>;
}

function SamplesView({ language, t, query, user }: { language: Language; t: Copy; query: QueryState<SampleRow[]>; user: AppUser }) {
  const rows = query.data ?? [];
  const utils = trpc.useUtils();
  const register = trpc.lis.registerSample.useMutation({ onSuccess: () => { void utils.lis.samples.invalidate(); } });
  const transition = trpc.lis.transitionSample.useMutation({ onSuccess: () => { void utils.lis.samples.invalidate(); } });
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ orderId: "", laboratoryId: "", barcode: "", specimenType: "" });
  const canOperate = ["lab_staff", "institution_admin", "system_admin"].includes(user.role);
  const nextStatus: Record<string, "received" | "verified" | "processing" | "completed"> = { expected: "received", received: "verified", verified: "processing", processing: "completed" };
  const submit = (event: React.FormEvent) => { event.preventDefault(); register.mutate({ orderId: Number(form.orderId), laboratoryId: Number(form.laboratoryId), barcode: form.barcode, specimenType: form.specimenType }); };
  return <>
    <DataPanel icon={TestTube2} title={t.samples} hint={t.samplesHint} loading={query.isLoading} empty={rows.length === 0} emptyTitle={t.noData} emptyHint={t.noDataHint} action={canOperate ? <button className="secondary-button" onClick={() => setOpen(!open)}><Plus size={15} /> {language === "ar" ? "تسجيل عينة" : "Register sample"}</button> : null}>{rows.map((row) => <div className="data-row" key={row.id}><div className="row-leading-icon amber"><TestTube2 size={17} /></div><div className="row-main"><strong>{row.barcode}</strong><span>{row.specimenType}</span></div><span className={`status-chip ${row.status}`}>{row.status}</span>{canOperate && nextStatus[row.status] ? <button className="row-action" disabled={transition.isPending} onClick={() => transition.mutate({ id: row.id, version: row.version, nextStatus: nextStatus[row.status] })}>{language === "ar" ? "التالي" : "Advance"}</button> : null}<span className="row-meta">{new Date(row.updatedAt).toLocaleDateString(language === "ar" ? "ar" : "en")}</span></div>)}</DataPanel>
    {open && canOperate ? <form className="inline-form panel" onSubmit={submit}><div className="form-heading"><div><div className="eyebrow">{language === "ar" ? "تتبع العينة" : "Specimen tracking"}</div><h3>{language === "ar" ? "تسجيل عينة جديدة" : "Register sample"}</h3></div><button type="button" className="icon-button" onClick={() => setOpen(false)}><X size={17} /></button></div><div className="form-grid"><label><span>{language === "ar" ? "معرف الطلب" : "Order ID"}</span><input required inputMode="numeric" value={form.orderId} onChange={(e) => setForm({ ...form, orderId: e.target.value })} /></label><label><span>{language === "ar" ? "معرف المختبر" : "Laboratory ID"}</span><input required inputMode="numeric" value={form.laboratoryId} onChange={(e) => setForm({ ...form, laboratoryId: e.target.value })} /></label><label><span>{language === "ar" ? "الباركود" : "Barcode"}</span><input required value={form.barcode} onChange={(e) => setForm({ ...form, barcode: e.target.value })} /></label><label><span>{language === "ar" ? "نوع العينة" : "Specimen type"}</span><input required value={form.specimenType} onChange={(e) => setForm({ ...form, specimenType: e.target.value })} /></label></div>{register.error ? <div className="form-error">{register.error.message}</div> : null}<button className="primary-button compact" disabled={register.isPending}><Save size={15} /> {register.isPending ? "…" : (language === "ar" ? "حفظ" : "Save")}</button></form> : null}
  </>;
}

function ResultsView({ language, t, query, user }: { language: Language; t: Copy; query: QueryState<ResultRow[]>; user: AppUser }) {
  const rows = query.data ?? [];
  const utils = trpc.useUtils();
  const enter = trpc.lis.enterResult.useMutation({ onSuccess: () => { void utils.lis.results.invalidate(); } });
  const transition = trpc.lis.transitionResult.useMutation({ onSuccess: () => { void utils.lis.results.invalidate(); } });
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ orderTestId: "", sampleId: "", value: "", unit: "", referenceRange: "", interpretation: "", isCritical: false });
  const canEnter = ["lab_staff", "institution_admin", "system_admin"].includes(user.role);
  const canReview = ["physician", "institution_admin", "system_admin"].includes(user.role);
  const nextStatus: Record<string, "pending_review" | "approved" | "released"> = { entered: "pending_review", pending_review: "approved", approved: "released" };
  const submit = (event: React.FormEvent) => { event.preventDefault(); enter.mutate({ orderTestId: Number(form.orderTestId), sampleId: Number(form.sampleId), value: form.value, unit: form.unit, referenceRange: form.referenceRange, interpretation: form.interpretation, isCritical: form.isCritical }); };
  return <>
    <DataPanel icon={FlaskConical} title={t.results} hint={t.resultsHint} loading={query.isLoading} empty={rows.length === 0} emptyTitle={t.noData} emptyHint={t.noDataHint} action={canEnter ? <button className="secondary-button" onClick={() => setOpen(!open)}><Plus size={15} /> {language === "ar" ? "إدخال نتيجة" : "Enter result"}</button> : null}>{rows.map((row) => <div className="data-row" key={row.id}><div className="row-leading-icon violet"><FlaskConical size={17} /></div><div className="row-main"><strong>{row.value || "—"}</strong><span>{row.isCritical ? (language === "ar" ? "قيمة حرجة" : "Critical value") : (language === "ar" ? "نتيجة مسجلة" : "Recorded result")}</span></div><span className={`status-chip ${row.status}`}>{row.status}</span>{canReview && nextStatus[row.status] ? <button className="row-action" disabled={transition.isPending} onClick={() => transition.mutate({ id: row.id, version: row.version, nextStatus: nextStatus[row.status] })}>{language === "ar" ? "مراجعة" : "Review"}</button> : null}<span className="row-meta">{new Date(row.updatedAt).toLocaleDateString(language === "ar" ? "ar" : "en")}</span></div>)}</DataPanel>
    {open && canEnter ? <form className="inline-form panel" onSubmit={submit}><div className="form-heading"><div><div className="eyebrow">{language === "ar" ? "دون تجاوز التحقق" : "Verified sample required"}</div><h3>{language === "ar" ? "إدخال نتيجة" : "Enter result"}</h3></div><button type="button" className="icon-button" onClick={() => setOpen(false)}><X size={17} /></button></div><div className="form-grid"><label><span>{language === "ar" ? "معرف بند الطلب" : "Order test ID"}</span><input required inputMode="numeric" value={form.orderTestId} onChange={(e) => setForm({ ...form, orderTestId: e.target.value })} /></label><label><span>{language === "ar" ? "معرف العينة" : "Sample ID"}</span><input required inputMode="numeric" value={form.sampleId} onChange={(e) => setForm({ ...form, sampleId: e.target.value })} /></label><label><span>{language === "ar" ? "القيمة" : "Value"}</span><input value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} /></label><label><span>{language === "ar" ? "الوحدة" : "Unit"}</span><input value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} /></label><label className="wide-field"><span>{language === "ar" ? "التفسير" : "Interpretation"}</span><textarea value={form.interpretation} onChange={(e) => setForm({ ...form, interpretation: e.target.value })} /></label></div><label className="checkbox-field"><input type="checkbox" checked={form.isCritical} onChange={(e) => setForm({ ...form, isCritical: e.target.checked })} /><span>{language === "ar" ? "تمييز كقيمة حرجة" : "Mark as critical"}</span></label>{enter.error ? <div className="form-error">{enter.error.message}</div> : null}<button className="primary-button compact" disabled={enter.isPending}><Save size={15} /> {enter.isPending ? "…" : (language === "ar" ? "حفظ النتيجة" : "Save result")}</button></form> : null}
  </>;
}

function InboxView({ language, t, query }: { language: Language; t: Copy; query: QueryState<InboxData> }) {
  const notifications = query.data?.notifications ?? [];
  const tasks = query.data?.tasks ?? [];
  const alerts = query.data?.alerts ?? [];
  const approvals = query.data?.approvals ?? [];
  const messages = query.data?.messages ?? [];
  const total = notifications.length + tasks.length + alerts.length + approvals.length + messages.length;
  return (
    <div className="inbox-layout">
      <DataPanel icon={Inbox} title={t.inbox} hint={t.inboxHint} loading={query.isLoading} empty={total === 0} emptyTitle={t.emptyInbox} emptyHint={t.emptyInboxHint}>
        {tasks.map((task) => (
          <div className="data-row" key={`task-${task.id}`}>
            <div className="row-leading-icon blue"><ClipboardList size={17} /></div>
            <div className="row-main"><strong>{task.title}</strong><span>{task.description || (language === "ar" ? "مهمة تشغيلية" : "Operational task")}</span></div>
            <span className={`status-chip ${task.status}`}>{task.priority}</span>
            <span className="row-meta">{new Date(task.createdAt).toLocaleDateString(language === "ar" ? "ar" : "en")}</span>
          </div>
        ))}
        {alerts.map((item) => (
          <div className="data-row" key={`alert-${item.id}`}>
            <div className="row-leading-icon rose"><Bell size={17} /></div>
            <div className="row-main"><strong>{item.title}</strong><span>{item.message}</span></div>
            <span className={`status-chip ${item.severity}`}>{item.severity}</span>
            <span className="row-meta">{new Date(item.createdAt).toLocaleDateString(language === "ar" ? "ar" : "en")}</span>
          </div>
        ))}
        {notifications.map((item) => (
          <div className="data-row" key={`notif-${item.id}`}>
            <div className="row-leading-icon amber"><Bell size={17} /></div>
            <div className="row-main"><strong>{item.title}</strong><span>{item.message}</span></div>
            <span className={`status-chip ${item.status}`}>{item.status}</span>
            <span className="row-meta">{new Date(item.createdAt).toLocaleDateString(language === "ar" ? "ar" : "en")}</span>
          </div>
        ))}
        {approvals.map((item) => (
          <div className="data-row" key={`approval-${item.id}`}>
            <div className="row-leading-icon violet"><CheckCircle2 size={17} /></div>
            <div className="row-main"><strong>{item.title}</strong><span>{item.description || (language === "ar" ? "موافقة مطلوبة" : "Approval required")}</span></div>
            <span className={`status-chip ${item.status}`}>{item.status}</span>
            <span className="row-meta">{new Date(item.createdAt).toLocaleDateString(language === "ar" ? "ar" : "en")}</span>
          </div>
        ))}
        {messages.map((item) => (
          <div className="data-row" key={`message-${item.id}`}>
            <div className="row-leading-icon blue"><Inbox size={17} /></div>
            <div className="row-main"><strong>{item.subject}</strong><span>{item.body}</span></div>
            <span className={`status-chip ${item.status}`}>{item.status}</span>
            <span className="row-meta">{new Date(item.createdAt).toLocaleDateString(language === "ar" ? "ar" : "en")}</span>
          </div>
        ))}
      </DataPanel>
    </div>
  );
}

function SettingsView({ language, t, user }: { language: Language; t: Copy; user: AppUser }) {
  return <div className="settings-grid"><div className="panel settings-profile"><div className="avatar large-avatar">{initials(user.name)}</div><div><div className="eyebrow">{t.account}</div><h3>{user.name || "GULA Account"}</h3><p>{user.email || "—"}</p></div><div className="role-chip">{roleLabel(user.role, language)}</div></div><div className="panel settings-list"><SettingRow icon={ShieldCheck} title={language === "ar" ? "مركز الأمان" : "Security center"} description={language === "ar" ? "الجلسات والأجهزة والتحقق المتدرج" : "Sessions, devices, and step-up authentication"} /><SettingRow icon={LockKeyhole} title={t.privacy} description={language === "ar" ? "الموافقات وسجل الوصول إلى بياناتك" : "Consents and access history"} /><SettingRow icon={ArrowLeftRight} title={language === "ar" ? "السياق التنظيمي" : "Organization context"} description={language === "ar" ? "المؤسسة والمختبر ونطاق البيانات" : "Institution, laboratory, and data scope"} /></div></div>;
}

function SettingRow({ icon: Icon, title, description }: { icon: typeof ShieldCheck; title: string; description: string }) {
  return <div className="setting-row"><div className="setting-icon"><Icon size={18} /></div><div><strong>{title}</strong><span>{description}</span></div><ChevronDown size={16} className="muted-icon" /></div>;
}

function DataPanel({ icon: Icon, title, hint, loading, empty, emptyTitle, emptyHint, action, children }: { icon: typeof Users; title: string; hint: string; loading: boolean; empty: boolean; emptyTitle: string; emptyHint: string; action?: React.ReactNode; children: React.ReactNode }) {
  return <section className="panel data-panel"><div className="panel-heading"><div className="panel-title-wrap"><div className="panel-heading-icon"><Icon size={18} /></div><div><h3>{title}</h3><p>{hint}</p></div></div><div className="panel-actions">{action}<button className="secondary-button"><Search size={15} /> Filter</button></div></div>{loading ? <div className="data-loading"><span /><span /><span /></div> : empty ? <EmptyState title={emptyTitle} hint={emptyHint} /> : <div className="data-list">{children}</div>}</section>;
}

function EmptyState({ title, hint }: { title: string; hint: string }) {
  return <div className="empty-state"><div className="empty-icon"><Activity size={20} /></div><strong>{title}</strong><span>{hint}</span></div>;
}

function formatCount(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : new Intl.NumberFormat().format(value);
}

function initials(name: string | null | undefined) {
  return (name || "GULA")
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}
