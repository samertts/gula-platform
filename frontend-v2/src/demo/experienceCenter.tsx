import { useState } from 'react';

interface AppEntry {
  id: string;
  name: string;
  nameAr: string;
  description: string;
  icon: string;
  path: string;
  category: 'core' | 'health' | 'lab' | 'admin' | 'ai' | 'gov';
  status: 'active' | 'beta' | 'coming_soon';
}

const applications: AppEntry[] = [
  { id: 'core', name: 'GULA Core', nameAr: 'النواة', description: 'Platform foundation and identity management', icon: '⚙️', path: '/', category: 'core', status: 'active' },
  { id: 'health', name: 'GULA Health', nameAr: 'الصحة', description: 'Patient health records and clinical data', icon: '🏥', path: '/patients', category: 'health', status: 'active' },
  { id: 'lab', name: 'GULA Laboratory', nameAr: 'المختبر', description: 'Laboratory information management system', icon: '🔬', path: '/lab/dashboard', category: 'lab', status: 'active' },
  { id: 'docintel', name: 'Document Intelligence', nameAr: 'ذكاء المستندات', description: 'OCR, classification, entity extraction', icon: '📄', path: '/documents', category: 'ai', status: 'active' },
  { id: 'ai', name: 'GULA AI', nameAr: 'الذكاء الاصطناعي', description: 'AI assistant, clinical decision support', icon: '🤖', path: '/intelligence', category: 'ai', status: 'active' },
  { id: 'knowledge', name: 'Knowledge Graph', nameAr: 'الرسم المعرفي', description: 'Healthcare knowledge exploration', icon: '🕸️', path: '/knowledge', category: 'ai', status: 'beta' },
  { id: 'analytics', name: 'GULA Analytics', nameAr: 'التحليلات', description: 'Dashboards, KPIs, and operational metrics', icon: '📊', path: '/analytics', category: 'admin', status: 'active' },
  { id: 'ministry', name: 'Ministry Dashboard', nameAr: 'لوحة الوزارة', description: 'National health oversight and governance', icon: '🏛️', path: '/ministry/dashboard', category: 'gov', status: 'active' },
  { id: 'admin', name: 'Administration', nameAr: 'الإدارة', description: 'System administration and configuration', icon: '🔧', path: '/admin/infrastructure', category: 'admin', status: 'active' },
  { id: 'developer', name: 'Developer Portal', nameAr: 'بوابة المطورين', description: 'API explorer, SDK, and documentation', icon: '💻', path: '/developer', category: 'admin', status: 'beta' },
];

export function ExperienceCenter() {
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

  if (!isDemoMode) return null;

  const filtered = filter === 'all' ? applications : applications.filter(a => a.category === filter);

  const categories = [
    { id: 'all', label: 'All', labelAr: 'الكل' },
    { id: 'core', label: 'Core', labelAr: 'الأساسية' },
    { id: 'health', label: 'Health', labelAr: 'الصحة' },
    { id: 'lab', label: 'Laboratory', labelAr: 'المختبر' },
    { id: 'ai', label: 'AI & Intelligence', labelAr: 'الذكاء الاصطناعي' },
    { id: 'admin', label: 'Administration', labelAr: 'الإدارة' },
    { id: 'gov', label: 'Government', labelAr: 'الحكومة' },
  ];

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 16px',
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          color: '#fff',
          border: 'none',
          borderRadius: 8,
          cursor: 'pointer',
          fontSize: 13,
          fontWeight: 600,
        }}
      >
        <span>🚀</span>
        <span>Experience Center</span>
      </button>

      {open && (
        <>
          <div onClick={() => setOpen(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999 }} />
          <div
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: '#fff',
              borderRadius: 20,
              padding: 24,
              zIndex: 10000,
              width: '90%',
              maxWidth: 720,
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 25px 80px rgba(0,0,0,0.3)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>GULA Experience Center</h2>
                <p style={{ margin: '4px 0 0', fontSize: 13, color: '#6b7280' }}>مركز تجربة جولة</p>
              </div>
              <button
                onClick={() => setOpen(false)}
                style={{
                  width: 32, height: 32, borderRadius: '50%', border: 'none',
                  background: '#f3f4f6', cursor: 'pointer', fontSize: 16, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
              {categories.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setFilter(cat.id)}
                  style={{
                    padding: '4px 12px',
                    borderRadius: 20,
                    border: filter === cat.id ? '2px solid #6366f1' : '1px solid #e5e7eb',
                    background: filter === cat.id ? '#eef2ff' : '#fff',
                    cursor: 'pointer',
                    fontSize: 12,
                    fontWeight: filter === cat.id ? 600 : 400,
                    color: filter === cat.id ? '#4338ca' : '#6b7280',
                  }}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8 }}>
              {filtered.map(app => (
                <a
                  key={app.id}
                  href={app.status === 'coming_soon' ? undefined : app.path}
                  onClick={(e) => {
                    if (app.status === 'coming_soon') e.preventDefault();
                    else setOpen(false);
                  }}
                  style={{
                    display: 'block',
                    padding: 16,
                    borderRadius: 12,
                    border: '1px solid #e5e7eb',
                    textDecoration: 'none',
                    color: 'inherit',
                    opacity: app.status === 'coming_soon' ? 0.5 : 1,
                    transition: 'all 0.2s',
                    cursor: app.status === 'coming_soon' ? 'not-allowed' : 'pointer',
                  }}
                  onMouseEnter={e => {
                    if (app.status !== 'coming_soon') {
                      (e.currentTarget as HTMLElement).style.borderColor = '#6366f1';
                      (e.currentTarget as HTMLElement).style.boxShadow = '0 4px 12px rgba(99,102,241,0.15)';
                    }
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = '#e5e7eb';
                    (e.currentTarget as HTMLElement).style.boxShadow = 'none';
                  }}
                >
                  <div style={{ fontSize: 28, marginBottom: 8 }}>{app.icon}</div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{app.name}</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{app.description}</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                    <span style={{ fontSize: 11, color: '#9ca3af' }}>{app.nameAr}</span>
                    {app.status === 'coming_soon' && (
                      <span style={{ fontSize: 10, padding: '1px 6px', background: '#fef3c7', borderRadius: 10, color: '#92400e' }}>
                        Coming Soon
                      </span>
                    )}
                    {app.status === 'beta' && (
                      <span style={{ fontSize: 10, padding: '1px 6px', background: '#dbeafe', borderRadius: 10, color: '#1e40af' }}>
                        Beta
                      </span>
                    )}
                  </div>
                </a>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  );
}
