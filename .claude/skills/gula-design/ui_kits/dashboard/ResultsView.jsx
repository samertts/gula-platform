// ResultsView.jsx — Lab results with clinical flag logic (multilingual)
const { useContext: useCtxR, useState: useStateR } = React;

// Medical-grade mock data with reference ranges
const RESULTS = [
  { id: 'R-0101', patient: 'أحمد حسن', patient_en: 'Ahmed Hassan', test: 'Hemoglobin', value: 9.2, unit: 'g/dL', ref: '13.5–17.5', refMin: 13.5, refMax: 17.5, statusKey: 'failed', date: 'Apr 28, 2026', doctor: 'Dr. Samer' },
  { id: 'R-0102', patient: 'سارة خالد', patient_en: 'Sara Khalid', test: 'LDL Cholesterol', value: 98, unit: 'mg/dL', ref: '<100', refMin: 0, refMax: 100, statusKey: 'completed', date: 'Apr 28, 2026', doctor: 'Dr. Layla' },
  { id: 'R-0103', patient: 'عمر جاسم', patient_en: 'Omar Jasim', test: 'WBC Count', value: 12.8, unit: '×10³/µL', ref: '4.5–11.0', refMin: 4.5, refMax: 11.0, statusKey: 'failed', date: 'Apr 27, 2026', doctor: 'Dr. Samer' },
  { id: 'R-0104', patient: 'فاطمة علي', patient_en: 'Fatima Ali', test: 'TSH', value: 2.1, unit: 'mIU/L', ref: '0.4–4.0', refMin: 0.4, refMax: 4.0, statusKey: 'completed', date: 'Apr 27, 2026', doctor: 'Dr. Hassan' },
  { id: 'R-0105', patient: 'كريم صالح', patient_en: 'Kareem Saleh', test: 'HbA1c', value: 8.4, unit: '%', ref: '<5.7', refMin: 0, refMax: 5.7, statusKey: 'failed', date: 'Apr 26, 2026', doctor: 'Dr. Layla' },
  { id: 'R-0106', patient: 'نور أحمد', patient_en: 'Nour Ahmed', test: 'Platelets', value: 245, unit: '×10³/µL', ref: '150–400', refMin: 150, refMax: 400, statusKey: 'completed', date: 'Apr 26, 2026', doctor: 'Dr. Samer' },
];

// Clinical logic: determine if value is abnormal
const isAbnormal = (r) => r.value < r.refMin || r.value > r.refMax;
const isHigh = (r) => r.value > r.refMax;
const isLow = (r) => r.value < r.refMin;

const FLAG = {
  high: { label: '↑ H', bg: '#FEE2E2', color: '#B91C1C' },
  low:  { label: '↓ L', bg: '#FEF9C3', color: '#A16207' },
  ok:   { label: '✓',   bg: '#DCFCE7', color: '#15803D' },
};

const STATUS_S = {
  completed: { bg: '#DCFCE7', color: '#15803D', dot: '#10B981' },
  pending:   { bg: '#FEF9C3', color: '#A16207', dot: '#F59E0B' },
  failed:    { bg: '#FEE2E2', color: '#B91C1C', dot: '#EF4444' },
};

