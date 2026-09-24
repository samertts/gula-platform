// LabQueueView.jsx — Incoming samples queue with processing states (multilingual)
const { useContext: useCtxLQ, useState: useStateLQ } = React;

const QUEUE = [
  { id: 'Q-001', patient_ar: 'محمد علي',  patient_en: 'Mohammed Ali',  test: 'CBC Panel',     priority: 'stat',   received: '08:12', state: 'processing', eta: '5 min' },
  { id: 'Q-002', patient_ar: 'زينب حسن', patient_en: 'Zainab Hassan', test: 'Lipid Panel',   priority: 'routine',received: '08:45', state: 'waiting',    eta: '20 min' },
  { id: 'Q-003', patient_ar: 'حسن كريم', patient_en: 'Hassan Kareem', test: 'Blood Culture', priority: 'stat',   received: '09:01', state: 'processing', eta: '8 min' },
  { id: 'Q-004', patient_ar: 'ليلى أحمد', patient_en: 'Layla Ahmed',  test: 'Thyroid Panel', priority: 'routine',received: '09:15', state: 'received',   eta: '35 min' },
  { id: 'Q-005', patient_ar: 'عادل سالم', patient_en: 'Adel Salem',   test: 'Urine R&M',     priority: 'routine',received: '09:30', state: 'received',   eta: '40 min' },
  { id: 'Q-006', patient_ar: 'ريم جاسم', patient_en: 'Reem Jasim',   test: 'HbA1c',         priority: 'urgent', received: '09:42', state: 'waiting',    eta: '15 min' },
];

const STATE_MAP = {
  received:   { label: 'Received',   bg: '#EFF6FF', color: '#1D4ED8', dot: '#2563EB' },
  waiting:    { label: 'Waiting',    bg: '#FEF9C3', color: '#A16207', dot: '#F59E0B' },
  processing: { label: 'Processing', bg: '#F3E8FF', color: '#7E22CE', dot: '#8B5CF6', animate: true },
};

const PRIORITY_MAP = {
  stat:    { label: 'STAT',    bg: '#FEE2E2', color: '#B91C1C' },
  urgent:  { label: 'URGENT', bg: '#FEF9C3', color: '#A16207' },
  routine: { label: 'Routine', bg: '#F1F5F9', color: '#64748B' },
};

function LabQueueView({ dark }) {
  const { t, lang } = useCtxLQ(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;

  const bg      = dark ? '#0F172A' : '#F8FAFC';
  const surface = dark ? '#1E293B' : '#fff';
  const fg1     = dark ? '#F1F5F9' : '#0F172A';
  const fg2     = dark ? '#94A3B8' : '#64748B';
  const border  = dark ? '#334155' : '#E2E8F0';
  const isRtl   = dir === 'rtl';

  const statCount = QUEUE.filter(q => q.priority === 'stat').length;
  const procCount = QUEUE.filter(q => q.state === 'processing').length;
  const waitCount = QUEUE.filter(q => q.state === 'waiting').length;

  const patName = (item) => (lang === 'ar' || lang === 'ku' || lang === 'sy') ? item.patient_ar : item.patient_en;

  return (
    <div style={{ padding: 28, overflowY: 'auto', flex: 1, fontFamily: cfg.font, direction: dir, background: bg }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: fg1 }}>{t('nav_lab_queue')}</div>
          <div style={{ fontSize: 12, color: fg2, marginTop: 2 }}>{QUEUE.length} samples — {statCount} STAT</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 14px', borderRadius: 8, border: `1.5px solid ${border}`, background: surface, color: fg2, fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: cfg.font }}>
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Add Sample
          </button>
        </div>
      </div>

      {/* Summary pills */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {[
          { label: 'Processing', count: procCount, color: '#8B5CF6', bg: '#F3E8FF' },
          { label: 'Waiting', count: waitCount, color: '#F59E0B', bg: '#FEF9C3' },
          { label: 'STAT Priority', count: statCount, color: '#EF4444', bg: '#FEE2E2' },
          { label: 'Total Queue', count: QUEUE.length, color: '#3B82F6', bg: '#EFF6FF' },
        ].map(s => (
          <div key={s.label} style={{ background: surface, borderRadius: 10, padding: '12px 16px', border: dark ? `1px solid ${border}` : 'none', boxShadow: dark ? 'none' : '0 1px 2px rgb(0 0 0/.06)', display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: s.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700, color: s.color }}>{s.count}</div>
            <div style={{ fontSize: 11, color: fg2, fontWeight: 500 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Queue cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {QUEUE.map(q => {
          const sm = STATE_MAP[q.state];
          const pm = PRIORITY_MAP[q.priority];
          return (
            <div key={q.id} style={{
              background: surface, borderRadius: 12, padding: '14px 18px',
              display: 'flex', alignItems: 'center', gap: 14,
              boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.06)',
              border: q.priority === 'stat' ? '1.5px solid #FECACA' : (dark ? `1px solid ${border}` : 'none'),
            }}>
              {/* Queue number */}
              <div style={{ width: 40, height: 40, borderRadius: 10, background: sm.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: sm.dot }}></div>
              </div>

              {/* Info */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: fg1 }}>{patName(q)}</span>
                  <span style={{ padding: '1px 7px', borderRadius: 4, fontSize: 10, fontWeight: 700, background: pm.bg, color: pm.color }}>{pm.label}</span>
                </div>
                <div style={{ fontSize: 11, color: fg2 }}>{q.id} · {q.test} · Received {q.received}</div>
              </div>

              {/* ETA */}
              <div style={{ textAlign: 'center', flexShrink: 0 }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: fg1 }}>{q.eta}</div>
                <div style={{ fontSize: 9, color: fg2, textTransform: 'uppercase', letterSpacing: '0.06em' }}>ETA</div>
              </div>

              {/* Status */}
              <span style={{ padding: '4px 12px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: sm.bg, color: sm.color, flexShrink: 0 }}>
                {sm.label}
              </span>

              {/* Action */}
              <button style={{ padding: '6px 14px', borderRadius: 7, border: 'none', background: '#2563EB', color: '#fff', fontSize: 11, fontWeight: 600, cursor: 'pointer', flexShrink: 0, fontFamily: cfg.font }}>
                {t('act_view')}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

Object.assign(window, { LabQueueView });
