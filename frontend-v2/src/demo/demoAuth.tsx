import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

export type DemoRole =
  | 'super_admin'
  | 'ministry_admin'
  | 'directorate_manager'
  | 'hospital_director'
  | 'lab_manager'
  | 'lab_technician'
  | 'doctor'
  | 'pharmacist'
  | 'nurse'
  | 'reception'
  | 'auditor'
  | 'citizen'
  | 'developer';

export interface DemoUser {
  id: string;
  email: string;
  name: string;
  nameAr: string;
  role: DemoRole;
  labId?: string;
  hospitalId?: string;
  avatar?: string;
}

interface DemoAuthState {
  user: DemoUser | null;
  isAuthenticated: boolean;
  isDemoMode: boolean;
  login: (role: DemoRole) => void;
  logout: () => void;
  switchRole: (role: DemoRole) => void;
  availableRoles: DemoRole[];
}

const roleConfig: Record<DemoRole, { name: string; nameAr: string }> = {
  super_admin: { name: 'Super Administrator', nameAr: 'مدير عام' },
  ministry_admin: { name: 'Ministry Administrator', nameAr: 'مدير وزارة' },
  directorate_manager: { name: 'Directorate Manager', nameAr: 'مدير مديرية' },
  hospital_director: { name: 'Hospital Director', nameAr: 'مدير مستشفى' },
  lab_manager: { name: 'Laboratory Manager', nameAr: 'مدير مختبر' },
  lab_technician: { name: 'Lab Technician', nameAr: 'فني مختبر' },
  doctor: { name: 'Doctor', nameAr: 'طبيب' },
  pharmacist: { name: 'Pharmacist', nameAr: 'صيدلي' },
  nurse: { name: 'Nurse', nameAr: 'ممرض' },
  reception: { name: 'Receptionist', nameAr: 'موظف استقبال' },
  auditor: { name: 'Auditor', nameAr: 'مدقق' },
  citizen: { name: 'Citizen', nameAr: 'مواطن' },
  developer: { name: 'Developer', nameAr: 'مطور' },
};

const roleEmails: Record<DemoRole, string> = {
  super_admin: 'admin@demo.gula-platform.org',
  ministry_admin: 'ministry@demo.gula-platform.org',
  directorate_manager: 'directorate@demo.gula-platform.org',
  hospital_director: 'hospital@demo.gula-platform.org',
  lab_manager: 'lab.manager@demo.gula-platform.org',
  lab_technician: 'lab.tech@demo.gula-platform.org',
  doctor: 'doctor@demo.gula-platform.org',
  pharmacist: 'pharmacist@demo.gula-platform.org',
  nurse: 'nurse@demo.gula-platform.org',
  reception: 'reception@demo.gula-platform.org',
  auditor: 'auditor@demo.gula-platform.org',
  citizen: 'citizen@demo.gula-platform.org',
  developer: 'developer@demo.gula-platform.org',
};

const DemoAuthContext = createContext<DemoAuthState | null>(null);

export function DemoAuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<DemoUser | null>(null);
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

  useEffect(() => {
    const stored = localStorage.getItem('gula_demo_user');
    if (stored && isDemoMode) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem('gula_demo_user');
      }
    }
  }, [isDemoMode]);

  const createDemoUser = useCallback((role: DemoRole): DemoUser => {
    const config = roleConfig[role];
    return {
      id: `demo-${role}`,
      email: roleEmails[role],
      name: config.name,
      nameAr: config.nameAr,
      role,
      labId: role === 'lab_manager' || role === 'lab_technician' ? 'demo-lab-1' : undefined,
      hospitalId: role === 'hospital_director' ? 'demo-hospital-1' : undefined,
    };
  }, []);

  const login = useCallback((role: DemoRole) => {
    const demoUser = createDemoUser(role);
    setUser(demoUser);
    localStorage.setItem('gula_demo_user', JSON.stringify(demoUser));
  }, [createDemoUser]);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('gula_demo_user');
  }, []);

  const switchRole = useCallback((role: DemoRole) => {
    login(role);
  }, [login]);

  const availableRoles: DemoRole[] = Object.keys(roleConfig) as DemoRole[];

  return (
    <DemoAuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isDemoMode,
        login,
        logout,
        switchRole,
        availableRoles,
      }}
    >
      {children}
    </DemoAuthContext.Provider>
  );
}

export function useDemoAuth(): DemoAuthState {
  const context = useContext(DemoAuthContext);
  if (!context) {
    throw new Error('useDemoAuth must be used within DemoAuthProvider');
  }
  return context;
}
