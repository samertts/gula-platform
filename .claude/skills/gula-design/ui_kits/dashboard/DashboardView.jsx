// DashboardView.jsx — main dashboard (multilingual)
const { useContext: useCtxDash } = React;

const dashStyles = {
  page: { padding: 28, overflowY: 'auto', flex: 1 },
  welcome: { marginBottom: 24 },
  welcomeTitle: { fontSize: 24, fontWeight: 700, color: '#0F172A', letterSpacing: '-0.01em' },
  welcomeSub: { fontSize: 13, color: '#64748B', marginTop: 4 },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 },
  chartsGrid: { display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 24 },
  bottomGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  card: { background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 1px 3px rgb(0 0 0/.07)' },
  cardTitle: { fontSize: 13, fontWeight: 600, color: '#0F172A', marginBottom: 2 },
  cardSub: { fontSize: 11, color: '#94A3B8', marginBottom: 14 },
  statTop: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 },
  statLabel: { fontSize: 11, color: '#64748B', fontWeight: 500, marginBottom: 4 },
  statValue: { fontSize: 28, fontWeight: 700, color: '#0F172A', lineHeight: 1 },
  iconBox: { width: 38, height: 38, borderRadius: 9, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' },
};

const STAT_ICONS = [
  { key: 'stat_patients', color: '#3B82F6', icon: <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>, value: '1,234', change: '+12%', positive: true },
  { key: 'stat_samples', color: '#8B5CF6', icon: <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/></svg>, value: '87', change: '+8%', positive: true },
  { key: 'stat_reports', color: '#F97316', icon: <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>, value: '23', change: '-5%', positive: false },
  { key: 'stat_tests', color: '#10B981', icon: <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>, value: '456', change: '+15%', positive: true },
];

const ACTIVITY_KEYS = [
  { actKey: 'act1', color: '#10B981', timeKey: 'hours_ago', timeVal: '2', icon: <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg> },
  { actKey: 'act2', color: '#F97316', timeKey: 'hours_ago', timeVal: '4', icon: <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> },
  { actKey: 'act3', color: '#3B82F6', timeKey: 'hours_ago', timeVal: '6', icon: <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg> },
  { actKey: 'act4', color: '#8B5CF6', timeKey: 'day_ago', timeVal: '', icon: <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> },
];

const QUICK_KEYS = [
  { key: 'act_register', color: '#2563EB', icon: <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> },
  { key: 'act_sample',   color: '#8B5CF6', icon: <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/></svg> },
  { key: 'act_report',   color: '#10B981', icon: <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> },
  { key: 'act_download', color: '#F97316', icon: <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> },
];

function MiniBarChart() {
  const bars = [24,28,32,26,35,20,18];
  const samp = [12,15,18,14,22,10,8];
  const days = ['M','T','W','T','F','S','S'];
  const max = 40; const h = 90;
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'flex-end', height: h + 22 }}>
      {bars.map((b, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, flex: 1 }}>
          <div style={{ display: 'flex', gap: 2, alignItems: 'flex-end', height: h }}>
            <div style={{ width: 10, height: (b/max)*h, background: '#3B82F6', borderRadius: '3px 3px 0 0' }}></div>
            <div style={{ width: 10, height: (samp[i]/max)*h, background: '#C4B5FD', borderRadius: '3px 3px 0 0' }}></div>
          </div>
          <div style={{ fontSize: 9, color: '#94A3B8', fontWeight: 500 }}>{days[i]}</div>
        </div>
      ))}
    </div>
  );
}

