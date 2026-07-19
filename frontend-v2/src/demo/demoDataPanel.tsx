import { useState, useEffect } from 'react';
import { SyntheticDataStore } from '../mock/dataStore';
import { DemoDataGenerator } from '../mock/demoData';

export function DemoDataPanel() {
  const [stats, setStats] = useState<Record<string, number>>({});
  const [visible, setVisible] = useState(false);
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

  useEffect(() => {
    if (isDemoMode) {
      try {
        const store = SyntheticDataStore.getInstance();
        setStats(store.getStats());
      } catch {
        // Not initialized yet
      }
    }
  }, [isDemoMode]);

  if (!isDemoMode) return null;

  const handleReset = async () => {
    const { MockService } = await import('../mock/mockService');
    const service = MockService.getInstance();
    await service.reset();
    setStats(service.getStore().getStats());
  };

  const handleRegenerate = async () => {
    const { MockService } = await import('../mock/mockService');
    const service = MockService.getInstance();
    service.getStore().reset();

    const generator = new DemoDataGenerator();
    const store = service.getStore();
    (store as any).data = {
      patients: generator.generatePatients(1000),
      labs: generator.generateLabs(100),
      hospitals: generator.generateHospitals(20),
      doctors: generator.generateDoctors(100),
      labResults: generator.generateLabResults(5000),
      documents: generator.generateDocuments(2000),
      orders: generator.generateOrders(3000),
      samples: generator.generateSamples(3000),
      notifications: [],
      users: generator.generateUsers(50),
      appointments: generator.generateAppointments(2000),
      auditLogs: [],
    };
    setStats(service.getStore().getStats());
  };

  return (
    <div style={{ position: 'fixed', bottom: 16, right: 16, zIndex: 9998 }}>
      {visible && (
        <div
          style={{
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: 12,
            padding: 16,
            marginBottom: 8,
            boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
            minWidth: 240,
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 600, color: '#6b7280', marginBottom: 8 }}>
            DEMO DATA STORE
          </div>
          <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
            <tbody>
              {Object.entries(stats).map(([key, val]) => (
                <tr key={key}>
                  <td style={{ padding: '2px 4px', color: '#374151' }}>{key}</td>
                  <td style={{ padding: '2px 4px', textAlign: 'right', fontWeight: 600 }}>{val.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
            <button
              onClick={handleReset}
              style={{
                flex: 1,
                padding: '4px 8px',
                fontSize: 11,
                background: '#fee2e2',
                border: '1px solid #fecaca',
                borderRadius: 6,
                cursor: 'pointer',
                color: '#991b1b',
              }}
            >
              Reset
            </button>
            <button
              onClick={handleRegenerate}
              style={{
                flex: 1,
                padding: '4px 8px',
                fontSize: 11,
                background: '#dbeafe',
                border: '1px solid #bfdbfe',
                borderRadius: 6,
                cursor: 'pointer',
                color: '#1e40af',
              }}
            >
              Regenerate
            </button>
          </div>
        </div>
      )}
      <button
        onClick={() => setVisible(!visible)}
        style={{
          width: 44,
          height: 44,
          borderRadius: '50%',
          background: '#6366f1',
          color: '#fff',
          border: 'none',
          cursor: 'pointer',
          fontSize: 18,
          boxShadow: '0 4px 12px rgba(99,102,241,0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        📊
      </button>
    </div>
  );
}
