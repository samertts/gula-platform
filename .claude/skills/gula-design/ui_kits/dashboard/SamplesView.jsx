// SamplesView.jsx — Samples screen (multilingual)
const { useState: useStateS, useContext: useCtxS } = React;

const SAMPLES = [
  { id: 'S-0041', patient: 'Ahmed Al-Rashidi', test: 'CBC — Blood', statusKey: 'completed', date: 'Apr 28, 2026', priorityKey: 'priority_normal' },
  { id: 'S-0042', patient: 'Sara Khalil', test: 'Lipid Panel', statusKey: 'pending', date: 'Apr 28, 2026', priorityKey: 'priority_high' },
  { id: 'S-0043', patient: 'Omar Hassan', test: 'Urine Culture', statusKey: 'processing', date: 'Apr 27, 2026', priorityKey: 'priority_normal' },
  { id: 'S-0044', patient: 'Fatima Al-Amiri', test: 'Thyroid Panel', statusKey: 'failed', date: 'Apr 27, 2026', priorityKey: 'priority_high' },
  { id: 'S-0045', patient: 'Kareem Saleh', test: 'HbA1c', statusKey: 'completed', date: 'Apr 26, 2026', priorityKey: 'priority_normal' },
];

const STATUS_STYLES = {
  completed:  { bg: '#DCFCE7', color: '#15803D', dot: '#10B981' },
  pending:    { bg: '#FEF9C3', color: '#A16207', dot: '#F59E0B' },
  processing: { bg: '#EFF6FF', color: '#1D4ED8', dot: '#2563EB' },
  failed:     { bg: '#FEE2E2', color: '#B91C1C', dot: '#EF4444' },
};

const sampStyles = {
  page: { padding: 28, overflowY: 'auto', flex: 1 },
  header: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20 },
  title: { fontSize: 18, fontWeight: 700, color: '#0F172A' },
  sub: { fontSize: 12, color: '#94A3B8', marginTop: 2 },
  btn: {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    padding: '8px 16px', borderRadius: 8, border: 'none',
    background: '#2563EB', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
  },
  filters: { display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' },
  filterBtn: (active) => ({
    padding: '5px 14px', borderRadius: 7, border: '1.5px solid',
    borderColor: active ? '#2563EB' : '#E2E8F0',
    background: active ? '#EFF6FF' : '#fff',
    color: active ? '#2563EB' : '#64748B',
    fontSize: 12, fontWeight: 500, cursor: 'pointer',
  }),
  table: {
    background: '#fff', borderRadius: 12, overflow: 'hidden',
    boxShadow: '0 1px 3px rgb(0 0 0/.07)', width: '100%', borderCollapse: 'collapse',
  },
  th: {
    padding: '10px 16px', fontSize: 11, fontWeight: 600,
    color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.06em',
    background: '#F8FAFC', borderBottom: '1.5px solid #E2E8F0',
  },
  td: { padding: '13px 16px', fontSize: 13, color: '#0F172A', borderBottom: '1px solid #F1F5F9' },
};

const ALL_FILTERS = ['all', 'completed', 'pending', 'processing', 'failed'];

function SamplesView({ dark }) {
  const { t, lang } = useCtxS(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';
  const [filter, setFilter] = useStateS('all');
  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';

  const shown = filter === 'all' ? SAMPLES : SAMPLES.filter(s => s.statusKey === filter);
  const thStyle = { ...sampStyles.th, textAlign: isRtl ? 'right' : 'left' };
  const tdStyle = { ...sampStyles.td, textAlign: isRtl ? 'right' : 'left' };

  return (
    <div style={{ ...sampStyles.page, fontFamily: cfg.font, direction: dir, background: bg }}>
      <div style={sampStyles.header}>
        <div>
          <div style={{ ...sampStyles.title, color: fg1 }}>{t('samp_title')}</div>
          <div style={{ ...sampStyles.sub, color: fg2 }}>{t('samp_sub')}</div>
        </div>
        <button style={{ ...sampStyles.btn, fontFamily: cfg.font }}>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          {t('samp_add')}
        </button>
      </div>

      <div style={sampStyles.filters}>
        {ALL_FILTERS.map(f => (
          <button key={f} style={{ ...sampStyles.filterBtn(filter === f), fontFamily: cfg.font }} onClick={() => setFilter(f)}>
            {t(f)}
          </button>
        ))}
      </div>

      <table style={{ ...sampStyles.table, background: surface }}>
        <thead>
          <tr>
            <th style={thStyle}>{t('col_id')}</th>
            <th style={thStyle}>{t('col_patient')}</th>
            <th style={thStyle}>{t('col_test')}</th>
            <th style={thStyle}>{t('col_priority')}</th>
            <th style={thStyle}>{t('col_status')}</th>
            <th style={thStyle}>{t('col_date')}</th>
            <th style={thStyle}></th>
          </tr>
        </thead>
        <tbody>
          {shown.map(s => {
            const sc = STATUS_STYLES[s.statusKey];
            return (
              <tr key={s.id}>
                <td style={{ ...tdStyle, color: '#2563EB', fontWeight: 600 }}>#{s.id}</td>
                <td style={tdStyle}>{s.patient}</td>
                <td style={tdStyle}>{s.test}</td>
                <td style={tdStyle}>
                  <span style={{
                    display: 'inline-block', padding: '2px 8px', borderRadius: 9999,
                    fontSize: 11, fontWeight: 600,
                    background: s.priorityKey === 'priority_high' ? '#FEE2E2' : '#F1F5F9',
                    color: s.priorityKey === 'priority_high' ? '#B91C1C' : '#64748B',
                  }}>{t(s.priorityKey)}</span>
                </td>
                <td style={tdStyle}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: sc.bg, color: sc.color }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: sc.dot, flexShrink: 0 }}></span>
                    {t(s.statusKey)}
                  </span>
                </td>
                <td style={{ ...tdStyle, color: '#64748B', fontSize: 12 }}>{s.date}</td>
                <td style={tdStyle}>
                  <button style={{ background: 'none', border: 'none', fontSize: 12, fontWeight: 500, color: '#2563EB', cursor: 'pointer', fontFamily: cfg.font }}>
                    {s.statusKey === 'failed' ? t('act_retry') : t('act_view')}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

Object.assign(window, { SamplesView });