function DonutChart({ t }) {
  const data = [
    { labelKey: 'completed', value: 65, color: '#10B981' },
    { labelKey: 'pending',   value: 25, color: '#F59E0B' },
    { labelKey: 'failed',    value: 10, color: '#EF4444' },
  ];
  const total = 100; const r = 36; const cx = 50; const cy = 50; const stroke = 16;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <svg viewBox="0 0 100 100" width="86" height="86">
        {data.map((d, i) => {
          const dash = (d.value / total) * circ;
          const rot = (offset / total) * 360 - 90;
          offset += d.value;
          return <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={d.color} strokeWidth={stroke} strokeDasharray={`${dash} ${circ - dash}`} transform={`rotate(${rot} ${cx} ${cy})`}/>;
        })}
        <text x={cx} y={cy - 4} textAnchor="middle" fontSize="13" fontWeight="700" fill="#0F172A" fontFamily="Poppins">65%</text>
        <text x={cx} y={cy + 10} textAnchor="middle" fontSize="8" fill="#94A3B8" fontFamily="Poppins">{t('complete')}</text>
      </svg>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
        {data.map(d => (
          <div key={d.labelKey} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: d.color, flexShrink: 0 }}></div>
            <span style={{ fontSize: 11, color: '#475569', fontWeight: 500 }}>{t(d.labelKey)}</span>
            <span style={{ fontSize: 11, color: '#0F172A', fontWeight: 600, marginLeft: 'auto' }}>{d.value}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DashboardView({ dark }) {
  const { t, lang } = useCtxDash(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const cardBg = dark ? '#1E293B' : '#fff';
  const pageBg = dark ? '#0F172A' : '#F8FAFC';
  const style = { fontFamily: cfg.font, direction: dir, background: pageBg };

  return (
    <div style={{ ...dashStyles.page, ...style }}>
      <div style={dashStyles.welcome}>
        <div style={{ ...dashStyles.welcomeTitle, color: fg1 }}>{t('welcome')}</div>
        <div style={{ ...dashStyles.welcomeSub, color: fg2 }}>{t('welcome_sub')}</div>
      </div>

      <div style={dashStyles.statsGrid}>
        {STAT_ICONS.map(s => (
          <div key={s.key} style={{ ...dashStyles.card, background: cardBg }}>
            <div style={dashStyles.statTop}>
              <div>
                <div style={{ ...dashStyles.statLabel, color: fg2 }}>{t(s.key)}</div>
                <div style={{ ...dashStyles.statValue, color: fg1 }}>{s.value}</div>
              </div>
              <div style={{ ...dashStyles.iconBox, background: s.color }}>{s.icon}</div>
            </div>
            <div style={{ fontSize: 11, fontWeight: 500, color: s.positive ? '#10B981' : '#EF4444' }}>
              {s.change} {t('from_last_week')}
            </div>
          </div>
        ))}
      </div>

      <div style={dashStyles.chartsGrid}>
        <div style={{ ...dashStyles.card, background: cardBg }}>
          <div style={{ ...dashStyles.cardTitle, color: fg1 }}>{t('trends_title')}</div>
          <div style={{ ...dashStyles.cardSub, color: fg2 }}>{t('trends_sub')}</div>
          <MiniBarChart />
          <div style={{ display: 'flex', gap: 14, marginTop: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: '#475569' }}>
              <div style={{ width: 12, height: 4, background: '#3B82F6', borderRadius: 2 }}></div>
              {t('nav_patients')}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: '#475569' }}>
              <div style={{ width: 12, height: 4, background: '#C4B5FD', borderRadius: 2 }}></div>
              {t('nav_samples')}
            </div>
          </div>
        </div>
        <div style={{ ...dashStyles.card, background: cardBg }}>
          <div style={{ ...dashStyles.cardTitle, color: fg1 }}>{t('status_title')}</div>
          <div style={{ ...dashStyles.cardSub, color: fg2 }}>{t('status_sub')}</div>
          <DonutChart t={t} />
        </div>
      </div>

      <div style={dashStyles.bottomGrid}>
        <div style={{ ...dashStyles.card, background: cardBg }}>
          <div style={{ ...dashStyles.cardTitle, color: fg1 }}>{t('quick_title')}</div>
          <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {QUICK_KEYS.map(a => (
              <button key={a.key} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '9px 12px', borderRadius: 8, border: '1.5px solid #E2E8F0',
                background: cardBg, cursor: 'pointer', fontFamily: cfg.font,
                fontSize: 13, fontWeight: 500, color: '#0F172A', textAlign: dir === 'rtl' ? 'right' : 'left',
                direction: dir,
              }}>
                <div style={{ width: 28, height: 28, borderRadius: 7, background: a.color + '18', color: a.color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {a.icon}
                </div>
                {t(a.key)}
              </button>
            ))}
          </div>
        </div>
        <div style={{ ...dashStyles.card, background: cardBg }}>
          <div style={{ ...dashStyles.cardTitle, color: fg1 }}>{t('activity_title')}</div>
          <div style={{ marginTop: 14 }}>
            {ACTIVITY_KEYS.map((a, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: i < ACTIVITY_KEYS.length - 1 ? '1px solid #F1F5F9' : 'none' }}>
                <div style={{ width: 28, height: 28, borderRadius: 7, background: a.color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {a.icon}
                </div>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 500, color: fg1 }}>{t(a.actKey)}</div>
                  <div style={{ fontSize: 11, color: fg2, marginTop: 1 }}>
                    {a.timeVal ? `${a.timeVal} ${t(a.timeKey)}` : t(a.timeKey)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { DashboardView });
