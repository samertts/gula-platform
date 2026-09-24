// App.jsx — GULA Platform root (multilingual + dark mode)
const { useState, useMemo } = React;

function SettingsView({ dark, setDark }) {
  const { t, lang } = React.useContext(LangContext);
  const cfg = LANGS[lang];
  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';

  return (
    <div style={{ padding: 28, flex: 1, overflowY: 'auto', fontFamily: cfg.font, direction: cfg.dir, background: bg }}>
      <div style={{ fontSize: 18, fontWeight: 700, color: fg1, marginBottom: 24 }}>{t('nav_settings')}</div>
      <div style={{ background: surface, borderRadius: 12, padding: 20, boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)', border: dark ? `1px solid ${border}` : 'none', maxWidth: 480 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: fg1, marginBottom: 16 }}>Appearance</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', borderBottom: `1px solid ${border}` }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 500, color: fg1 }}>Dark Mode</div>
            <div style={{ fontSize: 11, color: fg2, marginTop: 2 }}>Switch between light and dark interface</div>
          </div>
          <div
            onClick={() => setDark(d => !d)}
            style={{
              width: 44, height: 24, borderRadius: 12, cursor: 'pointer',
              background: dark ? '#2563EB' : '#E2E8F0',
              position: 'relative', transition: 'background 0.2s', flexShrink: 0,
            }}
          >
            <div style={{
              width: 18, height: 18, borderRadius: '50%', background: '#fff',
              position: 'absolute', top: 3,
              left: dark ? 23 : 3,
              transition: 'left 0.2s',
              boxShadow: '0 1px 3px rgb(0 0 0/.2)',
            }}></div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 500, color: fg1 }}>Language</div>
            <div style={{ fontSize: 11, color: fg2, marginTop: 2 }}>EN / ع / ک / TK / ܣ — switch in the top bar</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [page, setPage] = useState('dashboard');
  const [lang, setLang] = useState(() => localStorage.getItem('gula_lang') || 'en');
  const [dark, setDark] = useState(() => localStorage.getItem('gula_dark') === 'true');

  // Persist preferences
  React.useEffect(() => { localStorage.setItem('gula_dark', dark); }, [dark]);
  React.useEffect(() => { localStorage.setItem('gula_lang', lang); }, [lang]);

  const ctxValue = useMemo(() => ({
    lang,
    setLang,
    t: (key) => (LANGS[lang] && LANGS[lang][key]) || key,
  }), [lang]);

  const cfg = LANGS[lang];
  const isRtl = cfg.dir === 'rtl';

  const bg   = dark ? '#0F172A' : '#F8FAFC';
  const side = dark ? '#1E293B' : '#fff';
  const sideBorder = dark ? '1px solid #334155' : undefined;

  const renderView = () => {
    if (page === 'dashboard') return <DashboardView dark={dark} />;
    if (page === 'patients')  return <PatientsView dark={dark} />;
    if (page === 'samples')   return <SamplesView dark={dark} />;
    if (page === 'results')   return <ResultsView dark={dark} />;
    if (page === 'reports')   return <ReportsView dark={dark} />;
    if (page === 'billing')   return <BillingView dark={dark} />;
    if (page === 'patient_profile') return <PatientProfileView dark={dark} />;
    if (page === 'doctor_dash')     return <DoctorDashView dark={dark} />;
    if (page === 'lab_queue')       return <LabQueueView dark={dark} />;
    if (page === 'settings')  return <SettingsView dark={dark} setDark={setDark} />;
    return null;
  };

  return (
    <LangContext.Provider value={ctxValue}>
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', flexDirection: isRtl ? 'row-reverse' : 'row', background: bg }}>
        <div style={{ background: side, borderRight: !isRtl ? (dark ? '1px solid #334155' : '1px solid #E2E8F0') : undefined, borderLeft: isRtl ? (dark ? '1px solid #334155' : '1px solid #E2E8F0') : undefined }}>
          <Sidebar active={page} onNavigate={setPage} dark={dark} />
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
          <TopBar page={page} lang={lang} setLang={setLang} dark={dark} setDark={setDark} />
          {renderView()}
        </div>
      </div>
    </LangContext.Provider>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
