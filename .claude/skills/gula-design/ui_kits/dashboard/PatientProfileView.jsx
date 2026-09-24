// PatientProfileView.jsx — Patient timeline + history (multilingual)
const { useContext: useCtxPP } = React;

const PATIENT = {
  id: 'P-001', name_ar: 'أحمد حسن محمد', name_en: 'Ahmed Hassan Mohammed',
  nid: '19841204012345', dob: '1984-12-04', age: 41, gender_ar: 'ذكر', gender_en: 'Male',
  phone: '+964 770 123 4567', blood: 'A+',
  conditions: ['Type 2 Diabetes', 'Hypertension'],
  allergies: ['Penicillin'],
};

const TIMELINE = [
  { date: 'Apr 28, 2026', test: 'Hemoglobin', value: '9.2 g/dL', flag: 'low', doctor: 'Dr. Samer', status: 'failed' },
  { date: 'Mar 15, 2026', test: 'HbA1c',      value: '8.1%',     flag: 'high', doctor: 'Dr. Layla', status: 'failed' },
  { date: 'Feb 10, 2026', test: 'CBC Panel',   value: 'Normal',   flag: 'ok',  doctor: 'Dr. Samer', status: 'completed' },
  { date: 'Jan 05, 2026', test: 'Lipid Panel', value: 'LDL 112',  flag: 'high', doctor: 'Dr. Hassan', status: 'failed' },
  { date: 'Dec 20, 2025', test: 'TSH',         value: '2.4 mIU/L',flag: 'ok', doctor: 'Dr. Layla', status: 'completed' },
];

const FLAG_COLORS = {
  high: { bg: '#FEE2E2', color: '#B91C1C', label: '↑ High' },
  low:  { bg: '#FEF9C3', color: '#A16207', label: '↓ Low' },
  ok:   { bg: '#DCFCE7', color: '#15803D', label: '✓ Normal' },
};

function PatientProfileView({ dark }) {
  const { t, lang } = useCtxPP(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';

  const bg      = dark ? '#0F172A' : '#F8FAFC';
  const surface = dark ? '#1E293B' : '#fff';
  const fg1     = dark ? '#F1F5F9' : '#0F172A';
  const fg2     = dark ? '#94A3B8' : '#64748B';
  const border  = dark ? '#334155' : '#E2E8F0';

  const name = (lang === 'ar' || lang === 'ku' || lang === 'sy') ? PATIENT.name_ar : PATIENT.name_en;
  const gender = (lang === 'ar' || lang === 'ku' || lang === 'sy') ? PATIENT.gender_ar : PATIENT.gender_en;

  return (
    <div style={{ padding: 28, overflowY: 'auto', flex: 1, fontFamily: cfg.font, direction: dir, background: bg }}>
      <div style={{ fontSize: 18, fontWeight: 700, color: fg1, marginBottom: 20 }}>{t('nav_patient_profile')}</div>

      {/* Profile header */}
      <div style={{ background: surface, borderRadius: 14, padding: 22, marginBottom: 18, boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)', border: dark ? `1px solid ${border}` : 'none', display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'linear-gradient(135deg,#2563EB,#8B5CF6)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 22, flexShrink: 0 }}>
          {name[0]}
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: fg1 }}>{name}</div>
          <div style={{ fontSize: 12, color: fg2, marginTop: 2 }}>{PATIENT.id} · {gender} · {PATIENT.age} yrs · {PATIENT.blood}</div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
            {PATIENT.conditions.map(c => (
              <span key={c} style={{ padding: '2px 9px', borderRadius: 6, background: '#FEF9C3', color: '#A16207', fontSize: 11, fontWeight: 600 }}>{c}</span>
            ))}
            {PATIENT.allergies.map(a => (
              <span key={a} style={{ padding: '2px 9px', borderRadius: 6, background: '#FEE2E2', color: '#B91C1C', fontSize: 11, fontWeight: 600 }}>⚠ {a}</span>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: fg2 }}>
          <div>📞 {PATIENT.phone}</div>
          <div>🪪 {PATIENT.nid}</div>
          <div>🎂 {PATIENT.dob}</div>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 18 }}>
        {[
          { label: 'Total Tests', value: TIMELINE.length, color: '#3B82F6' },
          { label: 'Abnormal', value: TIMELINE.filter(t => t.flag !== 'ok').length, color: '#EF4444' },
          { label: 'Normal', value: TIMELINE.filter(t => t.flag === 'ok').length, color: '#10B981' },
          { label: 'Last Visit', value: 'Apr 28', color: '#8B5CF6' },
        ].map(s => (
          <div key={s.label} style={{ background: surface, borderRadius: 10, padding: '14px 16px', border: dark ? `1px solid ${border}` : 'none', boxShadow: dark ? 'none' : '0 1px 2px rgb(0 0 0/.06)' }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 11, color: fg2, marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Lab timeline */}
      <div style={{ background: surface, borderRadius: 14, padding: 20, border: dark ? `1px solid ${border}` : 'none', boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)' }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: fg1, marginBottom: 16 }}>Lab Results Timeline</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {TIMELINE.map((item, i) => {
            const fc = FLAG_COLORS[item.flag];
            return (
              <div key={i} style={{ display: 'flex', gap: 14, padding: '12px 0', borderBottom: i < TIMELINE.length - 1 ? `1px solid ${border}` : 'none', alignItems: 'center' }}>
                <div style={{ flexShrink: 0, textAlign: 'center', width: 70 }}>
                  <div style={{ fontSize: 10, color: fg2, fontWeight: 500 }}>{item.date}</div>
                </div>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: item.flag === 'ok' ? '#10B981' : '#EF4444', flexShrink: 0, border: `2px solid ${bg}`, boxShadow: `0 0 0 2px ${item.flag === 'ok' ? '#10B981' : '#EF4444'}` }}></div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: fg1 }}>{item.test}</div>
                  <div style={{ fontSize: 11, color: fg2 }}>{item.doctor}</div>
                </div>
                <div style={{ fontSize: 13, fontWeight: 700, color: fg1 }}>{item.value}</div>
                <span style={{ padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 700, background: fc.bg, color: fc.color }}>{fc.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PatientProfileView });
