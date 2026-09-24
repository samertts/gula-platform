// BillingView.jsx — Billing screen (multilingual)
const { useContext: useCtxB } = React;

const INVOICES = [
  { id: 'INV-2026-041', patient: 'Ahmed Al-Rashidi', tests: ['CBC', 'Lipid Panel'], amount: 75000, currency: 'IQD', statusKey: 'completed', date: 'Apr 28, 2026' },
  { id: 'INV-2026-042', patient: 'Sara Khalil', tests: ['Thyroid Panel'], amount: 45000, currency: 'IQD', statusKey: 'pending', date: 'Apr 27, 2026' },
  { id: 'INV-2026-043', patient: 'Omar Hassan', tests: ['Urine Culture', 'HbA1c'], amount: 90000, currency: 'IQD', statusKey: 'completed', date: 'Apr 26, 2026' },
  { id: 'INV-2026-044', patient: 'Fatima Al-Amiri', tests: ['CBC', 'CMP'], amount: 60000, currency: 'IQD', statusKey: 'failed', date: 'Apr 25, 2026' },
  { id: 'INV-2026-045', patient: 'Kareem Saleh', tests: ['Testosterone'], amount: 35000, currency: 'IQD', statusKey: 'pending', date: 'Apr 24, 2026' },
];

const BILL_STATUS = {
  completed: { bg: '#DCFCE7', color: '#15803D', dot: '#10B981', label: 'Paid' },
  pending:   { bg: '#FEF9C3', color: '#A16207', dot: '#F59E0B', label: 'Unpaid' },
  failed:    { bg: '#FEE2E2', color: '#B91C1C', dot: '#EF4444', label: 'Overdue' },
};

function BillingView({ dark }) {
  const { t, lang } = useCtxB(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';

  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  const rowAlt = dark ? '#1A2744' : '#FAFBFC';

  const total = INVOICES.reduce((s, i) => s + i.amount, 0);
  const paid  = INVOICES.filter(i => i.statusKey === 'completed').reduce((s, i) => s + i.amount, 0);
  const unpaid = INVOICES.filter(i => i.statusKey !== 'completed').reduce((s, i) => s + i.amount, 0);

  return (
    <div style={{ padding: 28, overflowY: 'auto', flex: 1, fontFamily: cfg.font, direction: dir, background: bg }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: fg1 }}>{t('nav_billing')}</div>
          <div style={{ fontSize: 12, color: fg2, marginTop: 2 }}>{INVOICES.length} invoices this month</div>
        </div>
        <button style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 8, border: 'none', background: '#2563EB', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: cfg.font }}>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          New Invoice
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14, marginBottom: 24 }}>
        {[
          { label: 'Total Revenue', value: `${(total/1000).toFixed(0)}K IQD`, color: '#3B82F6' },
          { label: 'Collected', value: `${(paid/1000).toFixed(0)}K IQD`, color: '#10B981' },
          { label: 'Outstanding', value: `${(unpaid/1000).toFixed(0)}K IQD`, color: '#F59E0B' },
        ].map(s => (
          <div key={s.label} style={{ background: surface, borderRadius: 12, padding: '18px 20px', boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)', border: dark ? `1px solid ${border}` : 'none' }}>
            <div style={{ fontSize: 11, color: fg2, fontWeight: 500, marginBottom: 6 }}>{s.label}</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div style={{ background: surface, borderRadius: 12, overflow: 'hidden', boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)', border: dark ? `1px solid ${border}` : 'none' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: dark ? '#1A2744' : '#F8FAFC', borderBottom: `1.5px solid ${border}` }}>
              {['Invoice', 'Patient', 'Tests', 'Amount', 'Status', 'Date', ''].map((h,i) => (
                <th key={i} style={{ padding: '10px 16px', textAlign: isRtl ? 'right' : 'left', fontSize: 11, fontWeight: 600, color: fg2, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {INVOICES.map((inv, i) => {
              const bs = BILL_STATUS[inv.statusKey];
              return (
                <tr key={inv.id} style={{ background: i % 2 === 0 ? surface : rowAlt }}>
                  <td style={{ padding: '13px 16px', color: '#2563EB', fontWeight: 600, fontSize: 12, borderBottom: `1px solid ${border}`, textAlign: isRtl ? 'right' : 'left' }}>{inv.id}</td>
                  <td style={{ padding: '13px 16px', fontSize: 13, color: fg1, borderBottom: `1px solid ${border}`, textAlign: isRtl ? 'right' : 'left' }}>{inv.patient}</td>
                  <td style={{ padding: '13px 16px', fontSize: 12, color: fg2, borderBottom: `1px solid ${border}`, textAlign: isRtl ? 'right' : 'left' }}>{inv.tests.join(', ')}</td>
                  <td style={{ padding: '13px 16px', fontSize: 13, fontWeight: 700, color: fg1, borderBottom: `1px solid ${border}`, textAlign: isRtl ? 'right' : 'left' }}>{inv.amount.toLocaleString()} {inv.currency}</td>
                  <td style={{ padding: '13px 16px', borderBottom: `1px solid ${border}`, textAlign: isRtl ? 'right' : 'left' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: bs.bg, color: bs.color }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: bs.dot }}></span>
                      {bs.label}
                    </span>
                  </td>
                  <td style={{ padding: '13px 16px', fontSize: 12, color: fg2, borderBottom: `1px solid ${border}`, textAlign: isRtl ? 'right' : 'left' }}>{inv.date}</td>
                  <td style={{ padding: '13px 16px', borderBottom: `1px solid ${border}` }}>
                    <button style={{ background: 'none', border: 'none', fontSize: 12, fontWeight: 500, color: '#2563EB', cursor: 'pointer', fontFamily: cfg.font }}>{t('act_view')}</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

Object.assign(window, { BillingView });
