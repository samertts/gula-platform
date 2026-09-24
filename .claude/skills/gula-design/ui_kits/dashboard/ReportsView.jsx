// ReportsView.jsx — Reports screen (multilingual)
const { useContext: useCtxRep } = React;

const REPORTS_DATA = [
  { id: 'RPT-001', title: 'Monthly Lab Summary — April 2026', type: 'Summary', generated: 'Apr 28, 2026', size: '2.4 MB', format: 'PDF' },
  { id: 'RPT-002', title: 'Critical Results Alert Report', type: 'Critical', generated: 'Apr 27, 2026', size: '1.1 MB', format: 'PDF' },
  { id: 'RPT-003', title: 'Patient Billing Statement — Q1', type: 'Billing', generated: 'Apr 25, 2026', size: '3.8 MB', format: 'Excel' },
  { id: 'RPT-004', title: 'Sample Turnaround Time Analysis', type: 'Analytics', generated: 'Apr 22, 2026', size: '0.9 MB', format: 'PDF' },
  { id: 'RPT-005', title: 'Equipment Quality Control Log', type: 'QC', generated: 'Apr 20, 2026', size: '1.6 MB', format: 'PDF' },
];

const TYPE_COLORS = {
  Summary:   { bg: '#EFF6FF', color: '#1D4ED8' },
  Critical:  { bg: '#FEE2E2', color: '#B91C1C' },
  Billing:   { bg: '#FEF9C3', color: '#A16207' },
  Analytics: { bg: '#F3E8FF', color: '#7E22CE' },
  QC:        { bg: '#DCFCE7', color: '#15803D' },
};

function ReportsView({ dark }) {
  const { t, lang } = useCtxRep(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';

  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';

  return (
    <div style={{ padding: 28, overflowY: 'auto', flex: 1, fontFamily: cfg.font, direction: dir, background: bg }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: fg1 }}>{t('nav_reports')}</div>
          <div style={{ fontSize: 12, color: fg2, marginTop: 2 }}>{REPORTS_DATA.length} reports available</div>
        </div>
        <button style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 8, border: 'none', background: '#2563EB', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: cfg.font }}>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          {t('act_report')}
        </button>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginBottom: 24 }}>
        {[
          { label: 'Total Reports', value: '148', icon: '📊', color: '#3B82F6' },
          { label: 'This Month', value: '23', icon: '📅', color: '#10B981' },
          { label: 'Pending Review', value: '5', icon: '⏳', color: '#F59E0B' },
        ].map(s => (
          <div key={s.label} style={{ background: surface, borderRadius: 12, padding: 18, boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)', border: dark ? `1px solid ${border}` : 'none', display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: s.color + '18', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>{s.icon}</div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, color: fg1 }}>{s.value}</div>
              <div style={{ fontSize: 11, color: fg2 }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Reports list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {REPORTS_DATA.map(r => {
          const tc = TYPE_COLORS[r.type];
          return (
            <div key={r.id} style={{ background: surface, borderRadius: 12, padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 16, boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.06)', border: dark ? `1px solid ${border}` : 'none' }}>
              <div style={{ width: 40, height: 40, borderRadius: 9, background: r.format === 'PDF' ? '#FEE2E2' : '#DCFCE7', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke={r.format === 'PDF' ? '#EF4444' : '#10B981'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: fg1, marginBottom: 3 }}>{r.title}</div>
                <div style={{ fontSize: 11, color: fg2 }}>{r.id} · {r.generated} · {r.size}</div>
              </div>
              <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: tc.bg, color: tc.color, flexShrink: 0 }}>{r.type}</span>
              <button style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px', borderRadius: 7, border: `1.5px solid ${border}`, background: 'transparent', color: fg2, fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: cfg.font, flexShrink: 0 }}>
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                {t('act_download')}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

Object.assign(window, { ReportsView });
