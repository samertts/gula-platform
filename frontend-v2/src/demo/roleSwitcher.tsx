import { useState } from 'react';
import { useDemoAuth, type DemoRole } from './demoAuth';

const roleCategories: { label: string; roles: DemoRole[] }[] = [
  {
    label: 'Administration',
    roles: ['super_admin', 'ministry_admin', 'directorate_manager'],
  },
  {
    label: 'Healthcare',
    roles: ['hospital_director', 'doctor', 'pharmacist', 'nurse', 'reception'],
  },
  {
    label: 'Laboratory',
    roles: ['lab_manager', 'lab_technician'],
  },
  {
    label: 'Other',
    roles: ['auditor', 'citizen', 'developer'],
  },
];

const roleLabels: Record<DemoRole, { en: string; ar: string }> = {
  super_admin: { en: 'Super Admin', ar: 'مدير عام' },
  ministry_admin: { en: 'Ministry Admin', ar: 'مدير وزارة' },
  directorate_manager: { en: 'Directorate Manager', ar: 'مدير مديرية' },
  hospital_director: { en: 'Hospital Director', ar: 'مدير مستشفى' },
  lab_manager: { en: 'Lab Manager', ar: 'مدير مختبر' },
  lab_technician: { en: 'Lab Technician', ar: 'فني مختبر' },
  doctor: { en: 'Doctor', ar: 'طبيب' },
  pharmacist: { en: 'Pharmacist', ar: 'صيدلي' },
  nurse: { en: 'Nurse', ar: 'ممرض' },
  reception: { en: 'Receptionist', ar: 'استقبال' },
  auditor: { en: 'Auditor', ar: 'مدقق' },
  citizen: { en: 'Citizen', ar: 'مواطن' },
  developer: { en: 'Developer', ar: 'مطور' },
};

export function RoleSwitcher() {
  const { user, switchRole, isDemoMode } = useDemoAuth();
  const [open, setOpen] = useState(false);

  if (!isDemoMode || !user) return null;

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 12px',
          background: '#fef3c7',
          border: '1px solid #f59e0b',
          borderRadius: 8,
          cursor: 'pointer',
          fontSize: 13,
          color: '#92400e',
          fontWeight: 500,
        }}
      >
        <span>🎭</span>
        <span>{roleLabels[user.role]?.en || user.role}</span>
        <span style={{ fontSize: 10 }}>▼</span>
      </button>

      {open && (
        <>
          <div
            onClick={() => setOpen(false)}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 999,
            }}
          />
          <div
            style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: 4,
              background: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: 12,
              boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
              zIndex: 1000,
              minWidth: 280,
              padding: 8,
            }}
          >
            <div style={{ padding: '8px 12px', fontSize: 11, color: '#6b7280', fontWeight: 600 }}>
              SWITCH DEMO ROLE
            </div>
            {roleCategories.map(cat => (
              <div key={cat.label}>
                <div style={{ padding: '4px 12px', fontSize: 10, color: '#9ca3af', fontWeight: 500 }}>
                  {cat.label}
                </div>
                {cat.roles.map(role => (
                  <button
                    key={role}
                    onClick={() => {
                      switchRole(role);
                      setOpen(false);
                    }}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      padding: '8px 12px',
                      border: 'none',
                      background: user.role === role ? '#eef2ff' : 'transparent',
                      borderRadius: 8,
                      cursor: 'pointer',
                      fontSize: 13,
                      color: user.role === role ? '#4338ca' : '#374151',
                      fontWeight: user.role === role ? 600 : 400,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>{roleLabels[role]?.en}</span>
                      <span style={{ direction: 'rtl' }}>{roleLabels[role]?.ar}</span>
                    </div>
                  </button>
                ))}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
