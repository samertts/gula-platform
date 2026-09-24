// TopBar.jsx — GULA Platform top bar (multilingual + dark mode)
const { useContext: useCtxTop } = React;

const PAGE_KEY_MAP = {
  dashboard: 'nav_dashboard', patients: 'nav_patients', samples: 'nav_samples',
  results: 'nav_results', reports: 'nav_reports', billing: 'nav_billing', settings: 'nav_settings',
};

function TopBar({ page, lang, setLang, dark, setDark }) {
  const { t } = useCtxTop(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;

  const bg     = dark ? '#1E293B' : '#fff';
  const border = dark ? '#334155' : '#E2E8F0';
  const fg1    = dark ? '#F1F5F9' : '#0F172A';
  const fg2    = dark ? '#94A3B8' : '#475569';
  const searchBg = dark ? '#0F172A' : '#F8FAFC';

  return (
    <div style={{
      height: 58, background: bg, borderBottom: `1px solid ${border}`,
      display: 'flex', alignItems: 'center', padding: '0 20px',
      gap: 12, flexShrink: 0, direction: dir, fontFamily: cfg.font,
    }}>
      <div style={{ fontSize: 16, fontWeight: 700, color: fg1, flex: 1 }}>
        {t(PAGE_KEY_MAP[page] || 'nav_dashboard')}
      </div>

      {/* Search */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: searchBg, border: `1.5px solid ${border}`, borderRadius: 8, padding: '6px 12px', width: 200 }}>
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 12, color: fg2, width: '100%', fontFamily: cfg.font, direction: dir }} placeholder={t('search_placeholder')} />
      </div>

      {/* System online badge */}
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 10px', borderRadius: 9999, background: '#DCFCE7', color: '#15803D', fontSize: 11, fontWeight: 600, flexShrink: 0, whiteSpace: 'nowrap' }}>
        <svg viewBox="0 0 24 24" width="8" height="8" fill="#10B981"><circle cx="12" cy="12" r="12"/></svg>
        {t('system_online')}
      </div>

      {/* Dark mode toggle */}
      <div onClick={() => setDark(d => !d)} title="Toggle dark mode" style={{
        width: 34, height: 34, borderRadius: 8, border: `1.5px solid ${border}`,
        background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
        cursor: 'pointer', flexShrink: 0,
      }}>
        {dark
          ? <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
          : <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke={fg2} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        }
      </div>

      {/* Notifications */}
      <div style={{ width: 34, height: 34, borderRadius: 8, border: `1.5px solid ${border}`, background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', position: 'relative', flexShrink: 0 }}>
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke={fg2} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        <span style={{ position: 'absolute', top: 6, right: 6, width: 7, height: 7, background: '#EF4444', borderRadius: '50%', border: `1.5px solid ${bg}` }}></span>
      </div>

      {/* Language Switcher */}
      <LangSwitcher lang={lang} setLang={setLang} />
    </div>
  );
}

Object.assign(window, { TopBar });