function ResultsView({ dark }) {
  const { t, lang } = useCtxR(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';
  const [filter, setFilter] = useStateR('all');

  const surface = dark ? '#1E293B' : '#fff';
  const bg      = dark ? '#0F172A' : '#F8FAFC';
  const fg1     = dark ? '#F1F5F9' : '#0F172A';
  const fg2     = dark ? '#94A3B8' : '#64748B';
  const border  = dark ? '#334155' : '#E2E8F0';
  const rowAlt  = dark ? '#1A2744' : '#FAFBFC';

  const shown = filter === 'all' ? RESULTS : filter === 'abnormal'
    ? RESULTS.filter(r => isAbnormal(r))
    : RESULTS.filter(r => r.statusKey === filter);

  const abnormalCount = RESULTS.filter(r => isAbnormal(r)).length;

  return (
    <div style={{ padding: 28, overflowY: 'auto', flex: 1, fontFamily: cfg.font, direction: dir, background: bg }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: fg1 }}>{t('nav_results')}</div>
          <div style={{ fontSize: 12, color: fg2, marginTop: 2 }}>{RESULTS.length} results — {abnormalCount} abnormal flags</div>
        </div>
        <button style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 8, border: 'none', background: '#2563EB', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: cfg.font }}>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {t('act_download')}
        </button>
      </div>

      {/* Critical alert banner if any abnormals */}
      {abnormalCount > 0 && (
        <div style={{ background: '#FEF2F2', border: '1.5px solid #FECACA', borderRadius: 10, padding: '10px 14px', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 10 }}>
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span style={{ fontSize: 12, fontWeight: 600, color: '#B91C1C' }}>{abnormalCount} critical results require immediate review</span>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        {[['all', 'All'], ['abnormal', `⚑ Abnormal (${abnormalCount})`], ['completed', t('completed')], ['pending', t('pending')], ['failed', t('failed')]].map(([f, label]) => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '5px 12px', borderRadius: 7, border: '1.5px solid',
            borderColor: filter === f ? '#2563EB' : border,
            background: filter === f ? (f === 'abnormal' ? '#FEE2E2' : '#EFF6FF') : surface,
            color: filter === f ? (f === 'abnormal' ? '#B91C1C' : '#2563EB') : fg2,
            fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: cfg.font,
          }}>{label}</button>
        ))}
      </div>

      <div style={{ background: surface, borderRadius: 12, overflow: 'hidden', boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)', border: dark ? `1px solid ${border}` : 'none' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: dark ? '#1A2744' : '#F8FAFC', borderBottom: `1.5px solid ${border}` }}>
              {['ID', t('col_patient'), 'Test', 'Result', 'Flag', 'Reference', t('col_status'), t('col_date')].map((h, i) => (
                <th key={i} style={{ padding: '10px 14px', textAlign: isRtl ? 'right' : 'left', fontSize: 10, fontWeight: 600, color: fg2, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shown.map((r, i) => {
              const sc   = STATUS_S[r.statusKey];
              const abn  = isAbnormal(r);
              const flag = abn ? (isHigh(r) ? FLAG.high : FLAG.low) : FLAG.ok;
              const td   = { padding: '12px 14px', fontSize: 13, color: fg1, borderBottom: `1px solid ${border}`, textAlign: isRtl ? 'right' : 'left', background: abn && i % 2 === 0 ? (dark ? '#2D1515' : '#FFF9F9') : (i % 2 === 0 ? surface : rowAlt) };
              return (
                <tr key={r.id}>
                  <td style={{ ...td, color: '#2563EB', fontWeight: 600, fontSize: 11 }}>{r.id}</td>
                  <td style={td}>{lang === 'ar' || lang === 'ku' ? r.patient : r.patient_en}</td>
                  <td style={{ ...td, color: fg2, fontSize: 12 }}>{r.test}</td>
                  <td style={{ ...td, fontWeight: 700, color: abn ? '#EF4444' : '#10B981', fontFamily: 'monospace' }}>{r.value} <span style={{ fontSize: 10, fontWeight: 400, color: fg2 }}>{r.unit}</span></td>
                  <td style={td}>
                    <span style={{ display: 'inline-block', padding: '2px 7px', borderRadius: 5, fontSize: 11, fontWeight: 700, background: flag.bg, color: flag.color }}>{flag.label}</span>
                  </td>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: 11, color: fg2 }}>{r.ref}</td>
                  <td style={td}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 9px', borderRadius: 9999, fontSize: 10, fontWeight: 600, background: sc.bg, color: sc.color }}>
                      <span style={{ width: 5, height: 5, borderRadius: '50%', background: sc.dot }}></span>
                      {t(r.statusKey)}
                    </span>
                  </td>
                  <td style={{ ...td, color: fg2, fontSize: 11 }}>{r.date}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

Object.assign(window, { ResultsView });
