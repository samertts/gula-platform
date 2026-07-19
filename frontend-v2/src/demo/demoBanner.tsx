export function DemoBanner() {
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

  if (!isDemoMode) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        background: 'linear-gradient(90deg, #f59e0b, #d97706)',
        color: '#000',
        textAlign: 'center',
        padding: '4px 16px',
        fontSize: '12px',
        fontWeight: 600,
        letterSpacing: '0.5px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
      }}
    >
      <span>🔷</span>
      <span>DEMO ENVIRONMENT — No real patient data — Synthetic data only</span>
      <span style={{ marginLeft: 8, opacity: 0.7, fontWeight: 400 }}>
        بيئة تجريبية — لا توجد بيانات حقيقية
      </span>
    </div>
  );
}
