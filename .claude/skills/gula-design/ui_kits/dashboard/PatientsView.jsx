// PatientsView.jsx — Patients screen (multilingual)
const { useState: useStateP, useContext: useCtxP } = React;

const PATIENTS = [
  { id: 'P-001', name: 'Ahmed Al-Rashidi', nid: '19841204012345', phone: '+964 770 123 4567', statusKey: 'status_active', tests: 8 },
  { id: 'P-002', name: 'Sara Khalil Mohammed', nid: '19950615078901', phone: '+964 771 234 5678', statusKey: 'status_active', tests: 3 },
  { id: 'P-003', name: 'Omar Hassan Al-Jabouri', nid: '19780320034567', phone: '+964 772 345 6789', statusKey: 'status_inactive', tests: 14 },
  { id: 'P-004', name: 'Fatima Al-Amiri', nid: '20010901056789', phone: '+964 773 456 7890', statusKey: 'status_active', tests: 2 },
  { id: 'P-005', name: 'Kareem Saleh', nid: '19900712089012', phone: '+964 774 567 8901', statusKey: 'status_active', tests: 6 },
];

const patStyles = {
  page: { padding: 28, overflowY: 'auto', flex: 1 },
  header: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20 },
  title: { fontSize: 18, fontWeight: 700, color: '#0F172A' },
  sub: { fontSize: 12, color: '#94A3B8', marginTop: 2 },
  btn: {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    padding: '8px 16px', borderRadius: 8, border: 'none',
    background: '#2563EB', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
  },
  searchWrap: { marginBottom: 16 },
  searchInput: {
    width: '100%', padding: '8px 12px', border: '1.5px solid #E2E8F0', borderRadius: 8,
    fontSize: 13, color: '#0F172A', outline: 'none', background: '#fff',
  },
  table: {
    background: '#fff', borderRadius: 12, overflow: 'hidden',
    boxShadow: '0 1px 3px rgb(0 0 0/.07)', width: '100%', borderCollapse: 'collapse',
  },
  th: {
    padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 600,
    color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.06em',
    background: '#F8FAFC', borderBottom: '1.5px solid #E2E8F0',
  },
  thRtl: { textAlign: 'right' },
  td: { padding: '12px 16px', fontSize: 13, color: '#0F172A', borderBottom: '1px solid #F1F5F9' },
  tdRtl: { textAlign: 'right' },
  actionBtn: {
    background: 'none', border: 'none', fontSize: 12, fontWeight: 500,
    color: '#2563EB', cursor: 'pointer', padding: '0 6px',
  },
};

function PatientsView({ dark }) {
  const { t, lang } = useCtxP(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';
  const [search, setSearch] = useStateP('');
  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';

  const filtered = PATIENTS.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) || p.nid.includes(search)
  );

  const thStyle = { ...patStyles.th, ...(isRtl ? patStyles.thRtl : {}) };
  const tdStyle = { ...patStyles.td, ...(isRtl ? patStyles.tdRtl : {}) };

  return (
    <div style={{ ...patStyles.page, fontFamily: cfg.font, direction: dir, background: bg }}>
      <div style={patStyles.header}>
        <div>
          <div style={{ ...patStyles.title, color: fg1 }}>{t('pat_title')}</div>
          <div style={{ ...patStyles.sub, color: fg2 }}>{PATIENTS.length} {t('pat_sub')}</div>
        </div>
        <button style={{ ...patStyles.btn, fontFamily: cfg.font }}>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          {t('pat_register')}
        </button>
      </div>

      <div style={patStyles.searchWrap}>
        <input
          style={{ ...patStyles.searchInput, fontFamily: cfg.font, direction: dir }}
          placeholder={t('pat_search')}
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <table style={{ ...patStyles.table, background: surface }}>
        <thead>
          <tr>
            <th style={thStyle}>{t('col_id')}</th>
            <th style={thStyle}>{t('col_name')}</th>
            <th style={thStyle}>{t('col_nid')}</th>
            <th style={thStyle}>{t('col_phone')}</th>
            <th style={thStyle}>{t('col_status')}</th>
            <th style={thStyle}>{t('col_tests')}</th>
            <th style={thStyle}></th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((p, i) => (
            <tr key={p.id} style={{ background: i % 2 === 0 ? '#fff' : '#FAFBFC' }}>
              <td style={{ ...tdStyle, color: '#2563EB', fontWeight: 600 }}>{p.id}</td>
              <td style={tdStyle}>{p.name}</td>
              <td style={{ ...tdStyle, fontFamily: 'monospace', fontSize: 12, color: '#64748B' }}>{p.nid}</td>
              <td style={{ ...tdStyle, color: '#64748B', fontSize: 12 }}>{p.phone}</td>
              <td style={tdStyle}>
                <span style={{
                  display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 9px',
                  borderRadius: 9999, fontSize: 11, fontWeight: 600,
                  background: p.statusKey === 'status_active' ? '#DCFCE7' : '#F1F5F9',
                  color: p.statusKey === 'status_active' ? '#15803D' : '#64748B',
                }}>
                  <span style={{ width: 5, height: 5, borderRadius: '50%', background: p.statusKey === 'status_active' ? '#10B981' : '#94A3B8' }}></span>
                  {t(p.statusKey)}
                </span>
              </td>
              <td style={{ ...tdStyle, fontWeight: 600 }}>{p.tests}</td>
              <td style={tdStyle}>
                <button style={{ ...patStyles.actionBtn, fontFamily: cfg.font }}>{t('act_view')}</button>
                <button style={{ ...patStyles.actionBtn, fontFamily: cfg.font, color: '#64748B' }}>{t('act_edit')}</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

Object.assign(window, { PatientsView });
