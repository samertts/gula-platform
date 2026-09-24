// Sidebar.jsx — GULA Platform navigation sidebar (multilingual)
const { useContext: useCtxSidebar } = React;

const NAV_KEYS = [
  { id: 'dashboard', key: 'nav_dashboard', section: 'nav_main', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
  )},
  { id: 'patients', key: 'nav_patients', section: 'nav_main', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
  )},
  { id: 'samples', key: 'nav_samples', section: 'nav_main', badge: 5, icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/></svg>
  )},
  { id: 'results', key: 'nav_results', section: 'nav_main', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
  )},
  { id: 'patient_profile', key: 'nav_patient_profile', section: 'nav_main', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
  )},
  { id: 'doctor_dash', key: 'nav_doctor_dash', section: 'nav_main', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
  )},
  { id: 'lab_queue', key: 'nav_lab_queue', section: 'nav_main', badge: 3, icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
  )},
  { id: 'reports', key: 'nav_reports', section: 'nav_manage', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
  )},
  { id: 'billing', key: 'nav_billing', section: 'nav_manage', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
  )},
  { id: 'settings', key: 'nav_settings', section: 'nav_system', icon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 1 1-14.14 0"/></svg>
  )},
];

const sidebarStyles = {
  sidebar: (dir) => ({
    width: 220, minWidth: 220, height: '100%',
    background: '#fff',
    borderRight: dir === 'ltr' ? '1px solid #E2E8F0' : 'none',
    borderLeft: dir === 'rtl' ? '1px solid #E2E8F0' : 'none',
    display: 'flex', flexDirection: 'column', padding: '20px 0', flexShrink: 0,
  }),
  logo: {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '0 18px 20px', borderBottom: '1px solid #E2E8F0', marginBottom: 12,
  },
  logoMark: { width: 36, height: 36, flexShrink: 0 },
  logoText: { fontSize: 15, fontWeight: 700, letterSpacing: '-0.02em' },
  logoSub: { fontSize: 10, color: '#94A3B8', fontWeight: 500 },
  section: {
    fontSize: 9, fontWeight: 600, color: '#94A3B8',
    textTransform: 'uppercase', letterSpacing: '0.08em',
    padding: '10px 18px 4px',
  },
  item: {
    display: 'flex', alignItems: 'center', gap: 9,
    padding: '8px 18px', margin: '1px 8px', borderRadius: 8,
    fontSize: 13, fontWeight: 500, color: '#475569', cursor: 'pointer',
  },
  itemActive: { background: '#EFF6FF', color: '#2563EB' },
  badge: {
    marginLeft: 'auto', background: '#EF4444', color: '#fff',
    fontSize: 9, fontWeight: 700, borderRadius: 9999, padding: '1px 6px',
  },
  badgeRtl: {
    marginRight: 'auto', marginLeft: 0,
  },
  bottom: {
    marginTop: 'auto', padding: '12px 8px 0', borderTop: '1px solid #E2E8F0',
  },
  user: {
    display: 'flex', alignItems: 'center', gap: 9, padding: '8px 10px', borderRadius: 8, cursor: 'pointer',
  },
  avatar: {
    width: 30, height: 30, borderRadius: '50%',
    background: 'linear-gradient(135deg,#2563EB,#8B5CF6)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    color: '#fff', fontWeight: 700, fontSize: 12, flexShrink: 0,
  },
  userName: { fontSize: 12, fontWeight: 600, color: '#0F172A' },
  userRole: { fontSize: 10, color: '#94A3B8' },
};

function Sidebar({ active, onNavigate, dark }) {
  const { t, lang } = useCtxSidebar(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#475569';
  const activeItem = dark ? { background: '#1D3461', color: '#60A5FA' } : sidebarStyles.itemActive;

  const sections = ['nav_main', 'nav_manage', 'nav_system'];
  return (
    <div style={{ ...sidebarStyles.sidebar(dir), fontFamily: cfg.font, direction: dir, background: 'inherit', height: '100%' }}>
      <div style={sidebarStyles.logo}>
        <img src="../../assets/logo-mark.svg" style={sidebarStyles.logoMark} alt="GULA" />
        <div>
          <div style={{ ...sidebarStyles.logoText, color: fg1 }}>GULA</div>
          <div style={sidebarStyles.logoSub}>Lab Platform</div>
        </div>
      </div>
      {sections.map(sec => {
        const items = NAV_KEYS.filter(n => n.section === sec);
        if (!items.length) return null;
        return (
          <React.Fragment key={sec}>
            <div style={{ ...sidebarStyles.section, color: dark ? '#475569' : '#94A3B8' }}>{t(sec)}</div>
            {items.map(n => (
              <div
                key={n.id}
                style={{ ...sidebarStyles.item, color: fg2, ...(active === n.id ? activeItem : {}) }}
                onClick={() => onNavigate(n.id)}
              >
                {n.icon}
                {t(n.key)}
                {n.badge && (
                  <span style={{ ...sidebarStyles.badge, ...(dir === 'rtl' ? sidebarStyles.badgeRtl : {}) }}>
                    {n.badge}
                  </span>
                )}
              </div>
            ))}
          </React.Fragment>
        );
      })}
      <div style={sidebarStyles.bottom}>
        <div style={sidebarStyles.user}>
          <div style={sidebarStyles.avatar}>A</div>
          <div>
            <div style={sidebarStyles.userName}>Ahmed Al-Rashidi</div>
            <div style={sidebarStyles.userRole}>Lab Manager</div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Sidebar });
