// DoctorDashView.jsx — Doctor dashboard with alerts + pending approvals (multilingual)
const { useContext: useCtxDD } = React;

const CRITICAL_ALERTS = [
  { id: 'R-0101', patient_ar: 'أحمد حسن', patient_en: 'Ahmed Hassan', test: 'Hemoglobin', value: '9.2 g/dL', flag: 'Critical Low', time: '10 min ago' },
  { id: 'R-0103', patient_ar: 'عمر جاسم', patient_en: 'Omar Jasim', test: 'WBC Count', value: '12.8 ×10³/µL', flag: 'Critical High', time: '25 min ago' },
  { id: 'R-0105', patient_ar: 'كريم صالح', patient_en: 'Kareem Saleh', test: 'HbA1c', value: '8.4%', flag: 'High', time: '1 hr ago' },
];

const PENDING = [
  { id: 'R-0102', patient_ar: 'سارة خالد', patient_en: 'Sara Khalid', test: 'Lipid Panel', time: 'Awaiting 2h' },
  { id: 'R-0104', patient_ar: 'فاطمة علي', patient_en: 'Fatima Ali', test: 'TSH', time: 'Awaiting 4h' },
  { id: 'R-0106', patient_ar: 'نور أحمد', patient_en: 'Nour Ahmed', test: 'Platelets', time: 'Awaiting 6h' },
];

function DoctorDashView({ dark }) {
  const { t, lang } = useCtxDD(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;

  const bg      = dark ? '#0F172A' : '#F8FAFC';
  const surface = dark ? '#1E293B' : '#fff';
  const fg1     = dark ? '#F1F5F9' : '#0F172A';
  const fg2     = dark ? '#94A3B8' : '#64748B';
  const border  = dark ? '#334155' : '#E2E8F0';
  const isRtl   = dir === 'rtl';

  const patName = (item) => (lang === 'ar' || lang === 'ku' || lang === 'sy') ? item.patient_ar : item.patient_en;

  return (
    <div style={{ padding: 28, overflowY: 'auto', flex: 1, fontFamily: cfg.font, direction: dir, background: bg }}>
      <div style={{ fontSize: 18, fontWeight: 700, color: fg1, marginBottom: 4 }}>{t('nav_doctor_dash')}</div>
      <div style={{ fontSize: 12, color: fg2, marginBottom: 20 }}>Dr. Samer Al-Rashidi · April 28, 2026</div>

      {/* KPI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 22 }}>
        {[
          { label: 'My Patients', value: '34', color: '#3B82F6' },
          { label: 'Critical Alerts', value: CRITICAL_ALERTS.length.toString(), color: '#EF4444' },
          { label: 'Pending Review', value: PENDING.length.toString(), color: '#F59E0B' },
          { label: 'Approved Today', value: '12', color: '#10B981' },
        ].map(s => (
          <div key={s.label} style={{ background: surface, borderRadius: 11, padding: '16px 18px', border: dark ? `1px solid ${border}` : 'none', boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)' }}>
            <div style={{ fontSize: 26, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 11, color: fg2, marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Critical alerts */}
        <div style={{ background: surface, borderRadius: 12, padding: 18, border: dark ? `1px solid ${border}` : `1.5px solid #FECACA`, boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#EF4444' }}>Critical Alerts</div>
            <span style={{ marginLeft: 'auto', background: '#FEE2E2', color: '#B91C1C', fontSize: 10, fontWeight: 700, padding: '1px 7px', borderRadius: 9999 }}>{CRITICAL_ALERTS.length}</span>
          </div>
          {CRITICAL_ALERTS.map((a, i) => (
            <div key={a.id} style={{ padding: '10px 0', borderBottom: i < CRITICAL_ALERTS.length - 1 ? `1px solid ${border}` : 'none', display: 'flex', gap: 10, alignItems: 'center' }}>
              <div style={{ width: 36, height: 36, borderRadius: 9, background: '#FEE2E2', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: fg1 }}>{patName(a)}</div>
                <div style={{ fontSize: 11, color: fg2 }}>{a.test} — <strong style={{ color: '#EF4444' }}>{a.value}</strong></div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                <span style={{ fontSize: 9, color: fg2 }}>{a.time}</span>
                <button style={{ padding: '3px 10px', borderRadius: 6, border: 'none', background: '#EF4444', color: '#fff', fontSize: 10, fontWeight: 600, cursor: 'pointer' }}>Review</button>
              </div>
            </div>
          ))}
        </div>

        {/* Pending approvals */}
        <div style={{ background: surface, borderRadius: 12, padding: 18, border: dark ? `1px solid ${border}` : 'none', boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <div style={{ fontSize: 13, fontWeight: 600, color: fg1 }}>Pending Approval</div>
            <span style={{ marginLeft: 'auto', background: '#FEF9C3', color: '#A16207', fontSize: 10, fontWeight: 700, padding: '1px 7px', borderRadius: 9999 }}>{PENDING.length}</span>
          </div>
          {PENDING.map((p, i) => (
            <div key={p.id} style={{ padding: '10px 0', borderBottom: i < PENDING.length - 1 ? `1px solid ${border}` : 'none', display: 'flex', gap: 10, alignItems: 'center' }}>
              <div style={{ width: 36, height: 36, borderRadius: 9, background: '#FEF9C3', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: fg1 }}>{patName(p)}</div>
                <div style={{ fontSize: 11, color: fg2 }}>{p.test} · {p.time}</div>
              </div>
              <div style={{ display: 'flex', gap: 5 }}>
                <button style={{ padding: '3px 10px', borderRadius: 6, border: 'none', background: '#10B981', color: '#fff', fontSize: 10, fontWeight: 600, cursor: 'pointer' }}>✓</button>
                <button style={{ padding: '3px 10px', borderRadius: 6, border: `1.5px solid ${border}`, background: 'transparent', color: fg2, fontSize: 10, fontWeight: 600, cursor: 'pointer' }}>✕</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { DoctorDashView });
